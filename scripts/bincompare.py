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

import getopt
import gdb
import os

@register_external_command
class BincompareCommand(GenericCommand):
    """BincompareCommand: compare an binary file with the memory position looking for badchars."""
    _cmdline_ = "bincompare"
    _syntax_ = "{:s} -f FILE -a MEMORY_ADDRESS [-h]".format(_cmdline_)

    def __init__(self):
        super(BincompareCommand, self).__init__(complete=gdb.COMPLETE_FILENAME)
        return

    def usage(self):
        h = self._syntax_
        h += "\n\t-f FILE specifies the binary file to be compared.\n"
        h += "\t-a MEMORY_ADDRESS sepecifies the memory address.\n"
        info(h)
        return

    @only_if_gdb_running
    def do_invoke(self, argv):
        filename = None
        start_addr = None
        size = 0
        file_data = None
        memory_data = None

        opts, args = getopt.getopt(argv, "f:a:ch")
        for o, a in opts:
            if o == "-f":
                filename = a
            elif o == "-a":
                start_addr = int(gdb.parse_and_eval(a))
            elif o == "-h":
                self.usage()
                return

        if not filename or not start_addr:
            err("No file and/or address specified")
            return

        if not os.path.isfile(filename):
            err("Especified file '{:s}' not exists".format(filename))
            return

        f = open(filename, "rb")
        file_data = f.read()
        f.close()

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
                result_table.append((hexchar, "{:02x}".format(memory_data[cnt])))
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

