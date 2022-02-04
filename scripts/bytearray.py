#
# Generate a bytearray to be compared with possible badchars.
#
# @helviojunior
# https://www.helviojunior.com.br/
#
# Load with:
# gef> source /path/to/bytearray.py
#
# Use with
# gef> bytearray -b "\x00\x0a\x0d"
#

import getopt
import gdb
import re

@register_external_command
class BytearrayCommand(GenericCommand):
    """BytearrayCommand: Generate a bytearray to be compared with possible badchars.
Function ported from mona.py"""
    _cmdline_ = "bytearray"
    _syntax_ = "{:s} [-b badchars]".format(_cmdline_)

    def __init__(self):
        super(BytearrayCommand, self).__init__(complete=gdb.COMPLETE_FILENAME)
        return

    def usage(self):
        h = self._syntax_
        h += "\n\t-b badchars specifies the excluded badchars.\n"
        info(h)
        return

    def do_invoke(self, argv):
        badchars = ""
        bytesperline = 32
        startval = 0
        endval = 255

        opts, args = getopt.getopt(argv, "b:ch")
        for o, a in opts:
            if o == "-b":
                badchars = a
            elif o == "-h":
                self.usage()
                return

        badchars = self.cleanHex(badchars)

        # see if we need to expand ..
        bpos = 0
        newbadchars = ""
        while bpos < len(badchars):
            curchar = badchars[bpos] + badchars[bpos + 1]
            if curchar == "..":
                pos = bpos
                if pos > 1 and pos <= len(badchars) - 4:
                    # get byte before and after ..
                    bytebefore = badchars[pos - 2] + badchars[pos - 1]
                    byteafter = badchars[pos + 2] + badchars[pos + 3]
                    bbefore = int(bytebefore, 16)
                    bafter = int(byteafter, 16)
                    insertbytes = ""
                    bbefore += 1
                    while bbefore < bafter:
                        insertbytes += "%02x" % bbefore
                        bbefore += 1
                    newbadchars += insertbytes
            else:
                newbadchars += curchar
            bpos += 2
        badchars = newbadchars

        cnt = 0
        excluded = []
        while cnt < len(badchars):
            excluded.append(self.hex2bin(badchars[cnt] + badchars[cnt + 1]))
            cnt = cnt + 2

        info("Generating table, excluding {:d} bad chars...".format(len(excluded)))
        arraytable = []
        binarray = bytearray()

        # handle range() last value
        if endval > startval:
            increment = 1
            endval += 1
        else:
            endval += -1
            increment = -1

        # create bytearray
        for thisval in range(startval, endval, increment):
            hexbyte = "{:02x}".format(thisval)
            binbyte = self.hex2bin(hexbyte)
            intbyte = self.hex2int(hexbyte)
            if binbyte not in excluded:
                arraytable.append(hexbyte)
                binarray.append(intbyte)

        info("Dumping table to file")
        output = ""
        cnt = 0
        outputline = '"'
        totalbytes = len(arraytable)
        tablecnt = 0
        while tablecnt < totalbytes:
            if (cnt < bytesperline):
                outputline += "\\x" + arraytable[tablecnt]
            else:
                outputline += '"\n'
                cnt = 0
                output += outputline
                outputline = '"\\x' + arraytable[tablecnt]
            tablecnt += 1
            cnt += 1
        if (cnt - 1) < bytesperline:
            outputline += '"\n'
        output += outputline

        gef_print(output)

        binfilename = "bytearray.bin"
        arrayfile = "bytearray.txt"
        binfile = open(binfilename, "wb")
        binfile.write(binarray)
        binfile.close()

        txtfile = open(arrayfile, "w+")
        txtfile.write(output)
        txtfile.close()

        info("Done, wrote {:d} bytes to file {:s}".format(len(arraytable), arrayfile))
        info("Binary output saved in {:s}".format(binfilename))

        return

    def hex2bin(self, pattern):
        """
        Converts a hex string (\\x??\\x??\\x??\\x??) to real hex bytes

        Arguments:
        pattern - A string representing the bytes to convert

        Return:
        the bytes
        """
        pattern = pattern.replace("\\x", "")
        pattern = pattern.replace("\"", "")
        pattern = pattern.replace("\'", "")
        return binascii.unhexlify(pattern)

    def cleanHex(self, hex):
        return "".join(filter(self.permitted_char, hex))

    def hex2int(self, hex):
        return int(hex, 16)

    def permitted_char(self, s):
        if bool(re.match("^[A-Fa-f0-9]", s)):
            return True
        else:
            return False

