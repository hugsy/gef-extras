
__AUTHOR__ = "bkth"
__VERSION__ = 0.2
__LICENSE__ = "MIT"

import pathlib
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from . import *


@register
class PeekPointers(GenericCommand):
    """Command to help find pointers belonging to other memory regions helpful in case
    of OOB Read when looking for specific pointers"""

    _cmdline_ = "peek-pointers"
    _syntax_ = f"{_cmdline_} starting_address <object_name> <all>"

    @only_if_gdb_running
    def do_invoke(self, argv: List[str]):
        argc = len(argv)
        if argc not in (1, 2, 3):
            self.usage()
            return

        addr = lookup_address(int(argv[0], 16))
        if (addr.value % DEFAULT_PAGE_SIZE):
            err("<starting_address> must be aligned to a page")
            return

        unique = True if "all" not in argv else False
        vmmap = gef.memory.maps

        if argc >= 2:
            section_name = argv[1].lower()
            if section_name == "stack":
                sections = [(s.path, s.page_start, s.page_end)
                            for s in vmmap if s.path == "[stack]"]
            elif section_name == "heap":
                sections = [(s.path, s.page_start, s.page_end)
                            for s in vmmap if s.path == "[heap]"]
            elif section_name != "all":
                sections = [(s.path, s.page_start, s.page_end)
                            for s in vmmap if section_name in s.path]
            else:
                sections = [(s.path, s.page_start, s.page_end) for s in vmmap]
        else:
            sections = [(s.path, s.page_start, s.page_end) for s in vmmap]

        while addr.valid:
            addr_value = gef.memory.read_integer(addr.value)

            if lookup_address(addr_value):
                for i, section in enumerate(sections):
                    name, start_addr, end_addr = section
                    if start_addr <= addr_value < end_addr:
                        sym = gdb_get_location_from_symbol(addr_value)
                        sym = "<{:s}+{:04x}>".format(*sym) if sym else ''
                        if name.startswith("/"):
                            name = pathlib.Path(name)
                        elif not name:
                            name = gef.session.file

                        msg = f" Found pointer at 0x{addr.value:x} to 0x{addr_value:x} {sym} ('{name}', perm: {str(addr.section.permission)})"
                        ok(msg)

                        if unique:
                            del sections[i]
                        break

            addr = lookup_address(addr.value + gef.arch.ptrsize)
        return
