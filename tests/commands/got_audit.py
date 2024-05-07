"""
`got-audit` command test module
"""

import pytest

from tests.base import RemoteGefUnitTestGeneric

from tests.utils import (
    ARCH,
    ERROR_INACTIVE_SESSION_MESSAGE,
    debug_target,
)


@pytest.mark.skipif(ARCH in ("ppc64le",), reason=f"Skipped for {ARCH}")
class GotAuditCommand(RemoteGefUnitTestGeneric):
    """`got-audit` command test module"""

    def setUp(self) -> None:
        self._target = debug_target("visualize_heap")
        return super().setUp()


    def test_cmd_got_audit(self):
        gdb = self._gdb

        self.assertEqual(ERROR_INACTIVE_SESSION_MESSAGE,gdb.execute("got-audit", to_string=True))

        gdb.execute("run")
        res = gdb.execute("got-audit", to_string=True)
        self.assertIn("malloc", res)
        self.assertIn("puts", res)
        self.assertIn("/libc", res)

        res = gdb.execute("got-audit malloc", to_string=True)
        self.assertIn("malloc", res)
        self.assertNotIn("puts", res)
