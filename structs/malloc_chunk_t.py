#
# Dummy reconstitution from https://sourceware.org/glibc/wiki/MallocInternals
#
# @_hugsy_
#

import ctypes as ct


class malloc_chunk_t(ct.Structure):
    _fields_ = [
        ("prev_size", ct.c_uint64),
        ("size", ct.c_uint64),
    ]

    _values_ = []
