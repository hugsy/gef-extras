"""
`syscall-args` command test module
"""

import pathlib
import tempfile

import pytest
from tests.base import RemoteGefUnitTestGeneric

from tests.utils import (
    ARCH,
    ERROR_INACTIVE_SESSION_MESSAGE,
    GEF_DEFAULT_TEMPDIR,
    debug_target,
    download_file,
    removeafter,
    removeuntil,
)


@pytest.mark.skipif(ARCH not in ("i686", "x86_64"), reason=f"Skipped for {ARCH}")
class SyscallArgsCommand(RemoteGefUnitTestGeneric):
    """`syscall-args` command test module"""

    @pytest.mark.online
    def setUp(self) -> None:
        #
        # `syscall-args.out` only work for x86_64 and i686 architectures
        #
        self.tempdirfd = tempfile.TemporaryDirectory(prefix=GEF_DEFAULT_TEMPDIR)
        self.tempdirpath = pathlib.Path(self.tempdirfd.name).absolute()
        # download some syscall tables from gef-extras
        base = "https://raw.githubusercontent.com/hugsy/gef-extras/main/scripts/syscall_args/syscall-tables"
        # todo: maybe add "PowerPC", "PowerPC64", "SPARC", "SPARC64"
        for arch in ("ARM", "ARM_OABI", "X86", "X86_64"):
            url = f"{base}/{arch}.py"
            data = download_file(url)
            if not data:
                raise Exception(f"Failed to download {arch}.py ({url})")
            fpath = self.tempdirpath / f"{arch}.py"
            with fpath.open("wb") as fd:
                fd.write(data)

        self._target = debug_target("syscall-args")
        return super().setUp()

    def tearDown(self) -> None:
        self.tempdirfd.cleanup()
        return

    def test_cmd_syscall_args(self):
        gdb = self._gdb
        cmd = "syscall-args"
        self.assertEqual(
            ERROR_INACTIVE_SESSION_MESSAGE, gdb.execute(cmd, to_string=True)
        )

        gdb.execute(f"gef config syscall-args.path {self.tempdirpath.absolute()}")

        res = gdb.execute("catch syscall openat", to_string=True) or ""
        assert res
        self.assertIn("(syscall 'openat' ", res)

        gdb.execute("run")

        res = gdb.execute("syscall-args", to_string=True) or ""
        self.assertIn("Detected syscall open", res)


@pytest.mark.skipif(ARCH not in ("i686", "x86_64"), reason=f"Skipped for {ARCH}")
class IsSyscallCommand(RemoteGefUnitTestGeneric):
    """`is-syscall` command test module"""

    def setUp(self) -> None:
        self._target = debug_target("syscall-args")
        self.syscall_location = None
        return super().setUp()

    def test_cmd_is_syscall(self):
        gdb = self._gdb
        cmd = "is-syscall"
        self.assertEqual(
            ERROR_INACTIVE_SESSION_MESSAGE, gdb.execute(cmd, to_string=True)
        )

        res = gdb.execute("disassemble openfile", to_string=True) or ""
        start_str = "Dump of assembler code for function main:\n"
        end_str = "End of assembler dump."
        disass_code = removeafter(end_str, res)
        disass_code = removeuntil(start_str, disass_code)
        lines = disass_code.splitlines()
        for line in lines:
            parts = [x.strip() for x in line.split(maxsplit=3)]
            self.assertGreaterEqual(len(parts), 3)
            if ARCH == "x86_64" and parts[2] == "syscall":
                self.syscall_location = parts[1].lstrip("<").rstrip(">:")
                break
            if ARCH == "i686" and parts[2] == "int" and parts[3] == "0x80":
                self.syscall_location = parts[1].lstrip("<").rstrip(">:")
                break
        assert self.syscall_location

        gdb.execute(f"break *(openfile{self.syscall_location})")
        gdb.execute("run")

        res = gdb.execute("is-syscall", to_string=True) or ""
        assert res
        self.assertIn("Current instruction is a syscall", res)
