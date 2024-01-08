"""
`set-permission` command test module
"""

import re

import pytest
from tests.base import RemoteGefUnitTestGeneric

from tests.utils import ARCH, debug_target, ERROR_INACTIVE_SESSION_MESSAGE


@pytest.mark.skipif(
    ARCH not in ("i686", "x86_64", "armv7l", "aarch64"), reason=f"Skipped for {ARCH}"
)
class SetPermissionCommand(RemoteGefUnitTestGeneric):
    """`set-permission` command test module"""

    def setUp(self) -> None:
        try:
            import keystone  # pylint: disable=W0611
            import unicorn  # pylint: disable=W0611
        except ImportError:
            pytest.skip("keystone-engine not available", allow_module_level=True)

        self._target = debug_target("set-permission")
        return super().setUp()

    def test_cmd_set_permission_basic(self):
        gdb = self._gdb
        cmd = "set-permission"

        self.assertEqual(
            ERROR_INACTIVE_SESSION_MESSAGE, gdb.execute(cmd, to_string=True)
        )

        # get the initial stack address
        gdb.execute("start")
        res = gdb.execute("vmmap", to_string=True) or ""
        assert res
        stack_line = [l.strip() for l in res.splitlines() if "[stack]" in l][0]
        stack_address = int(stack_line.split()[0], 0)

        # compare the new permissions
        gdb.execute(f"set-permission {stack_address:#x}")
        res = gdb.execute(f"xinfo {stack_address:#x}", to_string=True) or ""
        assert res
        line = [l.strip() for l in res.splitlines() if l.startswith("Permissions: ")][0]
        self.assertEqual(line.split()[1], "rwx")

        res = gdb.execute("set-permission 0x1338000", to_string=True) or ""
        assert res
        self.assertIn("Unmapped address", res)

    def test_cmd_set_permission_no_clobber(self):
        """Make sure set-permission command doesn't clobber any register"""
        gdb = self._gdb
        gef = self._gef

        gdb.execute("start")

        #
        # Collect registers pre-execution
        #
        before_register_state = [
            (name, gef.arch.register(name)) for name in gef.arch.registers
        ]
        res = gdb.execute("set-permission $sp", to_string=True) or ""

        #
        # Collect registers post-execution
        #
        assert res
        after_register_state = [
            (name, gef.arch.register(name)) for name in gef.arch.registers
        ]

        #
        # Compare their values
        #
        assert before_register_state == after_register_state
