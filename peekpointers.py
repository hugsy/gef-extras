class PeekPointers(GenericCommand):
    """
    Command to help find pointers belonging to other memory regions
    helpful in case of OOB Read when looking for specific pointers

    Example:
    \tgef➤  peek-pointers 0x55555575c000
    \tcat pointer at 0x55555575c008, value 0x55555575c008
    \t[stack] pointer at 0x55555575c0c0, value 0x7fffffffe497
    \tlibc-2.24.so pointer at 0x55555575c0c8, value 0x7ffff7dd2600 <_IO_2_1_stdout_>
    \t[heap] pointer at 0x55555575d038, value 0x55555575d010
    \tlocale-archive pointer at 0x55555575d0b8, value 0x7ffff774e5c0
    \tCould not read from address 0x55555577e000, stopping.
    \tgef➤  peek-pointers 0x55555575c000 libc-2.24.so
    \tlibc-2.24.so pointer at 0x55555575c0c8, value 0x7ffff7dd2600 <_IO_2_1_stdout_>
    \tgef➤  peek-pointers 0x55555575c000 libc-2.24.so all
    \tlibc-2.24.so pointer at 0x55555575c0c8, value 0x7ffff7dd2600 <_IO_2_1_stdout_>
    \tlibc-2.24.so pointer at 0x55555575c0e0, value 0x7ffff7dd2520 <_IO_2_1_stderr_>
    \tlibc-2.24.so pointer at 0x55555575dfe8, value 0x7ffff7ba1b40 <_nl_default_dirname>
    \tCould not read from address 0x55555577e000, stopping.
    """
    _cmdline_ = "peek-pointers"
    _syntax_  = "{:s} starting_address <object_name> <all>".format(_cmdline_)

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

        if argc >= 2 :
            section_name = argv[1].lower()
            if   section_name == "stack":
                sections = [(s.path, s.page_start, s.page_end) for s in vmmap if s.path == "[stack]"]
            elif section_name == "heap":
                sections = [(s.path, s.page_start, s.page_end) for s in vmmap if s.path == "[heap]"]
            elif section_name != "all":
                sections = [ (s.path, s.page_start, s.page_end) for s in vmmap if section_name in s.path ]
            else:
                sections = [ (s.path, s.page_start, s.page_end) for s in vmmap ]
        else:
            sections = [ (s.path, s.page_start, s.page_end) for s in vmmap ]

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
                        elif len(name)==0:
                            name = get_filename()

                        ok(" Found pointer at 0x{:x} to 0x{:x} {:s} ('{:s}', perm: {:s})".format(addr.value, addr_value, sym, name, str(addr.section.permission), ))

                        if unique:
                            del sections[i]
                        break

            addr = lookup_address(addr.value + current_arch.ptrsize)
        return


if __name__ == "__main__":
    register_external_command(PeekPointers())
