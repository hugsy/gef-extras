__AUTHOR__ = "hugsy"
__VERSION__ = 0.1

import os
import gdb


def fastbin_index(sz):
    return (sz >> 4) - 2 if current_arch.ptrsize == 8 else (sz >> 3) - 2


def nfastbins():
    return fastbin_index( (80 * current_arch.ptrsize // 4)) - 1


def get_tcache_count():
    count_addr = HeapBaseFunction.heap_base() + 2*current_arch.ptrsize
    count = p8(count_addr) if get_libc_version() < (2, 30) else p16(count_addr)
    return count


@lru_cache
def collect_known_values() -> dict:
    # { 0xaddress : "name" ,}
    arena = get_main_arena()
    result = {}

    # tcache
    for i in range(GlibcArena.TCACHE_MAX_BINS):
        chunk = arena.tcachebin(i)
        j = 0
        while True:
            if chunk is None:
                break
            result[chunk.address] = "tcachebins[{}/{}]".format(i, j)
            next_chunk_address = chunk.get_fwd_ptr(True)
            if not next_chunk_address: break
            next_chunk = GlibcChunk(next_chunk_address)
            j += 1
            chunk = next_chunk

    # fastbins
    for i in range(nfastbins()):
        chunk = arena.fastbin(i)
        j = 0
        while True:
            if chunk is None:
                break
            result[chunk.address] = "fastbins[{}/{}]".format(i, j)
            next_chunk_address = chunk.get_fwd_ptr(True)
            if not next_chunk_address: break
            next_chunk = GlibcChunk(next_chunk_address)
            j += 1
            chunk = next_chunk

    # other bins
    for name in ["unorderedbins", "smallbins", "largebins"]:
        fw, bk = arena.bin(i)
        if bk==0x00 and fw==0x00: continue
        head = GlibcChunk(bk, from_base=True).fwd
        if head == fw: continue

        chunk = GlibcChunk(head, from_base=True)
        j = 0
        while True:
            if chunk is None: break
            result[chunk.address] = "{}[{}/{}]".format(name, i, j)
            next_chunk_address = chunk.get_fwd_ptr(True)
            if not next_chunk_address: break
            next_chunk = GlibcChunk(next_chunk_address, from_base=True)
            j += 1
            chunk = next_chunk

    print(result)
    return result


@lru_cache
def collect_known_ranges()->list:
    result = []
    for entry in get_process_maps():
        if not entry.path:
            continue
        path = os.path.basename(entry.path)
        result.append( (range(entry.page_start, entry.page_end), path) )

    return result


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

        known_ranges = collect_known_ranges()
        known_values = collect_known_values()

        while True:
            addr = cur.chunk_base_address

            if addr == top:
                gef_print("{}    {}".format(format_address(addr), Color.colorify(LEFT_ARROW + "Top Chunk", "red bold")))
                break

            if cur.size == 0:
                warn("incorrect size, heap is corrupted")
                break

            for off in range(0, cur.size, cur.ptrsize):
                __addr = addr + off
                value = align_address( read_int_from_memory(__addr) )
                text = "".join([chr(b) if 0x20 <= b < 0x7F else "." for b in read_memory(__addr, cur.ptrsize)])
                line = "{}    {}".format(format_address(__addr),  Color.colorify(format_address(value), colors[idx % len(colors)]))
                line+= "    {}".format(text)
                derefs = DereferenceCommand.dereference_from(__addr)
                if len(derefs) > 2:
                    line+= "    [{}{}]".format(LEFT_ARROW, derefs[-1])

                if off == 0:
                    line+= "    Chunk[{}]".format(idx)
                if off == cur.ptrsize:
                    line+= "    {}{}{}{}".format(value&~7, "|NON_MAIN_ARENA" if value&4 else "", "|IS_MMAPED" if value&2 else "", "|PREV_INUSE" if value&1 else "")

                # look in mapping
                for x in known_ranges:
                    if value in x[0]:
                        line+= " (in {})".format(Color.redify(x[1]))

                # look in known values
                if value in known_values:
                    line += "{}{}".format(RIGHT_ARROW, Color.cyanify(known_values[value]))

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