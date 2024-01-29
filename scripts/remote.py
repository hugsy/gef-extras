"""
A slightly better way to remote with GDB/GEF

gdb -ex 'source /path/to/gef-extras/scripts/remote.py' -ex rpyc-remote -ex quit
"""

__AUTHOR__ = "hugsy"
__VERSION__ = 0.3

import argparse

import gdb

import rpyc

from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    import rpyc.core.protocol
    import rpyc.utils.server
    from . import *
    from . import gdb

RPYC_DEFAULT_HOST = "0.0.0.0"
RPYC_DEFAULT_PORT = 12345


class RemoteDebugService(rpyc.Service):
    def on_connect(self, conn: rpyc.core.protocol.Connection):
        ok(f"connect open: {str(conn)}")
        return

    def on_disconnect(self, conn: rpyc.core.protocol.Connection):
        ok(f"connection closed: {str(conn)}")
        return

    def exposed_eval(self, cmd):
        return eval(cmd)

    exposed_gdb = gdb

    exposed_gef = gef


@register
class GefRemoteCommand(GenericCommand):
    """A better way of remoting to GDB, using rpyc"""

    _cmdline_ = "rpyc-remote"
    _aliases_ = []
    _syntax_ = f"{_cmdline_:s} --port=[PORT]"
    _example_ = f"{_cmdline_:s} --port=1234"

    def __init__(self) -> None:
        super().__init__(prefix=False)
        self["host"] = (RPYC_DEFAULT_HOST, "The interface to listen on")
        self["port"] = (RPYC_DEFAULT_PORT, "The port to listen on")
        return

    def do_invoke(self, _: List[str]) -> None:
        old_value = gef.config["gef.buffer"]
        if gef.config["gef.buffer"]:
            gef.config["gef.buffer"] = False
            warn(f"TTY buffer must be disable for {self._cmdline_} to work")

        info(f"RPYC service listening on tcp/{self['host']}:{self['port']}")
        svc = rpyc.utils.server.OneShotServer(
            RemoteDebugService,
            port=self["port"],
            protocol_config={
                "allow_public_attrs": True,
            },
        )
        svc.start()
        gef.config["gef.buffer"] = old_value
