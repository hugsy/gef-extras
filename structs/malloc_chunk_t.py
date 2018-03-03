#
# Dummy reconstitution from https://sourceware.org/glibc/wiki/MallocInternals
#
# @_hugsy_
#

from ctypes import *

class malloc_chunk_t(Structure):
    _fields_ = [
        ("prev_size", c_uint64),
        ("size", c_uint64),
    ]

    _values_ = []
