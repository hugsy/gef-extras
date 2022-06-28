"""
Provide an ascii-based graphical representation of the heap layout.

"""
__AUTHOR__ = "hugsy"
__VERSION__ = 0.3
__LICENSE__ = "MIT"

import os
from functools import lru_cache
from typing import TYPE_CHECKING, Dict, List, Tuple

import gdb

if TYPE_CHECKING:
    from . import *
    from . import gdb


def fastbin_index(sz):
    return (sz >> 4) - 2 if gef.arch.ptrsize == 8 else (sz >> 3) - 2


def nfastbins():
    return fastbin_index((80 * gef.arch.ptrsize // 4)) - 1


def get_tcache_count():
    version = gef.libc.version
    if version is None:
        raise RuntimeError("Cannot get the libc version")
    if version < (2, 27):
        return 0
    base = gef.heap.base_address
    if not base:
        raise RuntimeError(
            "Failed to get the heap base address. Heap not initialized?")
    count_addr = base + 2*gef.arch.ptrsize
    count = p8(count_addr) if version < (2, 30) else p16(count_addr)
    return count


@lru_cache(128)
def collect_known_values() -> Dict[int, str]:
    arena = gef.heap.main_arena
    result: Dict[int, str] = {}  # format is { 0xaddress : "name" ,}

    version = gef.libc.version
    if not version:
        return result

    # tcache
    if version >= (2, 27):
        tcache_addr = GlibcHeapTcachebinsCommand.find_tcache()
        for i in range(GlibcHeapTcachebinsCommand.TCACHE_MAX_BINS):
            chunk, _ = GlibcHeapTcachebinsCommand.tcachebin(tcache_addr, i)
            j = 0
            while True:
                if chunk is None:
                    break
                sz = (i+1)*0x10+0x10
                result[chunk.data_address] = f"tcachebins[{i}/{j}] (size={sz:#x})"
                next_chunk_address = chunk.get_fwd_ptr(True)
                if not next_chunk_address:
                    break
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
            result[chunk.data_address] = f"fastbins[{i}/{j}]"
            next_chunk_address = chunk.get_fwd_ptr(True)
            if not next_chunk_address:
                break
            next_chunk = GlibcChunk(next_chunk_address)
            j += 1
            chunk = next_chunk

    # other bins
    for name in ["unorderedbins", "smallbins", "largebins"]:

        fw, bk = arena.bin(j)
        if bk == 0x00 and fw == 0x00:
            continue
        head = GlibcChunk(bk, from_base=True).fwd
        if head == fw:
            continue

        chunk = GlibcChunk(head, from_base=True)
        j = 0
        while True:
            if chunk is None:
                break
            result[chunk.data_address] = f"{name}[{i}/{j}]"
            next_chunk_address = chunk.get_fwd_ptr(True)
            if not next_chunk_address:
                break
            next_chunk = GlibcChunk(next_chunk_address, from_base=True)
            j += 1
            chunk = next_chunk

    return result


@lru_cache(128)
def collect_known_ranges() -> List[Tuple[range, str]]:
    result = []
    for entry in gef.memory.maps:
        if not entry.path:
            continue
        path = os.path.basename(entry.path)
        result.append((range(entry.page_start, entry.page_end), path))
    return result


@register
class VisualizeHeapChunksCommand(GenericCommand):
    """Visual helper for glibc heap chunks"""

    _cmdline_ = "visualize-libc-heap-chunks"
    _syntax_ = f"{_cmdline_:s}"
    _aliases_ = ["heap-view", ]
    _example_ = f"{_cmdline_:s}"

    def __init__(self):
        super().__init__(complete=gdb.COMPLETE_SYMBOL)
        return

    @only_if_gdb_running
    def do_invoke(self, _):
        ptrsize = gef.arch.ptrsize
        heap_base_address = gef.heap.base_address
        arena = gef.heap.main_arena
        if not arena.top or not heap_base_address:
            err("The heap has not been initialized")
            return

        top = align_address(int(arena.top))
        base = align_address(heap_base_address)

        colors = ["cyan", "red", "yellow", "blue", "green"]
        cur = GlibcChunk(base, from_base=True)
        idx = 0

        known_ranges = collect_known_ranges()
        known_values = collect_known_values()

        while True:
            base = cur.base_address
            addr = cur.data_address
            aggregate_nuls = 0

            if base == top:
                gef_print(
                    f"{format_address(addr)}    {format_address(gef.memory.read_integer(addr))}   {Color.colorify(LEFT_ARROW + 'Top Chunk', 'red bold')}\n"
                    f"{format_address(addr+ptrsize)}    {format_address(gef.memory.read_integer(addr+ptrsize))}   {Color.colorify(LEFT_ARROW + 'Top Chunk Size', 'red bold')}"
                )
                break

            if cur.size == 0:
                warn("Unexpected size for chunk, cannot pursue. Corrupted heap?")
                break

            for off in range(0, cur.size, ptrsize):
                addr = base + off
                value = gef.memory.read_integer(addr)
                if value == 0:
                    if off != 0 and off != cur.size - ptrsize:
                        aggregate_nuls += 1
                        if aggregate_nuls > 1:
                            continue

                if aggregate_nuls > 2:
                    gef_print(
                        "        ↓",
                        "      [...]",
                        "        ↓"
                    )
                    aggregate_nuls = 0

                text = "".join(
                    [chr(b) if 0x20 <= b < 0x7F else "." for b in gef.memory.read(addr, ptrsize)])
                line = f"{format_address(addr)}    {Color.colorify(format_address(value), colors[idx % len(colors)])}"
                line += f"    {text}"
                derefs = dereference_from(addr)
                if len(derefs) > 2:
                    line += f"    [{LEFT_ARROW}{derefs[-1]}]"

                if off == 0:
                    line += f"    Chunk[{idx}]"
                if off == ptrsize:
                    line += f"    {value&~7 }" \
                        f"{'|NON_MAIN_ARENA' if value&4 else ''}" \
                        f"{'|IS_MMAPED' if value&2 else ''}" \
                        f"{'|PREV_INUSE' if value&1 else ''}"

                # look in mapping
                for x in known_ranges:
                    if value in x[0]:
                        line += f" (in {Color.redify(x[1])})"

                # look in known values
                if value in known_values:
                    line += f"{RIGHT_ARROW}{Color.cyanify(known_values[value])}"

                gef_print(line)

            next_chunk = cur.get_next_chunk()
            if next_chunk is None:
                break

            next_chunk_addr = Address(value=next_chunk.data_address)
            if not next_chunk_addr.valid:
                warn("next chunk probably corrupted")
                break

            cur = next_chunk
            idx += 1
        return
