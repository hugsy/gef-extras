"""
If the $PC register is on a syscall, this command will display the arguments to that syscall from the known syscall definition.
"""

__AUTHOR__ = "daniellimws"
__VERSION__ = 0.1
__LICENSE__ = "MIT"

import inspect
import pathlib
import re
from importlib.machinery import SourceFileLoader
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .. import *

CURRENT_FILE = pathlib.Path(inspect.getfile(inspect.currentframe())).resolve()
CURRENT_DIRECTORY = pathlib.Path(inspect.getfile(inspect.currentframe())).parent.resolve()
CONTEXT_PANE_INDEX = "syscall_args"
CONTEXT_PANE_DESCRIPTION = "Syscall Arguments"


@register
class IsSyscallCommand(GenericCommand):
    """Tells whether the next instruction is a system call."""
    _cmdline_ = "is-syscall"
    _syntax_ = _cmdline_

    @only_if_gdb_running
    def do_invoke(self, _: List[str]) -> None:
        ok(f"Current instruction is{' ' if is_syscall(gef.arch.pc) else ' not '}a syscall")
        return


@register
class SyscallArgsCommand(GenericCommand):
    """Gets the syscall name and arguments based on the register values in the current state."""

    _cmdline_ = "syscall-args"
    _syntax_ = f"{_cmdline_:s}"
    _example_ = f"{_cmdline_:s}"

    def __init__(self) -> None:
        super().__init__(prefix=False, complete=gdb.COMPLETE_NONE)
        self.__path: Optional[pathlib.Path] = None
        path = CURRENT_DIRECTORY / "syscall-tables"
        self["path"] = (str(path),
                        "Path to store/load the syscall tables files")
        return

    @property
    def path(self) -> pathlib.Path:
        if not self.__path:
            path = pathlib.Path(self["path"]).expanduser()
            if not path.is_dir():
                raise FileNotFoundError(
                    f"'{self.__path}' is not valid directory")
            self.__path = path
        return self.__path

    @only_if_gdb_running
    def do_invoke(self, _: List[str]) -> None:
        syscall_register = gef.arch.syscall_register
        if not syscall_register:
            err(
                f"System call register not defined for architecture {gef.arch.arch}")
            return

        color = gef.config["theme.table_heading"]
        arch = gef.arch.__class__.__name__
        syscall_table = self.__get_syscall_table(arch)

        if is_syscall(gef.arch.pc):
            # if $pc is before the `syscall` instruction is executed:
            reg_value = gef.arch.register(syscall_register)
        else:
            # otherwise, try the previous instruction (case of using `catch syscall`)
            previous_insn_addr = gdb_get_nth_previous_instruction_address(
                gef.arch.pc, 1)
            if not previous_insn_addr or not is_syscall(previous_insn_addr):
                return
            reg_value = gef.arch.register(
                f"$orig_{syscall_register.lstrip('$')}")

        if reg_value not in syscall_table:
            warn(f"There is no system call for {reg_value:#x}")
            return
        syscall_entry = syscall_table[reg_value]

        values = [gef.arch.register(param.reg)
                  for param in syscall_entry.params]
        parameters = [s.param for s in syscall_entry.params]
        registers = [s.reg for s in syscall_entry.params]

        info(f"Detected syscall {Color.colorify(syscall_entry.name, color)}")
        gef_print(f"    {syscall_entry.name}({', '.join(parameters)})")

        headers = ["Parameter", "Register", "Value"]
        param_names = [re.split(r" |\*", p)[-1] for p in parameters]
        info(Color.colorify("{:<20} {:<20} {}".format(*headers), color))
        for name, register, value in zip(param_names, registers, values):
            line = f"    {name:<20} {register:<20} {value:#x}"
            addrs = dereference_from(value)
            if len(addrs) > 1:
                line += RIGHT_ARROW + RIGHT_ARROW.join(addrs[1:])
            gef_print(line)
        return

    def __get_syscall_table(self, modname: str) -> Dict[str, Any]:
        def load_module(modname: str) -> Any:
            _fpath = self.path / f"{modname}.py"
            if not _fpath.is_file():
                raise FileNotFoundError
            _fullname = str(_fpath.absolute())
            return SourceFileLoader(modname, _fullname).load_module(None)

        _mod = load_module(modname)
        return getattr(_mod, "syscall_table")


def __syscall_args_pane_condition() -> bool:
    insn = gef_current_instruction(gef.arch.pc)
    return is_syscall(insn)


def __syscall_args_pane_content() -> None:
    gdb.execute("syscall-args")
    return


def __syscall_args_pane_title() -> str:
    return CONTEXT_PANE_DESCRIPTION

if CONTEXT_PANE_INDEX not in gef.config["context.layout"]:
    #
    # Register a callback to `syscall-args` to automatically detect when a syscall is hit
    #
    register_external_context_pane(
        CONTEXT_PANE_INDEX, __syscall_args_pane_content, pane_title_function=__syscall_args_pane_title, condition=__syscall_args_pane_condition)
