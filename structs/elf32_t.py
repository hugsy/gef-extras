#
# ELF (32b) parsing from http://www.skyfree.org/linux/references/ELF_Format.pdf
#
# @_hugsy_
#

import ctypes as ct


class elf32_t(ct.Structure):

    _fields_ = [
        ("ei_magic", ct.c_char * 4),
        ("ei_class", ct.c_uint8),
        ("ei_data", ct.c_uint8),
        ("ei_version", ct.c_uint8),
        ("ei_padd", ct.c_char * 9),
        ("e_type", ct.c_uint16),
        ("e_machine", ct.c_uint16),
        ("e_version", ct.c_uint32),
        ("e_entry", ct.c_uint32),
    ]

    _values_ = [
        (
            "ei_magic",
            [
                (b"\x7fELF", "Correct ELF header"),
                (None, "Incorrect ELF header"),  # None -> default case
            ],
        ),
        (
            "e_type",
            [
                (0, "ET_NONE"),
                (1, "ET_REL"),
                (2, "ET_EXEC"),
                (3, "ET_DYN"),
                (None, "Unknown type"),
            ],
        ),
        (
            "e_machine",
            [
                (0, "EM_NONE"),
                (1, "EM_M32"),
                (2, "EM_SPARC"),
                (3, "EM_386"),
                (4, "EM_68K"),
                (5, "EM_88K"),
                (7, "EM_860"),
                (8, "EM_MIPS"),
                (40, "EM_ARM"),
                (21, "EM_ALPHA"),
                (None, "Unknown machine"),
            ],
        ),
    ]
