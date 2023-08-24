"""
ARM through the Black Magic Probe support for GEF

To use, source this file *after* gef

Author: Grazfather
"""

from typing import Optional

import gdb


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
    """GDB `target remote` command on steroids. This command will use the remote procfs to create
    a local copy of the execution environment, including the target binary and its libraries
    in the local temporary directory (the value by default is in `gef.config.tempdir`). Additionally, it
    will fetch all the /proc/PID/maps and loads all its information. If procfs is not available remotely, the command
    will likely fail. You can however still use the limited command provided by GDB `target remote`."""

    _cmdline_ = "gef-bmp-remote"
    _syntax_  = f"{_cmdline_} [OPTIONS] TARGET"
    _example_ = [f"{_cmdline_} --file /path/to/binary.elf --target 1 /dev/ttyUSB1",
                 f"{_cmdline_} --file /path/to/binary.elf --target 1 --power /dev/ttyUSB1",
                 f"{_cmdline_} --scan /dev/ttyUSB1",
                 f"{_cmdline_} --tty /dev/ttyXYZ --file /path/to/binary.elf --target 1"]

    def __init__(self) -> None:
        super().__init__(prefix=False)
        return

    @parse_arguments({"tty": ""}, {"--file": "", "--target": "", "--power": False, "--scan": False})
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        if gef.session.remote is not None:
            err("You're already in a remote session. Close it first before opening a new one...")
            return

        # argument check
        args : argparse.Namespace = kwargs["arguments"]
        if not args.tty:
            err("Missing parameters")
            return

        if args.scan:
            with DisableContextOutputContext():
                cmd = f"target extended-remote {args.tty}"
                dbg(f"[remote] Executing '{cmd}'")
                gdb.execute(cmd)
                cmd = "monitor swdp_scan"
                dbg(f"[remote] Executing '{cmd}'")
                gdb.execute(cmd)
                gdb.execute("disconnect")
            return

        # Try to establish the remote session, throw on error
        # Set `.remote_initializing` to True here - `GefRemoteSessionManager` invokes code which
        # calls `is_remote_debug` which checks if `remote_initializing` is True or `.remote` is None
        # This prevents some spurious errors being thrown during startup
        gef.session.remote_initializing = True
        session = GefBMPRemoteSessionManager(args.tty, args.file, args.target, args.power)

        dbg(f"[remote] initializing remote session with {session.target} under {session.root}")
        if not session.connect() or not session.setup():
            gef.session.remote = None
            gef.session.remote_initializing = False
            raise EnvironmentError("Failed to setup remote target")

        gef.session.remote_initializing = False
        gef.session.remote = session
        reset_all_caches()
        gdb.execute("context")
        return


class GefBMPRemoteSessionManager(GefRemoteSessionManager):
    """Class for managing remote sessions with GEF. It will create a temporary environment
    designed to clone the remote one."""
    def __init__(self, tty: str="", file: str="", target: int=1, power: bool=False) -> None:
        self.__tty = tty
        self.__file = file
        self.__target = target
        self.__power = power
        self.__local_root_fd = tempfile.TemporaryDirectory()
        self.__local_root_path = pathlib.Path(self.__local_root_fd.name)

    def __str__(self) -> str:
        return f"BMPRemoteSessionManager(tty='{self.__tty}', file='{self.__file}', target={self.__target})"

    @property
    def root(self) -> pathlib.Path:
        return self.__local_root_path.absolute()

    @property
    def target(self) -> str:
        return f"{self.__tty} target {self.__target}"

    def sync(self, src: str, dst: Optional[str] = None) -> bool:
        pass

    @property
    def file(self) -> pathlib.Path:
        return pathlib.Path(self.__file).expanduser()

    @property
    def maps(self) -> pathlib.Path:
        if not self._maps:
            self._maps = self.root / f"proc/{self.pid}/maps"
        return self._maps

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

        # then attempt to connect
        try:
            with DisableContextOutputContext():
                cmd = f"file {self.__file}"
                dbg(f"[remote] Executing '{cmd}'")
                gdb.execute(cmd)
                cmd = f"target extended-remote {self.__tty}"
                dbg(f"[remote] Executing '{cmd}'")
                gdb.execute(cmd)
                if self.__power:
                    cmd = f"monitor tpwr enable"
                    dbg(f"[remote] Executing '{cmd}'")
                    gdb.execute(cmd)
                cmd = f"attach {self.__target or 1}"
                dbg(f"[remote] Executing '{cmd}'")
                gdb.execute(cmd)
            return True
        except Exception as e:
            err(f"Failed to connect to {self.target}: {e}")

        # a failure will trigger the cleanup, deleting our hook anyway
        return False

    def setup(self) -> bool:
        # setup remote adequately depending on remote or qemu mode
        dbg(f"Setting up as remote session")

        # refresh gef to consider the binary
        reset_all_caches()
        gef.binary = Elf(self.file)
        reset_architecture("ARMBlackMagicProbe")
        return True

    def remote_objfile_event_handler(self, evt: "gdb.NewObjFileEvent") -> None:
        dbg(f"[remote] in remote_objfile_handler({evt.new_objfile.filename if evt else 'None'}))")
        if not evt or not evt.new_objfile.filename:
            return
        if not evt.new_objfile.filename.startswith("target:") and not evt.new_objfile.filename.startswith("/"):
            warn(f"[remote] skipping '{evt.new_objfile.filename}'")
            return
        if evt.new_objfile.filename.startswith("target:"):
            src: str = evt.new_objfile.filename[len("target:"):]
            if not self.sync(src):
                raise FileNotFoundError(f"Failed to sync '{src}'")
        return
