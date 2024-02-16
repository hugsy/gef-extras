"""
ARM through OpenOCD support for GEF

To use, source this file *after* gef

Author: Grazfather
"""

from typing import Optional
from pathlib import Path

import gdb


class ARMOpenOCD(ARM):
    arch = "ARMOpenOCD"
    aliases = ("ARMOpenOCD",)
    all_registers = ("$r0", "$r1", "$r2", "$r3", "$r4", "$r5", "$r6",
                     "$r7", "$r8", "$r9", "$r10", "$r11", "$r12", "$sp",
                     "$lr", "$pc", "$xPSR")
    flag_register = "$xPSR"
    @staticmethod
    def supports_gdb_arch(arch: str) -> Optional[bool]:
        if "arm" in arch and arch.endswith("-m"):
            return True
        return None

    @staticmethod
    def maps():
        yield from GefMemoryManager.parse_info_mem()


@register
class OpenOCDRemoteCommand(GenericCommand):
    """This command is intended to replace `gef-remote` to connect to an
    OpenOCD-hosted gdbserver. It uses a special session manager that knows how
    to connect and manage the server."""

    _cmdline_ = "gef-openocd-remote"
    _syntax_  = f"{_cmdline_} [OPTIONS] HOST PORT"
    _example_ = [f"{_cmdline_} --file /path/to/binary.elf localhost 3333",
                 f"{_cmdline_} localhost 3333"]

    def __init__(self) -> None:
        super().__init__(prefix=False)
        return

    @parse_arguments({"host": "", "port": 0}, {"--file": ""})
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        if gef.session.remote is not None:
            err("You're already in a remote session. Close it first before opening a new one...")
            return

        # argument check
        args: argparse.Namespace = kwargs["arguments"]
        if not args.host or not args.port:
            err("Missing parameters")
            return

        # Try to establish the remote session, throw on error
        # Set `.remote_initializing` to True here - `GefRemoteSessionManager` invokes code which
        # calls `is_remote_debug` which checks if `remote_initializing` is True or `.remote` is None
        # This prevents some spurious errors being thrown during startup
        gef.session.remote_initializing = True
        session = GefOpenOCDRemoteSessionManager(args.host, args.port, args.file)

        dbg(f"[remote] initializing remote session with {session.target} under {session.root}")

        # Connect can return false if it wants us to disconnect
        if not session.connect():
            gef.session.remote = None
            gef.session.remote_initializing = False
            return
        if not session.setup():
            gef.session.remote = None
            gef.session.remote_initializing = False
            raise EnvironmentError("Failed to setup remote target")

        gef.session.remote_initializing = False
        gef.session.remote = session
        reset_all_caches()
        gdb.execute("context")
        return


# We CANNOT use the normal session manager because it assumes we have a PID
class GefOpenOCDRemoteSessionManager(GefRemoteSessionManager):
    """This subclass of GefRemoteSessionManager specially handles the
    intricacies involved with connecting to an OpenOCD-hosted GDB server.
    Specifically, it does not have the concept of PIDs which we need to work
    around."""
    def __init__(self, host: str, port: str, file: str="") -> None:
        self.__host = host
        self.__port = port
        self.__file = file
        self.__local_root_fd = tempfile.TemporaryDirectory()
        self.__local_root_path = pathlib.Path(self.__local_root_fd.name)

    def __str__(self) -> str:
        return f"OpenOCDRemoteSessionManager(='{self.__tty}', file='{self.__file}', attach={self.__attach})"

    def close(self) -> None:
        self.__local_root_fd.cleanup()
        try:
            gef_on_new_unhook(self.remote_objfile_event_handler)
            gef_on_new_hook(new_objfile_handler)
        except Exception as e:
            warn(f"Exception while restoring local context: {str(e)}")
        return

    @property
    def target(self) -> str:
        return f"{self.__host}:{self.__port}"

    @property
    def root(self) -> Path:
        return self.__local_root_path.absolute()

    def sync(self, src: str, dst: Optional[str] = None) -> bool:
        # We cannot sync from this target
        return None

    @property
    def file(self) -> Optional[Path]:
        if self.__file:
            return Path(self.__file).expanduser()
        return None

    def connect(self) -> bool:
        """Connect to remote target. If in extended mode, also attach to the given PID."""
        # before anything, register our new hook to download files from the remote target
        dbg(f"[remote] Installing new objfile handlers")
        try:
            gef_on_new_unhook(new_objfile_handler)
        except SystemError:
            # the default objfile handler might already have been removed, ignore failure
            pass

        gef_on_new_hook(self.remote_objfile_event_handler)

        # Connect
        with DisableContextOutputContext():
            self._gdb_execute(f"target extended-remote {self.target}")

        try:
            with DisableContextOutputContext():
                if self.file:
                    self._gdb_execute(f"file '{self.file}'")
        except Exception as e:
            err(f"Failed to connect to {self.target}: {e}")
            # a failure will trigger the cleanup, deleting our hook
            return False

        return True

    def setup(self) -> bool:
        dbg(f"Setting up as remote session")

        # refresh gef to consider the binary
        reset_all_caches()
        if self.file:
            gef.binary = Elf(self.file)
        # We'd like to set this earlier, but we can't because of this bug
        # https://sourceware.org/bugzilla/show_bug.cgi?id=31303
        reset_architecture("ARMOpenOCD")
        return True

    def _gdb_execute(self, cmd):
        dbg(f"[remote] Executing '{cmd}'")
        gdb.execute(cmd)
