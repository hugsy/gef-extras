"""
Print a list of symbols in the GOT and the files that provide them.

Errors will be printed if a symbol is provided by multiple shared
libraries, or if a symbol points to a library that doesn't export
it.
"""

__AUTHOR__ = "gordonmessmer"
__VERSION__ = 1.0
__LICENSE__ = "MIT"

import collections
import pathlib
from typing import TYPE_CHECKING, Dict, List, Tuple

import gdb

if TYPE_CHECKING:
    from . import *
    from . import gdb

@register
class GotAuditCommand(GotCommand, GenericCommand):
    """Display current status of the got inside the process with paths providing functions."""

    _cmdline_ = "got-audit"
    _syntax_ = f"{_cmdline_} [FUNCTION_NAME ...] "
    _example_ = "got-audit read printf exit"
    _symbols_: Dict[str, List[str]] = collections.defaultdict(list)
    _paths_: Dict[str, List[str]] = collections.defaultdict(list)
    _expected_dups_ = ['__cxa_finalize']

    def get_symbols_from_path(self, elf_file):
        nm = gef.session.constants["nm"]
        # retrieve symbols using nm
        lines = gef_execute_external([nm, "-D", elf_file], as_list=True)
        for line in lines:
            words = line.split()
            # Record the symbol if it is in the text section or
            # an indirect function or weak symbol
            if len(words) == 3 and words[-2] in ('T', 'i', 'I', 'v', 'V', 'w', 'W'):
                sym = words[-1].split('@')[0]
                if elf_file not in self._symbols_[sym]:
                    self._symbols_[sym].append(elf_file)
                self._paths_[elf_file].append(sym)

    @only_if_gdb_running
    def do_invoke(self, argv: List[str]) -> None:
        # Build a list of the symbols provided by each path, and
        # a list of paths that provide each symbol.
        for section in gef.memory.maps:
            if (section.path not in self._paths_
                and pathlib.Path(section.path).is_file()
                and section.permission & Permission.EXECUTE):
                self.get_symbols_from_path(section.path)
        return super().do_invoke(argv)

    def build_line(self, name: str, color: str, address_val: int, got_address: int) -> str:
        line = Color.colorify(f"{name}", color)
        found = 0
        for section in gef.memory.maps:
            if not section.contains(got_address):
                continue
            line += f" : {section.path}"
            found = 1
            short_name = name.split('@')[0]
            if (len(self._symbols_[short_name]) > 1
                and short_name not in self._expected_dups_):
                line += f" :: ERROR {short_name} found in multiple paths ({str(self._symbols_[short_name])})"
            if (section.path != "[vdso]"
                and short_name not in self._paths_[section.path]):
                line += f" :: ERROR {short_name} not exported by {section.path}"
            break
        if not found:
            line += " : no mapping found"
        return line
