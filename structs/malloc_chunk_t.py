__AUTHOR__ = "hugsy"
__VERSION__ = 0.1
__DESCRIPTION__ = """glibc malloc chunk structure from https://sourceware.org/glibc/wiki/MallocInternals"""

from ctypes import *


class malloc_chunk_t(Structure):
    _values_ = []


malloc_chunk_t._fields_ = [
    ("prev_size", c_uint64),
    ("size", c_uint64),

    ("fd", POINTER(malloc_chunk_t)),
    ("bk", POINTER(malloc_chunk_t)),
]
