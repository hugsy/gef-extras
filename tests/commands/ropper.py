"""
`ropper` command test module
"""


import pytest
from tests.base import RemoteGefUnitTestGeneric

from tests.utils import ARCH, ERROR_INACTIVE_SESSION_MESSAGE


class RopperCommand(RemoteGefUnitTestGeneric):
    """`ropper` command test module"""

    def setUp(self) -> None:
        try:
            import ropper  # pylint: disable=W0611
        except ImportError:
            pytest.skip("ropper not available", allow_module_level=True)
        return super().setUp()

    @pytest.mark.skipif(ARCH not in ["x86_64", "i686"], reason=f"Skipped for {ARCH}")
    def test_cmd_ropper(self):
        gdb = self._gdb
        cmd = "ropper"
        self.assertEqual(
            ERROR_INACTIVE_SESSION_MESSAGE, gdb.execute(cmd, to_string=True)
        )

        gdb.execute("start")
        cmd = 'ropper --search "pop %; pop %; ret"'
        res = gdb.execute(cmd, to_string=True) or ""
        assert res
        self.assertNotIn(": error:", res)
        self.assertTrue(len(res.splitlines()) > 2)
