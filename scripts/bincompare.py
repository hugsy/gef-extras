#
# compare an binary file with the memory position looking for badchars
#
# @helviojunior
# https://www.helviojunior.com.br/
#
# Load with:
# gef> source /path/to/bincompare.py
#
# Use with
# gef> bincompare -f /path/to/bytearray.bin -a memory_address
#

import pathlib
from typing import TYPE_CHECKING, Any, List

import gdb

if TYPE_CHECKING:
    from . import *

__AUTHOR__ = "@helviojunior"
__VERSION__ = 0.2
__LICENSE__ = "MIT"


@register
class BincompareCommand(GenericCommand):
    """Compare an binary file with the memory position looking for badchars."""
    _cmdline_ = "bincompare"
    _syntax_ = f"{_cmdline_} MEMORY_ADDRESS FILE"

    def __init__(self):
        super().__init__(complete=gdb.COMPLETE_FILENAME)
        return

    def usage(self):
        h = (self._syntax_ + "\n" +
             "\tMEMORY_ADDRESS sepecifies the memory address.\n" +
             "\tFILE specifies the binary file to be compared.")
        info(h)
        return

    @only_if_gdb_running
    @parse_arguments({"address": "", "filename": ""}, {})
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        size = 0
        file_data = None
        memory_data = None

        args = kwargs["arguments"]
        if not args.address or not args.filename:
            err("No file and/or address specified")
            return

        start_addr = parse_address(args.address)
        filename = pathlib.Path(args.filename)

        if not filename.exists():
            err(f"Specified file '{filename}' not exists")
            return

        file_data = filename.open("rb").read()
        size = len(file_data)

        if size < 8:
            err("Error - file does not contain enough bytes (min 8 bytes needed)")
            return

        try:
            memory_data = gef.memory.read(start_addr, size)
        except gdb.MemoryError:
            err("Cannot reach memory {:#x}".format(start_addr))
            return

        result_table = []
        badchars = ""
        cnt = 0
        corrupted = -1
        for eachByte in file_data:
            hexchar = "{:02x}".format(eachByte)
            if cnt > len(memory_data):
                result_table.append((hexchar, "--"))
                corrupted = -1
            elif eachByte == memory_data[cnt]:
                result_table.append((hexchar, "  "))
                corrupted = -1
            else:
                result_table.append(
                    (hexchar, "{:02x}".format(memory_data[cnt])))
                if len(badchars) == 0:
                    badchars = hexchar
                else:
                    badchars += ", " + hexchar
                if corrupted == -1:
                    corrupted = cnt
            cnt += 1

        line = 0

        info("Comparison result:")
        gef_print("    +-----------------------------------------------+")
        for line in range(0, len(result_table), 16):
            pdata1 = []
            pdata2 = []
            for i in range(line, line + 16):
                if i < len(result_table):
                    pdata1.append(result_table[i][0])
                    pdata2.append(result_table[i][1])

            self.print_line("{:02x}".format(line), pdata1, "file")
            self.print_line("  ", pdata2, "memory")

        gef_print("    +-----------------------------------------------+")
        gef_print("")

        if corrupted > -1:
            info("Corruption after {:d} bytes".format(corrupted))

        if badchars == "":
            info("No badchars found!")
        else:
            info("Badchars found: {:s}".format(badchars))

        return

    def print_line(self, line, data, label):
        l = []
        for d in data:
            l.append(d)
        r = 16 - len(l)
        for i in range(0, r):
            l.append("--")

        gef_print(" {:s} |{:s} {:s} {:s} {:s} {:s} {:s} {:s} {:s} {:s} {:s} {:s} {:s} {:s} {:s} {:s} {:s}| {:s}"
                  .format(line, l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8],
                          l[9], l[10], l[11], l[12], l[13], l[14], l[15], label))
