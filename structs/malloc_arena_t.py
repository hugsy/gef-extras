import ctypes

#
# 2.31 -> https://elixir.bootlin.com/glibc/glibc-2.31/source/malloc/malloc.c#L1655
# 2.34 -> https://elixir.bootlin.com/glibc/glibc-2.34/source/malloc/malloc.c#L1831
#

NFASTBINS = 10
NBINS = 254
BINMAPSIZE = 0x10


def malloc_state64_t(gef = None):
    pointer = ctypes.c_uint64 if gef and gef.arch.ptrsize == 8 else ctypes.c_uint32

    fields = [
        ("mutex", ctypes.c_uint32),
        ("have_fastchunks", ctypes.c_uint32),
    ]

    if gef and gef.libc.version and gef.libc.version >= (2, 27):
        fields += [("fastbinsY", NFASTBINS * pointer), ]

    fields += [
        ("top", pointer),
        ("last_remainder", pointer),
        ("bins", NBINS * pointer),
        ("binmap", BINMAPSIZE * ctypes.c_uint32),
        ("next", pointer),
        ("next_free", pointer),
        ("attached_threads", pointer),
        ("system_mem", pointer),
        ("max_system_mem", pointer),
    ]

    class malloc_state64_cls(ctypes.Structure):
        _fields_ = fields

    return malloc_state64_cls
