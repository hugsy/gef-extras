#
# ELF (64b) parsing from https://www.uclibc.org/docs/elf-64-gen.pdf
#
# @_hugsy_
#

import ctypes as ct

Elf64_Addr = ct.c_uint64
Elf64_Off = ct.c_uint64
Elf64_Half = ct.c_uint16
Elf64_Word = ct.c_int32
Elf64_Sword = ct.c_int32
Elf64_Xword = ct.c_uint64
Elf64_Sxword = ct.c_int64


class elf64_t(ct.Structure):
    _fields_ = [
        ("ei_magic", ct.c_char * 4),  # ELF identification
        ("ei_class", ct.c_uint8),
        ("ei_data", ct.c_uint8),
        ("ei_version", ct.c_uint8),
        ("ei_padd", ct.c_char * 9),
        ("e_type", Elf64_Half),  #  Object file type
        ("e_machine", Elf64_Half),  #  Machine type
        ("e_version", Elf64_Word),  #  Object file version
        ("e_entry", Elf64_Addr),  #  Entry point address
        ("e_phoff", Elf64_Off),  #  Program header offset
        ("e_shoff", Elf64_Off),  #  Section header offset
        ("e_flags", Elf64_Word),  #  Processor-specific flags
        ("e_ehsize", Elf64_Half),  #  ELF header size
        ("e_phentsize", Elf64_Half),  #  Size of program header entry
        ("e_phnum", Elf64_Half),  #  Number of program header entries
        ("e_shentsize", Elf64_Half),  #  Size of section header entry
        ("e_shnum", Elf64_Half),  #  Number of section header entries
        ("e_shstrndx", Elf64_Half),  #  Section name string table index
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
            "ei_class",
            [
                (0, "ELFCLASSNONE"),
                (1, "ELFCLASS32"),
                (2, "ELFCLASS64"),
                (None, "Incorrect ELF class"),
            ],
        ),
        (
            "e_type",
            [
                (0, "ET_NONE"),
                (1, "ET_REL"),
                (2, "ET_EXEC"),
                (3, "ET_DYN"),
                (4, "ET_CORE"),
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
                (62, "EM_AMD64"),
                (None, "Unknown machine"),
            ],
        ),
    ]
