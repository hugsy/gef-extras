import ctypes

NFASTBINS = 10
NBINS = 128
BINMAPSHIFT = 5
BITSPERMAP = 1 << BINMAPSHIFT
BINMAPSIZE = NBINS / BITSPERMAP

mfastbinptr = ctypes.c_uint64
mchunkptr = ctypes.c_uint64


class malloc_arena_t(ctypes.Structure):
    _fields_ = [
        ("mutex", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("fastbinsY", 10 * mfastbinptr),
        ("top", mchunkptr),
        ("last_remainder", mchunkptr),
        ("bins", 256 * mchunkptr),
        ("next", ctypes.c_uint64),
        ("next_free", ctypes.c_uint64),
        ("attached_threads", ctypes.c_uint64),
        ("system_mem", ctypes.c_uint64),
        ("max_system_mem", ctypes.c_uint64),
    ]
