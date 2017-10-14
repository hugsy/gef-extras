
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

    
    def _build_ranges(self, name=""):

        maps = get_process_maps()
        ranges = {}
        for m in maps:

            if not m.path:
                continue
            if name and name != m.path and not m.path.endswith(name):
                continue
            if m.path not in ranges:
                ranges[m.path] = (1 << 128, 0)

            start_m, end_m = ranges[m.path]
            if m.page_start < start_m: 
                start_m = m.page_start 
            if m.page_end > end_m:
                end_m = m.page_end 

            ranges[m.path] = (start_m, end_m)
                       
        return ranges

    def _get_name_maps(self):
        names = []
        for m in get_process_maps():
            if m.path and m.path not in names:
                names.append(m.path) 

        print(names)
        return names

    def _resolve_symbol(self, addr):
        try:
            res = gdb.execute("x/gx 0x{:x}".format(addr), to_string=True)
        except:
            raise Exception()
            
        if "<" in res:
            sym = res.split("<")[1].split(">")[0]
            return sym
        return ""

    @only_if_gdb_running
    def do_invoke(self, argv):
        assert(len(argv) >= 1)
         
        addr = int(argv[0], 16)
        incr = 0

        unique = True
        specific_name = ""

        if "all" in argv:
            unique = False

        if len(argv) >= 2 and argv[1] == "stack":
            specific_name = "[stack]"
        elif len(argv) >= 2 and argv[1] == "heap":
            specific_name = "[heap]"
        elif len(argv) >= 2 and argv[1] != "all": 
            so_name = argv[1]
            specific_name = argv[1]
        ranges = self._build_ranges(specific_name)
        read_fn = read_int_from_memory 

        incr = get_memory_alignment() # hack around GEF not checking for cases where the inferior does not have a name

        assert(incr > 0)
        
        while ranges:
            try:
                v = read_fn(addr)
            except:
                print("Could not read from address 0x{:x}, stopping.".format(addr))
                return
            
            for k in ranges:
                if ranges[k][0] <= v < ranges[k][1]:
                    sym = None
                    # call resolve symbol in try catch block
                    # to avoid cases where it is not a valid pointer
                    try:
                        sym = self._resolve_symbol(v)
                    except:
                        break
                    short_name = k
                    if short_name[0] == "/":
                        short_name = short_name.split("/")[-1]
                    if sym:
                        print("{:s} pointer at 0x{:x}, value 0x{:x} <{:s}>".format(short_name, addr, v, sym))
                    else:
                        print("{:s} pointer at 0x{:x}, value 0x{:x}".format(short_name, addr, v))
                    if unique:
                        del ranges[k]
                    break
 
            addr += incr


if __name__ == "__main__":
    register_external_command(PeekPointers())
