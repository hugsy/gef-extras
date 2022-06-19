
__AUTHOR__ = "hugsy"
__VERSION__ = 0.2
__LICENSE__ = "MIT"

import binascii
from typing import TYPE_CHECKING, Any, List, Optional

import keystone

if TYPE_CHECKING:
    from . import *
    from . import gdb

PLUGIN_ASSEMBLE_DEFAULT_ADDRESS = 0x4000

VALID_ARCH_MODES = {
    # Format:
    # ARCH = [MODES]
    #   with MODE = (NAME, HAS_LITTLE_ENDIAN, HAS_BIG_ENDIAN)
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
VALID_ARCHS = VALID_ARCH_MODES.keys()
VALID_MODES = [_ for sublist in VALID_ARCH_MODES.values() for _ in sublist]

__ks: Optional[keystone.Ks] = None


@register
class AssembleCommand(GenericCommand):
    """Inline code assemble. Architecture can be set in GEF runtime config. """

    _cmdline_ = "assemble"
    _syntax_ = f"{_cmdline_} [-h] [--list-archs] [--mode MODE] [--arch ARCH] [--overwrite-location LOCATION] [--endian ENDIAN] [--as-shellcode] instruction;[instruction;...instruction;])"
    _aliases_ = ["asm", ]
    _example_ = (f"{_cmdline_} --arch x86 --mode 32 nop ; nop ; inc eax ; int3",
                 f"{_cmdline_} --arch arm --mode arm add r0, r0, 1")

    def __init__(self) -> None:
        super().__init__()
        self["default_architecture"] = (
            "X86", "Specify the default architecture to use when assembling")
        self["default_mode"] = (
            "64", "Specify the default architecture to use when assembling")
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
        for arch in VALID_ARCH_MODES:
            endianness = ""
            gef_print(f"- {arch}")
            for mode, le, be in VALID_ARCH_MODES[arch]:
                if le and be:
                    endianness = "little, big"
                elif le:
                    endianness = "little"
                elif be:
                    endianness = "big"
                gef_print(f"  * {mode:<7} ({endianness})")
        return

    @parse_arguments({"instructions": [""]}, {"--mode": "", "--arch": "", "--overwrite-location": "", "--endian": "little", "--list-archs": True, "--as-shellcode": True})
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

        if not args.arch:
            err("An architecture must be provided")
            return

        if not args.mode:
            err("A mode must be provided")
            return

        arch_s = args.arch.upper()
        mode_s = args.mode.upper()
        endian_s = args.endian.upper()

        if arch_s not in VALID_ARCH_MODES:
            raise AttributeError(f"invalid arch '{arch_s}'")

        valid_modes = VALID_ARCH_MODES[arch_s]
        try:
            mode_idx = [m[0] for m in valid_modes].index(mode_s)
        except ValueError:
            raise AttributeError(
                f"invalid mode '{mode_s}' for arch '{arch_s}'")

        if endian_s == "little" and not valid_modes[mode_idx][1] or endian_s == "big" and not valid_modes[mode_idx][2]:
            raise AttributeError(
                f"invalid endianness '{endian_s}' for arch/mode '{arch_s}:{mode_s}'")

        ks_arch: int = getattr(keystone, f"KS_ARCH_{arch_s}")
        ks_mode: int = getattr(keystone, f"KS_MODE_{mode_s}")
        ks_endian: int = getattr(
            keystone, f"KS_MODE_{endian_s}_ENDIAN")
        insns = [x.strip()
                 for x in " ".join(args.instructions).split(";") if x]
        info(f"Assembling {len(insns)} instruction(s) for {arch_s}:{mode_s}")

        if args.as_shellcode:
            gef_print("""sc="" """)

        raw = b""
        for insn in insns:
            res = ks_assemble(insn, ks_arch, ks_mode | ks_endian)
            if res is None:
                err("(Invalid)")
                return

            if args.overwrite_location:
                raw += res

            s = binascii.hexlify(res)
            res = b"\\x" + b"\\x".join([s[i:i + 2]
                                       for i in range(0, len(s), 2)])
            res = res.decode("utf-8")

            if args.as_shellcode:
                res = f"""sc+="{res}" """

            gef_print(f"{res!s:60s} # {insn}")

        if args.overwrite_location:
            if not is_alive():
                warn(
                    "The debugging session is not active, cannot overwrite location. Skipping...")
                return

            address = parse_address(args.overwrite_location)
            info(
                f"Overwriting {len(raw):d} bytes at {format_address(address)}")
            gef.memory.write(address, raw, len(raw))
        return


def ks_assemble(code: str, arch: int, mode: int, address: int = PLUGIN_ASSEMBLE_DEFAULT_ADDRESS) -> Optional[bytes]:
    """Assembly encoding function based on keystone."""
    global __ks

    if not __ks:
        __ks = keystone.Ks(arch, mode)

    try:
        enc, cnt = __ks.asm(code, address)
    except keystone.KsError as e:
        err(f"Keystone assembler error: {e}")
        return None

    if cnt == 0 or not enc:
        return None

    return bytes(enc)
