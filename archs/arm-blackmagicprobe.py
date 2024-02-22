"""
ARM through the Black Magic Probe support for GEF

To use, source this file *after* gef

Author: Grazfather
"""

from typing import Optional

import gdb

assert 'gef' in globals(), "This file must be source after gef.py"


class ARMBlackMagicProbe(ARM):
    arch = "ARMBlackMagicProbe"
    aliases = ("ARMBlackMagicProbe",)
    all_registers = ("$r0", "$r1", "$r2", "$r3", "$r4", "$r5", "$r6",
                     "$r7", "$r8", "$r9", "$r10", "$r11", "$r12", "$sp",
                     "$lr", "$pc", "$xpsr")
    flag_register = "$xpsr"
    @staticmethod
    def supports_gdb_arch(arch: str) -> Optional[bool]:
        if "arm" in arch and arch.endswith("-m"):
            return True
        return None

    @staticmethod
    def maps():
        yield from GefMemoryManager.parse_info_mem()


@register
class BMPRemoteCommand(GenericCommand):
    """This command is intended to replace `gef-remote` to connect to a
    BlackMagicProbe. It uses a special session manager that knows how to
    connect and manage the server running over a tty."""

    _cmdline_ = "gef-bmp-remote"
    _syntax_  = f"{_cmdline_} [OPTIONS] TTY"
    _example_ = [f"{_cmdline_} --scan /dev/ttyUSB1",
                 f"{_cmdline_} --scan /dev/ttyUSB1 --power",
                 f"{_cmdline_} --scan /dev/ttyUSB1 --power --keep-power",
                 f"{_cmdline_} --file /path/to/binary.elf --attach 1 /dev/ttyUSB1",
                 f"{_cmdline_} --file /path/to/binary.elf --attach 1 --power /dev/ttyUSB1"]

    def __init__(self) -> None:
        super().__init__(prefix=False)
        return

    @parse_arguments({"tty": ""}, {"--file": "", "--attach": "", "--power": False,
                                   "--keep-power": False, "--scan": False})
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        if gef.session.remote is not None:
            err("You're already in a remote session. Close it first before opening a new one...")
            return

        # argument check
        args: argparse.Namespace = kwargs["arguments"]
        if not args.tty:
            err("Missing parameters")
            return

        if not args.scan and not args.attach:
            err("Must provide target to attach to if not scanning")
            return

        # Try to establish the remote session, throw on error
        # Set `.remote_initializing` to True here - `GefRemoteSessionManager` invokes code which
        # calls `is_remote_debug` which checks if `remote_initializing` is True or `.remote` is None
        # This prevents some spurious errors being thrown during startup
        gef.session.remote_initializing = True
        session = GefBMPRemoteSessionManager(args.tty, args.file, args.attach, args.scan, args.power)

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


class GefBMPRemoteSessionManager(GefRemoteSessionManager):
    """This subclass of GefRemoteSessionManager specially handles the
    intricacies involved with connecting to a BlackMagicProbe."""
    def __init__(self, tty: str="", file: str="", attach: int=1,
                 scan: bool=False, power: bool=False, keep_power: bool=False) -> None:
        self.__tty = tty
        self.__file = file
        self.__attach = attach
        self.__scan = scan
        self.__power = power
        self.__keep_power = keep_power
        self.__local_root_fd = tempfile.TemporaryDirectory()
        self.__local_root_path = pathlib.Path(self.__local_root_fd.name)

    def __str__(self) -> str:
        return f"BMPRemoteSessionManager(tty='{self.__tty}', file='{self.__file}', attach={self.__attach})"

    def close(self) -> None:
        self.__local_root_fd.cleanup()
        try:
            gef_on_new_unhook(self.remote_objfile_event_handler)
            gef_on_new_hook(new_objfile_handler)
            if self.__power and not self.__keep_power:
                self._power_off()
        except Exception as e:
            warn(f"Exception while restoring local context: {str(e)}")
        return

    @property
    def root(self) -> pathlib.Path:
        return self.__local_root_path.absolute()

    @property
    def target(self) -> str:
        return f"{self.__tty} (attach {self.__attach})"

    def sync(self, src: str, dst: Optional[str] = None) -> bool:
        # We cannot sync from this target
        return None

    @property
    def file(self) -> Optional[pathlib.Path]:
        if self.__file:
            return pathlib.Path(self.__file).expanduser()
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
            self._gdb_execute(f"target extended-remote {self.__tty}")

        # Optionally enable target-powering
        if self.__power:
            self._power_on()

        # We must always scan, but with --scan we are done here
        self._gdb_execute("monitor swdp_scan")
        if self.__scan:
            self._gdb_execute("disconnect")

            # Returning false cleans up the session
            return False

        try:
            with DisableContextOutputContext():
                if self.file:
                    self._gdb_execute(f"file {self.file}")
                self._gdb_execute(f"attach {self.__attach or 1}")
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
        reset_architecture("ARMBlackMagicProbe")
        return True

    def _power_off(self):
        self._gdb_execute("monitor tpwr disable")

    def _power_on(self):
        self._gdb_execute("monitor tpwr enable")

    def _gdb_execute(self, cmd):
        dbg(f"[remote] Executing '{cmd}'")
        gdb.execute(cmd)
