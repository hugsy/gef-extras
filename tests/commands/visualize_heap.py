"""
`visualize-libc-heap-chunks` command test module
"""


import pytest
from tests.base import RemoteGefUnitTestGeneric

from tests.utils import (
    ARCH,
    ERROR_INACTIVE_SESSION_MESSAGE,
    debug_target,
)


class VisualizeLibcHeapChunksCommand(RemoteGefUnitTestGeneric):
    """`visualize-libc-heap-chunks` command test module"""

    def setUp(self) -> None:
        self._target = debug_target("visualize_heap")
        return super().setUp()

    @pytest.mark.skipif(ARCH not in ["x86_64", "i686"], reason=f"Skipped for {ARCH}")
    def test_cmd_heap_view(self):
        gdb = self._gdb
        cmd = "visualize-libc-heap-chunks"
        self.assertEqual(
            ERROR_INACTIVE_SESSION_MESSAGE, gdb.execute(cmd, to_string=True)
        )

        gdb.execute("run")
        res = gdb.execute(f"{cmd}", to_string=True) or ""
        assert res

        for i in range(4):
            self.assertIn(f"0x0000000000000000    ........   Chunk[{i}]", res)
