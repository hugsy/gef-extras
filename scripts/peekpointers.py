@register_external_command
class PeekPointers(GenericCommand):
    """Command to help find pointers belonging to other memory regions helpful in case
    of OOB Read when looking for specific pointers"""

    _cmdline_ = "peek-pointers"
    _syntax_ = "{:s} starting_address <object_name> <all>".format(_cmdline_)

    @only_if_gdb_running
    def do_invoke(self, argv):
        argc = len(argv)
        if argc not in (1, 2, 3):
            self.usage()
            return

        addr = lookup_address(int(argv[0], 16))
        if (addr.value % DEFAULT_PAGE_SIZE):
            err("<starting_address> must be aligned to a page")
            return

        unique = True if "all" not in argv else False
        vmmap = get_process_maps()

        if argc >= 2:
            section_name = argv[1].lower()
            if section_name == "stack":
                sections = [(s.path, s.page_start, s.page_end) for s in vmmap if s.path == "[stack]"]
            elif section_name == "heap":
                sections = [(s.path, s.page_start, s.page_end) for s in vmmap if s.path == "[heap]"]
            elif section_name != "all":
                sections = [(s.path, s.page_start, s.page_end) for s in vmmap if section_name in s.path]
            else:
                sections = [(s.path, s.page_start, s.page_end) for s in vmmap]
        else:
            sections = [(s.path, s.page_start, s.page_end) for s in vmmap]

        while addr.valid:
            addr_value = read_int_from_memory(addr.value)

            if lookup_address(addr_value):
                for i, section in enumerate(sections):
                    name, start_addr, end_addr = section
                    if start_addr <= addr_value < end_addr:
                        sym = gdb_get_location_from_symbol(addr_value)
                        sym = "<{:s}+{:04x}>".format(*sym) if sym else ''
                        if name.startswith("/"):
                            name = os.path.basename(name)
                        elif not name:
                            name = get_filename()

                        ok(" Found pointer at 0x{:x} to 0x{:x} {:s} ('{:s}', perm: {:s})".format(addr.value, addr_value, sym, name, str(addr.section.permission), ))

                        if unique:
                            del sections[i]
                        break

            addr = lookup_address(addr.value + current_arch.ptrsize)
        return
