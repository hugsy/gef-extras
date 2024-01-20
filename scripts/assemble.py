__AUTHOR__ = "hugsy"
__VERSION__ = 0.2
__LICENSE__ = "MIT"

import binascii
from typing import TYPE_CHECKING, Any, List, Optional, Union

import keystone

if TYPE_CHECKING:
    from . import *
    from . import gdb

PLUGIN_ASSEMBLE_DEFAULT_ADDRESS = 0x4000

VALID_ARCH_MODES = {
    # Format:
    # ARCH = [MODES]
    #   with MODE = (NAME, HAS_LITTLE_ENDIAN, HAS_BIG_ENDIAN)
    "ARM": [
        ("ARM", True, True),
        ("THUMB", True, True),
        ("ARMV8", True, True),
        ("THUMBV8", True, True),
    ],
    "ARM64": [("0", True, False)],
    "MIPS": [("MIPS32", True, True), ("MIPS64", True, True)],
    "PPC": [("PPC32", False, True), ("PPC64", True, True)],
    "SPARC": [("SPARC32", True, True), ("SPARC64", False, True)],
    "SYSTEMZ": [("SYSTEMZ", True, True)],
    "X86": [("16", True, False), ("32", True, False), ("64", True, False)],
}
VALID_ARCHS = VALID_ARCH_MODES.keys()
VALID_MODES = [_ for sublist in VALID_ARCH_MODES.values() for _ in sublist]

__ks: Optional[keystone.Ks] = None


@register
class AssembleCommand(GenericCommand):
    """Inline code assemble. Architecture can be set in GEF runtime config."""

    _cmdline_ = "assemble"
    _syntax_ = f"{_cmdline_} [-h] [--list-archs] [--mode MODE] [--arch ARCH] [--overwrite-location LOCATION] [--endian ENDIAN] [--as-shellcode] instruction;[instruction;...instruction;])"
    _aliases_ = [
        "asm",
    ]
    _example_ = (
        f"{_cmdline_} --arch x86 --mode 32 nop ; nop ; inc eax ; int3",
        f"{_cmdline_} --arch arm --mode arm add r0, r0, 1",
    )

    def __init__(self) -> None:
        super().__init__()
        self["default_architecture"] = (
            "X86",
            "Specify the default architecture to use when assembling",
        )
        self["default_mode"] = (
            "64",
            "Specify the default architecture to use when assembling",
        )
        self["default_endianess"] = (
            "little",
            "Specify the default endianess to use when assembling",
        )
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

    @parse_arguments(
        {"instructions": [""]},
        {
            "--arch": "",
            "--mode": "",
            "--endian": "",
            "--overwrite-location": "",
            "--list-archs": True,
            "--as-shellcode": True,
        },
    )
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        arch_s, mode_s, endian_s = (
            self["default_architecture"],
            self["default_mode"],
            self["default_endianess"],
        )

        args = kwargs["arguments"]
        if args.list_archs:
            self.list_archs()
            return

        if not args.instructions:
            err("No instruction given.")
            return

        if is_alive():
            arch_s, mode_s = gef.arch.arch, gef.arch.mode
            endian_s = (
                "big" if gef.arch.endianness == Endianness.BIG_ENDIAN else "little"
            )

        if args.arch:
            arch_s = args.arch

        if args.mode:
            mode_s = args.mode

        if args.endian:
            endian_s = args.endian

        arch_s = arch_s.upper()
        mode_s = mode_s.upper()
        endian_s = endian_s.upper()

        if arch_s not in VALID_ARCH_MODES:
            raise AttributeError(f"invalid arch '{arch_s}'")

        valid_modes = VALID_ARCH_MODES[arch_s]
        try:
            mode_idx = [m[0] for m in valid_modes].index(mode_s)
        except ValueError:
            raise AttributeError(f"invalid mode '{mode_s}' for arch '{arch_s}'")

        if (
            endian_s == "little"
            and not valid_modes[mode_idx][1]
            or endian_s == "big"
            and not valid_modes[mode_idx][2]
        ):
            raise AttributeError(
                f"invalid endianness '{endian_s}' for arch/mode '{arch_s}:{mode_s}'"
            )

        ks_arch: int = getattr(keystone, f"KS_ARCH_{arch_s}")
        # manual fixups
        # * aarch64
        if arch_s == "ARM64" and mode_s == "0":
            ks_mode = 0
        else:
            ks_mode: int = getattr(keystone, f"KS_MODE_{mode_s}")
        ks_endian: int = getattr(keystone, f"KS_MODE_{endian_s}_ENDIAN")
        insns = [x.strip() for x in " ".join(args.instructions).split(";") if x]
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
            res = b"\\x" + b"\\x".join([s[i : i + 2] for i in range(0, len(s), 2)])
            res = res.decode("utf-8")

            if args.as_shellcode:
                res = f"""sc+="{res}" """

            gef_print(f"{res!s:60s} # {insn}")

        if args.overwrite_location:
            if not is_alive():
                warn(
                    "The debugging session is not active, cannot overwrite location. Skipping..."
                )
                return

            address = parse_address(args.overwrite_location)
            info(f"Overwriting {len(raw):d} bytes at {format_address(address)}")
            gef.memory.write(address, raw, len(raw))
        return


