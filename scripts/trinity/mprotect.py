__AUTHOR__   = "hugsy"
__NAME__     = "mprotect"
__VERSION__  = 0.1


import gdb
import keystone


@register
class ChangePermissionCommand(GenericCommand):
    """Change a page permission. By default, it will change it to 7 (RWX)."""

    _cmdline_ = "set-permission"
    _syntax_  = (f"{_cmdline_} address [permission]\n"
                 "\taddress\t\tan address within the memory page for which the permissions should be changed\n"
                 "\tpermission\ta 3-bit bitmask with read=1, write=2 and execute=4 as integer")
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

        loc = int(loc)
        sect = process_lookup_address(loc)
        if sect is None:
            err("Unmapped address")
            return

        size = sect.page_end - sect.page_start
        original_pc = gef.arch.pc

        info(f"Generating sys_mprotect({sect.page_start:#x}, {size:#x}, "
             f"'{perm!s}') stub for arch {get_arch()}")
        stub = self.get_stub_by_arch(sect.page_start, size, perm)
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

    def get_stub_by_arch(self, addr: int, size: int, perm: Permission) -> Union[str, bytearray, None]:
        code = gef.arch.mprotect_asm(addr, size, perm)
        arch, mode = get_keystone_arch()
        raw_insns = keystone_assemble(code, arch, mode, raw=True)
        return raw_insns

