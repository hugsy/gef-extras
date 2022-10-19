__AUTHOR__ = "hugsy"
__VERSION__ = 0.4.2

import os
import tempfile
from typing import TYPE_CHECKING
import gdb

if TYPE_CHECKING:
    from gef import *

TEMPLATE = """#!/usr/bin/env python3
import sys, os
from pwn import *
context.update(
    arch="{arch}",
    endian="{endian}",
    os="linux",
    log_level="debug",
    terminal=["tmux", "split-window", "-h", "-p 65"],
)

REMOTE = False
TARGET=os.path.realpath("{filepath}")
elf = ELF(TARGET)

def attach(r):
    if not REMOTE:
        bkps = {bkps}
        cmds = []
        gdb.attach(r, '\\n'.join(["break {{}}".format(x) for x in bkps] + cmds))
    return

def exploit(r):
    attach(r)
    # r.sendlineafter(b"> ", b"HelloPwn" )
    r.interactive()
    return

if __name__ == "__main__":
    if len(sys.argv)==2 and sys.argv[1]=="remote":
        REMOTE = True
        r = remote("{target}", {port})
    else:
        REMOTE = False
        r = process([TARGET,])
    exploit(r)
    exit(0)
"""


@register
class ExploitTemplateCommand(GenericCommand):
    """Generates a exploit template."""
    _cmdline_ = "exploit-template"
    _syntax_ = f"{_cmdline_} [local|remote TARGET:PORT]"
    _aliases_ = ["skeleton", ]

    @only_if_gdb_running
    def do_invoke(self, args):
        if len(args) < 1:
            self.usage()
            return

        scope = args[0].lower()
        if scope not in ("local", "remote"):
            self.usage()
            return

        target, port = "127.0.0.1", "1337"
        if scope == "remote":
            if len(args) < 2:
                self.usage()
                return

            target, port = args[1].split(":", 1)
            port = int(port)

        bkps = [b.location for b in gdb.breakpoints()]
        temp = TEMPLATE.format(
            target=target,
            port=port,
            arch="amd64" if isinstance(gef.arch, X86_64) else "i386",
            endian="big" if gef.arch.endianness == Endianness.BIG_ENDIAN else "little",
            filepath=gef.binary.path,
            bkps=bkps
        )
        fd, fname = tempfile.mkstemp(suffix='.py', prefix='gef_')
        with os.fdopen(fd, "w") as f:
            f.write(temp)

        ok("Exploit generated in '{:s}'".format(fname))
        return
