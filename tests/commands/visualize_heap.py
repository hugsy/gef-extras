"""
`visualize-libc-heap-chunks` command test module
"""


import pytest

from tests.utils import (ARCH, GefUnitTestGeneric, _target, gdb_run_cmd,
                         gdb_run_silent_cmd)


class VisualizeLibcHeapChunksCommand(GefUnitTestGeneric):
    """`visualize-libc-heap-chunks` command test module"""

    @pytest.mark.skipif(ARCH not in ["x86_64", "i686"], reason=f"Skipped for {ARCH}")
    def test_cmd_heap_view(self):
        target = _target("visualize_heap")
        cmd = "visualize-libc-heap-chunks"
        self.assertFailIfInactiveSession(
            gdb_run_cmd(cmd, target=target, after=["gef"]))

        res = gdb_run_silent_cmd(f"{cmd}", target=target)
        self.assertNoException(res)

        for i in range(4):
            self.assertIn(
                f"0x0000000000000000    ........   Chunk[{i}]", res)
