"""
Collection of functions and commands to manipulate kernel symbols
"""

__AUTHOR__ = "hugsy"
__VERSION__ = 0.1
__LICENSE__ = "MIT"

import argparse
from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    from .. import *  # this will allow linting for GEF and GDB


@register
class SolveKernelSymbolCommand(GenericCommand):
    """Solve kernel symbols from kallsyms table."""

    _cmdline_ = "ksymaddr"
    _syntax_ = f"{_cmdline_} SymbolToSearch"
    _example_ = f"{_cmdline_} prepare_creds"

    @parse_arguments({"symbol": ""}, {})
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        def hex_to_int(num):
            try:
                return int(num, 16)
            except ValueError:
                return 0

        args: argparse.Namespace = kwargs["arguments"]
        if not args.symbol:
            self.usage()
            return
        sym = args.symbol
        with open("/proc/kallsyms", "r") as f:
            syms = [line.strip().split(" ", 2) for line in f]
        matches = [
            (hex_to_int(addr), sym_t, " ".join(name.split()))
            for addr, sym_t, name in syms
            if sym in name
        ]
        for addr, sym_t, name in matches:
            if sym == name.split()[0]:
                ok(f"Found matching symbol for '{name}' at {addr:#x} (type={sym_t})")
            else:
                warn(
                    f"Found partial match for '{sym}' at {addr:#x} (type={sym_t}): {name}"
                )
        if not matches:
            err(f"No match for '{sym}'")
        elif matches[0][0] == 0:
            err(
                "Check that you have the correct permissions to view kernel symbol addresses"
            )
        return
