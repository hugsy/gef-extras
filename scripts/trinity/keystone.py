__AUTHOR__   = "hugsy"
__VERSION__  = 0.1
__NAME__     = "assemble"


import keystone
import gdb


@register
class AssembleCommand(GenericCommand):
    """Inline code assemble. Architecture can be set in GEF runtime config. """

    _cmdline_ = "assemble"
    _syntax_  = f"{_cmdline_} [-h] [--list-archs] [--mode MODE] [--arch ARCH] [--overwrite-location LOCATION] [--endian ENDIAN] [--as-shellcode] instruction;[instruction;...instruction;])"
    _aliases_ = ["asm",]
    _example_ = (f"\n{_cmdline_} -a x86 -m 32 nop ; nop ; inc eax ; int3"
                 f"\n{_cmdline_} -a arm -m arm add r0, r0, 1")

    valid_arch_modes = {
            # Format: ARCH = [MODES] with MODE = (NAME, HAS_LITTLE_ENDIAN, HAS_BIG_ENDIAN)
            "ARM":     [("ARM",     True,  True),  ("THUMB",   True,  True),
                        ("ARMV8",   True,  True),  ("THUMBV8", True,  True)],
            "ARM64":   [("0", True,  False)],
            "MIPS":    [("MIPS32",  True,  True),  ("MIPS64",  True,  True)],
            "PPC":     [("PPC32",   False, True),  ("PPC64",   True,  True)],
            "SPARC":   [("SPARC32", True,  True),  ("SPARC64", False, True)],
            "SYSTEMZ": [("SYSTEMZ", True,  True)],
            "X86":     [("16",      True,  False), ("32",      True,  False),
                        ("64",      True,  False)]
        }
    valid_archs = valid_arch_modes.keys()
    valid_modes = [_ for sublist in valid_arch_modes.values() for _ in sublist]

    def __init__(self) -> None:
        super().__init__()
        self["default_architecture"] = ("X86", "Specify the default architecture to use when assembling")
        self["default_mode"] = ("64", "Specify the default architecture to use when assembling")
        return

    def pre_load(self) -> None:
        try:
            __import__("keystone")
        except ImportError:
            msg = "Missing `keystone-engine` package for Python, install with: `pip install keystone-engine`."
            raise ImportWarning(msg)
        return

    def usage(self) -> None:
        super().usage()
        gef_print("")
        self.list_archs()
        return

    def list_archs(self) -> None:
        gef_print("Available architectures/modes (with endianness):")
        # for updates, see https://github.com/keystone-engine/keystone/blob/master/include/keystone/keystone.h
        for arch in self.valid_arch_modes:
            gef_print(f"- {arch}")
            for mode, le, be in self.valid_arch_modes[arch]:
                if le and be:
                    endianness = "little, big"
                elif le:
                    endianness = "little"
                elif be:
                    endianness = "big"
                gef_print(f"  * {mode:<7} ({endianness})")
        return

    @parse_arguments({"instructions": [""]}, {"--mode": "", "--arch": "", "--overwrite-location": 0, "--endian": "little", "--list-archs": True, "--as-shellcode": True})
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        arch_s, mode_s, endian_s = self["default_architecture"], self["default_mode"], ""

        args = kwargs["arguments"]
        if args.list_archs:
            self.list_archs()
            return

        if not args.instructions:
            err("No instruction given.")
            return

        if is_alive():
            arch_s, mode_s = gef.arch.arch, gef.arch.mode
            endian_s = "big" if gef.arch.endianness == Endianness.BIG_ENDIAN else ""

        if args.arch:
            arch_s = args.arch
        arch_s = arch_s.upper()

        if args.mode:
            mode_s = args.mode
        mode_s = mode_s.upper()

        if args.endian == "big":
            endian_s = "big"
        endian_s = endian_s.upper()

        if arch_s not in self.valid_arch_modes:
            raise AttributeError(f"invalid arch '{arch_s}'")

        valid_modes = self.valid_arch_modes[arch_s]
        try:
            mode_idx = [m[0] for m in valid_modes].index(mode_s)
        except ValueError:
            raise AttributeError(f"invalid mode '{mode_s}' for arch '{arch_s}'")

        if endian_s == "little" and not valid_modes[mode_idx][1] or endian_s == "big" and not valid_modes[mode_idx][2]:
            raise AttributeError(f"invalid endianness '{endian_s}' for arch/mode '{arch_s}:{mode_s}'")

        arch, mode = get_keystone_arch(arch=arch_s, mode=mode_s, endian=endian_s)
        insns = [x.strip() for x in " ".join(args.instructions).split(";") if x]
        info(f"Assembling {len(insns)} instruction(s) for {arch_s}:{mode_s}")

        if args.as_shellcode:
            gef_print("""sc="" """)

        raw = b""
        for insn in insns:
            res = keystone_assemble(insn, arch, mode, raw=True)
            if res is None:
                gef_print("(Invalid)")
                continue

            if args.overwrite_location:
                raw += res
                continue

            s = binascii.hexlify(res)
            res = b"\\x" + b"\\x".join([s[i:i + 2] for i in range(0, len(s), 2)])
            res = res.decode("utf-8")

            if args.as_shellcode:
                res = f"""sc+="{res}" """

            gef_print(f"{res!s:60s} # {insn}")

        if args.overwrite_location:
            l = len(raw)
            info(f"Overwriting {l:d} bytes at {format_address(args.overwrite_location)}")
            gef.memory.write(args.overwrite_location, raw, l)
        return


def get_arch(arch: Optional[str] = None, mode: Optional[str] = None, endian: Optional[bool] = None, to_string: bool = False) -> Union[Tuple[None, None], Tuple[str, Union[int, str]]]:
    keystone = sys.modules["keystone"]
    if (arch, mode, endian) == (None, None, None):
        return get_generic_running_arch(keystone, "KS", to_string)

    if arch in ["ARM64", "SYSTEMZ"]:
        modes = [None]
    elif arch == "ARM" and mode == "ARMV8":
        modes = ["ARM", "V8"]
    elif arch == "ARM" and mode == "THUMBV8":
        modes = ["THUMB", "V8"]
    else:
        modes = [mode]
    a = arch
    if not to_string:
        mode = 0
        for m in modes:
            arch, _mode = get_generic_arch(keystone, "KS", a, m, endian, to_string)
            mode |= _mode
    else:
        mode = ""
        for m in modes:
            arch, _mode = get_generic_arch(keystone, "KS", a, m, endian, to_string)
            mode += f"|{_mode}"
        mode = mode[1:]
    return arch, mode



def assemble(code_str: str, arch: int, mode: int, **kwargs: Any) -> Optional[Union[str, bytearray]]:
    """Assembly encoding function based on keystone."""
    keystone = sys.modules["keystone"]
    code = gef_pybytes(code_str)
    addr = kwargs.get("addr", 0x1000)

    try:
        ks = keystone.Ks(arch, mode)
        enc, cnt = ks.asm(code, addr)
    except keystone.KsError as e:
        err(f"Keystone assembler error: {e}")
        return None

    if cnt == 0:
        return ""

    enc = bytearray(enc)
    if "raw" not in kwargs:
        s = binascii.hexlify(enc)
        enc = b"\\x" + b"\\x".join([s[i : i + 2] for i in range(0, len(s), 2)])
        enc = enc.decode("utf-8")

    return enc


