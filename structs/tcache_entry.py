
import ctypes

TCACHE_MAX_BINS = 0x40

class tcache_perthread_struct_t(ctypes.Structure):
    _values_ = []

class tcache_entry_t(ctypes.Structure):
    _values_ = []

tcache_entry_t._fields_ = [
    ("next", ctypes.POINTER(tcache_entry_t)),
    ("key", ctypes.POINTER(tcache_perthread_struct_t)),
]

tcache_perthread_struct_t._fields_ = [
    ("counts", TCACHE_MAX_BINS * ctypes.c_uint16),
    ("entries", TCACHE_MAX_BINS * ctypes.POINTER(tcache_entry_t))
]
