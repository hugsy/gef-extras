from ctypes import *

# http://sourceware.org/git/?p=glibc.git;a=blob;f=libio/libio.h;hb=765de945efc5d5602999b2999fe8abdf04881370#l67
_IO_MAGIC = 0xFBAD0000

class io_file64_plus_t(Structure):
    _fields_ = [
        ("_p1",                    c_uint64),
        ("_p2",                    c_uint64),
        ("_IO_file_finish",        c_uint64),
        ("_IO_file_overflow",      c_uint64),
        ("_IO_file_underflow",     c_uint64),
        ("_IO_default_uflow",      c_uint64),
        ("_IO_default_pbackfail",  c_uint64),
        ("_IO_file_xsputn",        c_uint64),
        ("_IO_Unk1",               c_uint64),
        ("_IO_file_seekoff",       c_uint64),
        ("_IO_Unk1",               c_uint64),
        ("_IO_file_setbuf",        c_uint64),
        ("_IO_file_sync",          c_uint64),
        ("_IO_file_doallocate",    c_uint64),
        ("_IO_file_read",          c_uint64),
        ("_IO_file_write",         c_uint64),
        ("_IO_file_seek",          c_uint64),
        ("_IO_file_close",         c_uint64),
        ("_IO_file_stat",          c_uint64),
    ]

    _values_ = [
    ]


class io_file64_t(Structure):
    # http://sourceware.org/git/?p=glibc.git;a=blob;f=libio/libio.h;h=3cf1712ea98d3c253f418feb1ef881c4a44649d5;hb=HEAD#l245
    _fields_ = [
        ("_flags",          c_uint16),
        ("_magic",          c_uint16), # should be equal to _IO_MAGIC
        ("_IO_read_ptr",    c_uint64), # /* Current read pointer */
        ("_IO_read_end",    c_uint64), # /* End of get area. */
        ("_IO_read_base",   c_uint64), # /* Start of putback+get area. */
        ("_IO_write_base",  c_uint64), # /* Start of put area. */
        ("_IO_write_ptr",   c_uint64), # /* Current put pointer. */
        ("_IO_write_end",   c_uint64), # /* End of put area. */
        ("_IO_buf_base",    c_uint64), # /* Start of reserve area. */
        ("_IO_buf_end",     c_uint64), # /* End of reserve area. */
        ("_IO_save_base",   c_uint64), # /* Pointer to start of non-current get area. */
        ("_IO_backup_base", c_uint64), # /* Pointer to first valid character of backup area */
        ("_IO_save_end",    c_uint64), # /* Pointer to end of non-current get area. */
        ("_markers",        c_char_p),
        ("_chain",          POINTER(io_file64_plus_t)),
        # TODO: some fields are missing, add them
    ]

    _values_ = [
        ("_magic", [
            (_IO_MAGIC >> 16, "Correct magic"),
            (None, "Incorrect magic (corrupted?)"),
        ]),
    ]