def ks_assemble(
    code: str, arch: int, mode: int, address: int = PLUGIN_ASSEMBLE_DEFAULT_ADDRESS
) -> Optional[bytes]:
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


@register
class ChangePermissionCommand(GenericCommand):
    """Change a page permission. By default, it will change it to 7 (RWX)."""

    _cmdline_ = "set-permission"
    _syntax_ = (
        f"{_cmdline_} address [permission]\n"
        "\taddress\t\tan address within the memory page for which the permissions should be changed\n"
        "\tpermission\ta 3-bit bitmask with read=1, write=2 and execute=4 as integer"
    )
    _aliases_ = ["mprotect"]
    _example_ = f"{_cmdline_} $sp 7"

    def __init__(self) -> None:
        super().__init__(complete=gdb.COMPLETE_LOCATION)
        return

    @only_if_gdb_running
    def do_invoke(self, argv: List[str]) -> None:
        if len(argv) not in (1, 2):
            err("Incorrect syntax")
            self.usage()
            return

        if len(argv) == 2:
            perm = Permission(int(argv[1]))
        else:
            perm = Permission.ALL

        loc = safe_parse_and_eval(argv[0])
        if loc is None:
            err("Invalid address")
            return

        loc = int(abs(loc))
        sect = process_lookup_address(loc)
        if sect is None:
            err("Unmapped address")
            return

        size = sect.page_end - sect.page_start
        original_pc = gef.arch.pc

        info(
            f"Generating sys_mprotect({sect.page_start:#x}, {size:#x}, "
            f"'{perm!s}') stub for arch {get_arch()}"
        )
        stub = self.get_arch_and_mode(sect.page_start, size, perm)
        if stub is None:
            err("Failed to generate mprotect opcodes")
            return

        info("Saving original code")
        original_code = gef.memory.read(original_pc, len(stub))

        bp_loc = f"*{original_pc + len(stub):#x}"
        info(f"Setting a restore breakpoint at {bp_loc}")
        ChangePermissionBreakpoint(bp_loc, original_code, original_pc)

        info(f"Overwriting current memory at {loc:#x} ({len(stub)} bytes)")
        gef.memory.write(original_pc, stub, len(stub))

        info("Resuming execution")
        gdb.execute("continue")
        return

    def get_arch_and_mode(
        self, addr: int, size: int, perm: Permission
    ) -> Union[bytes, None]:
        code = gef.arch.mprotect_asm(addr, size, perm)

        # arch, mode and endianness as seen by GEF
        arch_s = gef.arch.arch.upper()
        mode_s = gef.arch.mode.upper()
        endian_s = repr(gef.arch.endianness).upper()

        if arch_s not in VALID_ARCH_MODES:
            raise AttributeError(f"invalid arch '{arch_s}'")

        # convert them to arch, mode and endianness for keystone
        ks_arch: int = getattr(keystone, f"KS_ARCH_{arch_s}")
        if arch_s == "ARM64" and mode_s == "":
            ks_mode = 0
        else:
            ks_mode: int = getattr(keystone, f"KS_MODE_{mode_s}")
        ks_endian: int = getattr(keystone, f"KS_MODE_{endian_s}")

        addr = gef.arch.pc
        return ks_assemble(code, ks_arch, ks_mode | ks_endian, addr)
