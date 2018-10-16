#
# ELF (32b) parsing from http://www.skyfree.org/linux/references/ELF_Format.pdf
#
# @_hugsy_
#

from ctypes import *


class elf32_t(Structure):

    _fields_ = [
        ("ei_magic", c_char * 4),
        ("ei_class", c_uint8),
        ("ei_data", c_uint8),
        ("ei_version", c_uint8),
        ("ei_padd", c_char * 9),

        ("e_type", c_uint16),
        ("e_machine", c_uint16),
        ("e_version", c_uint32),
        ("e_entry", c_uint32),

    ]

    _values_ = [
        ("ei_magic", [
            (b"\x7fELF", "Correct ELF header"),
            (None, "Incorrect ELF header"), # None -> default case
        ]),

        ("e_type", [
            (0, "ET_NONE"),
            (1, "ET_REL"),
            (2, "ET_EXEC"),
            (3, "ET_DYN"),
            (None, "Unknown type"),
        ]),

        ("e_machine", [
            (0 , "EM_NONE"),
            (1 , "EM_M32"),
            (2 , "EM_SPARC"),
            (3 , "EM_386"),
            (4 , "EM_68K"),
            (5 , "EM_88K"),
            (7 , "EM_860"),
            (8 , "EM_MIPS"),
            (40, "EM_ARM"),
            (None, "Unknown machine")
        ]),
    ]
