"""
unicorn-emulate command test module
"""


import pytest
from tests.base import RemoteGefUnitTestGeneric

from tests.utils import ARCH, ERROR_INACTIVE_SESSION_MESSAGE, debug_target


@pytest.mark.skipif(
    ARCH not in ("i686", "x86_64", "armv7l", "aarch64"), reason=f"Skipped for {ARCH}"
)
class UnicornEmulateCommand(RemoteGefUnitTestGeneric):
    """`unicorn-emulate` command test module"""

    def setUp(self) -> None:
        try:
            import unicorn  # pylint: disable=W0611
        except ImportError:
            pytest.skip("unicorn-engine not available", allow_module_level=True)

        self._target = debug_target("unicorn")
        return super().setUp()

    @pytest.mark.skipif(ARCH not in ["x86_64"], reason=f"Skipped for {ARCH}")
    def test_cmd_unicorn_emulate(self):
        gdb = self._gdb
        nb_insn = 4

        cmd = f"emu {nb_insn}"
        self.assertEqual(
            ERROR_INACTIVE_SESSION_MESSAGE, gdb.execute(cmd, to_string=True)
        )

        res = gdb.execute(cmd, to_string=True) or ""
        assert res

        gdb.execute("break function1")
        gdb.execute("run")

        start_marker = "= Starting emulation ="
        end_marker = "Final registers"
        res = gdb.execute(cmd, to_string=True) or ""
        assert res

        self.assertNotIn("Emulation failed", res)
        self.assertIn(start_marker, res)
        self.assertIn(end_marker, res)

        insn_executed = len(
            res[res.find(start_marker) : res.find(end_marker)].splitlines()[1:-1]
        )
        self.assertGreaterEqual(insn_executed, nb_insn)
