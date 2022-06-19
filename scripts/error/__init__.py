__AUTHOR__ = "hugsy"
__VERSION__ = 0.1

import ctypes
from typing import TYPE_CHECKING

import gdb

if TYPE_CHECKING:
    from .. import *
    from .. import gdb


@register
class ErrorCommand(GenericCommand):
    """WinDbg `!error` -like command"""

    _cmdline_ = "error"
    _syntax_ = f"{_cmdline_:s}"
    _aliases_ = ["perror", ]
    _example_ = f"{_cmdline_:s}"

    def __init__(self):
        super().__init__(complete=gdb.COMPLETE_LOCATION)
        return

    def do_invoke(self, argv):
        argc = len(argv)
        if argc == 0 and is_alive():
            value = gef.arch.register(gef.arch.return_register)
        elif argv[0].isdigit():
            value = int(argv[0])
        else:
            value = parse_address(argv[0])

        __libc = ctypes.CDLL("libc.so.6")
        __libc.strerror.restype = ctypes.c_char_p
        __libc.strerror.argtypes = [ctypes.c_int32, ]
        c_s = __libc.strerror(value).decode("utf8")
        info(f"{value:d} ({value:#x}) : {Color.greenify(c_s):s}")
        return
