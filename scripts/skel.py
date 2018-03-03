#
# Quick'n dirty exploit template
#
# @_hugsy_
#
# Load with:
# gef> source /path/to/skel.py
#
# Use with
# gef> skel [local|remote=TARGET:PORT]
#

import os, tempfile

TEMPLATE="""#!/usr/bin/env python2
import sys
from pwn import *
context.update(arch="{arch}", endian="{endian}", os="linux", log_level="debug",
               terminal=["tmux", "split-window", "-v", "-p 85"],)
LOCAL, REMOTE = False, False
TARGET=os.path.realpath("{filepath}")
elf = ELF(TARGET)

def attach(r):
    if LOCAL:
        bkps = {bkps}
        gdb.attach(r, '\\n'.join(["break %s"%(x,) for x in bkps]))
    return

def exploit(r):
    attach(r)
    r.interactive()
    return

if __name__ == "__main__":
    if len(sys.argv)==2 and sys.argv[1]=="remote":
        REMOTE = True
        r = remote("{target}", {port})
    else:
        LOCAL = True
        r = process([TARGET,])
    exploit(r)
    sys.exit(0)
"""

class ExploitTemplateCommand(GenericCommand):
    """Generates a exploit template."""
    _cmdline_ = "exploit-template"
    _syntax_  = "{:s} [local|remote=TARGET:PORT]".format(_cmdline_)
    _aliases_ = ["skel", ]

    @only_if_gdb_running
    def do_invoke(self, args):
        if len(args) < 1:
            self.usage()
            return

        if args[0]!="local" and not args[0].startswith("remote="):
            self.usage()
            return

        target, port = "127.0.0.1", "1337"
        if args[0].startswith("remote"):
            target, port = args[0][len("remote="):].split(":")

        fd, fname = tempfile.mkstemp(suffix='.py', prefix='gef_')
        temp = TEMPLATE.format(target=target,
                               port=port,
                               arch="amd64" if "x86-64" in get_arch() else "i386",
                               endian="big" if is_big_endian() else "little",
                               filepath=get_filepath(),
                               bkps=[b.location for b in gdb.breakpoints()])
        os.write(fd, gef_pybytes(temp))
        os.close(fd)
        ok("Exploit generated in '{:s}'".format(fname))
        return


if __name__ == "__main__":
    register_external_command( ExploitTemplateCommand() )
