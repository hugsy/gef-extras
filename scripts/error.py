__AUTHOR__ = "hugsy"
__VERSION__ = 0.1

import gdb
from ctypes import (CDLL, c_char_p, c_int32,)


class ErrorCommand(GenericCommand):
    """windbg !error-like command"""

    _cmdline_ = "error"
    _syntax_  = "{:s}".format(_cmdline_)
    _aliases_ = ["perror", ]
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        super(ErrorCommand, self).__init__(complete=gdb.COMPLETE_LOCATION)
        return

    def do_invoke(self, argv):
        argc = len(argv)
        if not argc and is_alive():
            value = get_register(current_arch.return_register)
        elif argv[0].isdigit():
            value = int(argv[0])
        else:
            value = int(gdb.parse_and_eval(argv[0]))

        __libc = CDLL("libc.so.6")
        __libc.strerror.restype = c_char_p
        __libc.strerror.argtypes = [c_int32, ]
        c_s = __libc.strerror(value).decode("utf8")
        gef_print("{0:d} ({0:#x}) : {1:s}".format(value, Color.greenify(c_s)))
        return


if __name__ == "__main__":
    register_external_command(ErrorCommand())
