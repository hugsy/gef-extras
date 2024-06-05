"""
capstone-disassemble command test module
"""

import pytest
from tests.base import RemoteGefUnitTestGeneric

from tests.utils import (
    ARCH,
    ERROR_INACTIVE_SESSION_MESSAGE,
    removeuntil,
)


@pytest.mark.skipif(
    ARCH in ("mips64el", "ppc64le", "riscv64"), reason=f"Skipped for {ARCH}"
)
class CapstoneDisassembleCommand(RemoteGefUnitTestGeneric):
    """`capstone-disassemble` command test module"""

    def setUp(self) -> None:
        try:
            import capstone  # pylint: disable=W0611
        except ImportError:
            pytest.skip("capstone-engine not available", allow_module_level=True)
        return super().setUp()

    def test_cmd_capstone_disassemble(self):
        gdb = self._gdb
        cmd = "capstone-disassemble"

        self.assertEqual(
            ERROR_INACTIVE_SESSION_MESSAGE, gdb.execute(cmd, to_string=True)
        )

        gdb.execute("start")
        res = gdb.execute("capstone-disassemble", to_string=True) or ""
        assert res

        cmd = "capstone-disassemble --show-opcodes"
        res = gdb.execute(cmd, to_string=True) or ""
        assert res

        cmd = "capstone-disassemble --show-opcodes --length 5 $pc"
        res = gdb.execute(cmd, to_string=True) or ""
        assert res

        lines = res.splitlines()
        self.assertGreaterEqual(len(lines), 5)

        # jump to the output buffer
        res = removeuntil("→  ", res, included=True)
        addr, opcode, symbol, *_ = [x.strip() for x in lines[2].strip().split()]

        # match the correct output format: <addr> <opcode> [<symbol>] mnemonic [operands,]
        # gef➤  cs --show-opcodes --length 5 $pc
        # →    0xaaaaaaaaa840 80000090    <main+20>        adrp   x0, #0xaaaaaaaba000
        #      0xaaaaaaaaa844 00f047f9    <main+24>        ldr    x0, [x0, #0xfe0]
        #      0xaaaaaaaaa848 010040f9    <main+28>        ldr    x1, [x0]
        #      0xaaaaaaaaa84c e11f00f9    <main+32>        str    x1, [sp, #0x38]
        #      0xaaaaaaaaa850 010080d2    <main+36>        movz   x1, #0

        self.assertTrue(addr.startswith("0x"))
        self.assertTrue(int(addr, 16))
        self.assertTrue(int(opcode, 16))
        self.assertTrue(symbol.startswith("<") and symbol.endswith(">"))

        cmd = "cs --show-opcodes &__libc_start_main"
        res = gdb.execute(cmd, to_string=True) or ""
        assert res
        self.assertGreater(len(res.splitlines()), 1)
