"""
A slightly better way to remote with GDB/GEF

gdb -ex 'source /path/to/gef-extras/scripts/remote.py' -ex rpyc-remote -ex quit
"""


import contextlib
import sys
from typing import TYPE_CHECKING, Any

import gdb
import rpyc

if TYPE_CHECKING:
    from . import *
    from . import gdb

__AUTHOR__ = "hugsy"
__VERSION__ = 0.2


class GefRemoteService(rpyc.Service):
    """The RPYC service for interacting with GEF"""

    def exposed_gdb(self, cmd: str) -> str:
        return gdb.execute(cmd, to_string=True) or ""

    def exposed_gef(self, cmd: str) -> Any:
        return eval(cmd)


class DisableStreamBufferContext(contextlib.ContextDecorator):
    """Because stream buffering doesn't play well with rpyc"""

    def __enter__(self) -> None:
        info("Backuping context")
        self.old_stream_buffer = gef.ui.stream_buffer
        self.old_redirect_fd = gef.ui.redirect_fd
        gef.ui.stream_buffer = sys.stdout
        gef.ui.redirect_fd = None
        return self

    def __exit__(self, _) -> bool:
        info("Restoring context")
        gef.ui.stream_buffer = self.old_stream_buffer
        gef.ui.redirect_fd = self.old_redirect_fd
        return False


@register
class GefRemoteCommand(GenericCommand):
    """A better way of remoting to GDB, using rpyc"""

    _cmdline_ = "rpyc-remote"
    _aliases_ = []
    _syntax_ = f"{_cmdline_:s}"
    _example_ = f"{_cmdline_:s}"

    def __init__(self) -> None:
        super().__init__(prefix=False)
        self["host"] = ("0.0.0.0", "The interface to listen on")
        self["port"] = (12345, "The port to listen on")
        return

    def do_invoke(self, _) -> None:
        with DisableStreamBufferContext():
            info(
                f"Listening on {self['host']}:{self['port']}, press Ctrl+C to stop")
            server = rpyc.utils.server.ThreadedServer(
                GefRemoteService, port=12345)
            try:
                server.start()
            except KeyboardInterrupt:
                info("Stopping")
                server.close()
