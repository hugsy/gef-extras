import ctypes as ct
from ctypes import POINTER

# http://sourceware.org/git/?p=glibc.git;a=blob;f=libio/libio.h;hb=765de945efc5d5602999b2999fe8abdf04881370#l67
_IO_MAGIC = 0xFBAD0000


class io_file64_plus_t(ct.Structure):
    _fields_ = [
        ("_p1", ct.c_uint64),
        ("_p2", ct.c_uint64),
        ("_IO_file_finish", ct.c_uint64),
        ("_IO_file_overflow", ct.c_uint64),
        ("_IO_file_underflow", ct.c_uint64),
        ("_IO_default_uflow", ct.c_uint64),
        ("_IO_default_pbackfail", ct.c_uint64),
        ("_IO_file_xsputn", ct.c_uint64),
        ("_IO_Unk1", ct.c_uint64),
        ("_IO_file_seekoff", ct.c_uint64),
        ("_IO_Unk1", ct.c_uint64),
        ("_IO_file_setbuf", ct.c_uint64),
        ("_IO_file_sync", ct.c_uint64),
        ("_IO_file_doallocate", ct.c_uint64),
        ("_IO_file_read", ct.c_uint64),
        ("_IO_file_write", ct.c_uint64),
        ("_IO_file_seek", ct.c_uint64),
        ("_IO_file_close", ct.c_uint64),
        ("_IO_file_stat", ct.c_uint64),
    ]

    _values_ = []


class io_file64_t(ct.Structure):
    # http://sourceware.org/git/?p=glibc.git;a=blob;f=libio/libio.h;h=3cf1712ea98d3c253f418feb1ef881c4a44649d5;hb=HEAD#l245
    _fields_ = [
        ("_flags", ct.c_uint16),
        ("_magic", ct.c_uint16),  # should be equal to _IO_MAGIC
        ("_IO_read_ptr", ct.c_uint64),  # /* Current read pointer */
        ("_IO_read_end", ct.c_uint64),  # /* End of get area. */
        ("_IO_read_base", ct.c_uint64),  # /* Start of putback+get area. */
        ("_IO_write_base", ct.c_uint64),  # /* Start of put area. */
        ("_IO_write_ptr", ct.c_uint64),  # /* Current put pointer. */
        ("_IO_write_end", ct.c_uint64),  # /* End of put area. */
        ("_IO_buf_base", ct.c_uint64),  # /* Start of reserve area. */
        ("_IO_buf_end", ct.c_uint64),  # /* End of reserve area. */
        (
            "_IO_save_base",
            ct.c_uint64,
        ),  # /* Pointer to start of non-current get area. */
        (
            "_IO_backup_base",
            ct.c_uint64,
        ),  # /* Pointer to first valid character of backup area */
        ("_IO_save_end", ct.c_uint64),  # /* Pointer to end of non-current get area. */
        ("_markers", ct.c_char_p),
        ("_chain", POINTER(io_file64_plus_t)),
        # TODO: some fields are missing, add them
    ]

    _values_ = [
        (
            "_magic",
            [
                (_IO_MAGIC >> 16, "Correct magic"),
                (None, "Incorrect magic (corrupted?)"),
            ],
        ),
    ]
