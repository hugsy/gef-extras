__AUTHOR__ = "hugsy"
__VERSION__ = 0.1

import gdb

g_heap_known_values = {

}


@lru_cache
def collect_known_values():
    # todo: add chunk addresses
    # todo: add {fast,small,tcache}bins
    return g_heap_known_values


class VisualizeHeapChunksCommand(GenericCommand):
    """Visual helper for glibc heap chunks"""

    _cmdline_ = "visualize-libc-heap-chunks"
    _syntax_  = "{:s}".format(_cmdline_)
    _aliases_ = ["heap-view",]
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        super(VisualizeHeapChunksCommand, self).__init__(complete=gdb.COMPLETE_SYMBOL)
        return

    @only_if_gdb_running
    def do_invoke(self, argv):
        heap_base_address = int(argv[0]) if len(argv) else HeapBaseFunction.heap_base()
        arena = get_main_arena()
        if not arena.top:
            err("The heap has not been initialized")
            return

        top =  align_address(arena.top)
        base = align_address(heap_base_address)

        colors = [ "cyan", "red", "yellow", "blue", "green" ]
        cur = GlibcChunk(base, from_base=True)
        idx = 0

        while True:
            addr = cur.chunk_base_address

            if addr == top:
                gef_print("{}    {}".format(format_address(addr), Color.colorify(LEFT_ARROW + "Top Chunk", "red bold")))
                break

            if addr in g_heap_known_values:
                pass

            if cur.size == 0:
                break

            for off in range(0, cur.size, cur.ptrsize):
                __addr = addr + off
                value = align_address( read_int_from_memory(__addr) )
                text = "".join([chr(b) if 0x20 <= b < 0x7F else "." for b in read_memory(__addr, cur.ptrsize)])
                line = "{}    {}".format(format_address(__addr),  Color.colorify(format_address(value), colors[idx]))
                line+= "    {}".format(text)
                derefs = DereferenceCommand.dereference_from(__addr)
                if len(derefs) > 2:
                    line+= "    [{} {}]".format(LEFT_ARROW, derefs[-1])
                if off == 0:
                    line+= "    Chunk[{}]".format(idx)
                if off == cur.ptrsize:
                    line+= "    {}{}{}{}".format(value&~7, "|NON_MAIN_ARENA" if value&4 else "", "|IS_MMAPED" if value&2 else "", "|PREV_INUSE" if value&1 else "")

                gef_print(line)

            next_chunk = cur.get_next_chunk()
            if next_chunk is None:
                break

            next_chunk_addr = Address(value=next_chunk.address)
            if not next_chunk_addr.valid:
                warn("next chunk probably corrupted")
                break

            cur = next_chunk
            idx += 1
        return


if __name__ == "__main__":
    register_external_command(VisualizeHeapChunksCommand())