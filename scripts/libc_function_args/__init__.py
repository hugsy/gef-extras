"""
Conditional pane that will be shown only when a call is hit: it will try to collect the
libc parameter names of the function, and display them
"""

__AUTHOR__ = "daniellimws"
__VERSION__ = 0.1
__LICENSE__ = "MIT"

import inspect
import json
import pathlib
import re
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from .. import *


GLIBC_FUNCTION_ARGS_CURRENT_FILE = pathlib.Path(inspect.getfile(inspect.currentframe())).resolve()
GLIBC_FUNCTION_ARGS_CURRENT_DIRECTORY = pathlib.Path(inspect.getfile(inspect.currentframe())).parent.resolve()
GLIBC_FUNCTION_ARGS_CONTEXT_PANE_INDEX = "libc_function_args"
GLIBC_FUNCTION_ARGS_CONTEXT_PANE_DESCRIPTION = "Glibc Function Arguments"


class GlibcFunctionArguments:
    #
    # This table will be populate lazily
    #
    argument_table: Dict[str, Dict[str, Dict[str, str]]] = {}

    @staticmethod
    def load_libc_args() -> bool:
        """Load the LIBC function arguments. Returns `True` on success, `False` or an Exception otherwise."""

        # load libc function arguments' definitions
        path = GLIBC_FUNCTION_ARGS_CURRENT_DIRECTORY
        if not path.exists():
            raise RuntimeError(
                "Config `context.libc_args_path` set but it's not a directory"
            )

        _arch_mode = f"{gef.arch.arch.lower()}_{gef.arch.mode}"
        _libc_args_file = path / f"tables/{_arch_mode}.json"

        if not _libc_args_file.exists():
            # Try to generate the json table files
            from .tables.generator import generate_all_json_files

            if not generate_all_json_files():
                raise RuntimeError("Failed to generate JSON table files")

        # current arch and mode already loaded
        if _arch_mode in GlibcFunctionArguments.argument_table:
            return True

        GlibcFunctionArguments.argument_table[_arch_mode] = {}
        try:
            with _libc_args_file.open() as _libc_args:
                GlibcFunctionArguments.argument_table[_arch_mode] = json.load(
                    _libc_args
                )
            return True
        except FileNotFoundError:
            warn(
                f"Config context.libc_args is set but definition cannot be loaded: file {_libc_args_file} not found"
            )
        except json.decoder.JSONDecodeError as e:
            warn(
                f"Config context.libc_args is set but definition cannot be loaded from file {_libc_args_file}: {e}"
            )
        GlibcFunctionArguments.argument_table[_arch_mode] = {}
        return False

    @staticmethod
    def only_if_call() -> bool:
        insn = gef_current_instruction(gef.arch.pc)
        return gef.arch.is_call(insn)

    @staticmethod
    def pane_title() -> str:
        return GLIBC_FUNCTION_ARGS_CONTEXT_PANE_DESCRIPTION

    @staticmethod
    def pane_content() -> None:
        function_name = GlibcFunctionArguments.extract_called_function_name()

        if not GlibcFunctionArguments.argument_table:
            #
            # The table has been populated, do it now
            #
            GlibcFunctionArguments.load_libc_args()

        nb_argument = None
        _arch_mode = f"{gef.arch.arch.lower()}_{gef.arch.mode}"
        function_basename = None
        if not function_name.endswith("@plt") or function_name.endswith("@got.plt"):
            return
        function_basename = function_name.split("@")[0]
        nb_argument = len(
            GlibcFunctionArguments.argument_table[_arch_mode][function_basename]
        )

        args = []
        for i in range(nb_argument):
            _key, _values = gef.arch.get_ith_parameter(i, in_func=False)
            if not _values:
                args.append(f"{_key}: <invalid>")
                continue
            _values = RIGHT_ARROW.join(dereference_from(_values))
            args.append(
                f"\t{_key} = {_values} /* {GlibcFunctionArguments.argument_table[_arch_mode][function_basename][_key]}) */"
            )

        gef_print(f"{function_name} (\n", "\n".join(args), "\n)")
        return

    @staticmethod
    def extract_called_function_name() -> str:
        pc = gef.arch.pc
        insn = gef_current_instruction(pc)
        if not gef.arch.is_call(insn):
            raise RuntimeError("Not a call")

        size2type = {
            1: "BYTE",
            2: "WORD",
            4: "DWORD",
            8: "QWORD",
        }

        if insn.operands[-1].startswith(size2type[gef.arch.ptrsize] + " PTR"):
            function_name = "*" + insn.operands[-1].split()[-1]
        elif "$" + insn.operands[0] in gef.arch.all_registers:
            function_name = f"*{gef.arch.register('$' + insn.operands[0]):#x}"
        else:
            ops = " ".join(insn.operands)
            if "<" in ops and ">" in ops:
                function_name = re.sub(r".*<([^\(> ]*).*", r"\1", ops)
            else:
                function_name = re.sub(r".*(0x[a-fA-F0-9]*).*", r"\1", ops)

        return function_name

if GLIBC_FUNCTION_ARGS_CONTEXT_PANE_INDEX not in gef.config["context.layout"]:
    #
    # Register the context pane
    #
    register_external_context_pane(
        GLIBC_FUNCTION_ARGS_CONTEXT_PANE_INDEX,
        GlibcFunctionArguments.pane_content,
        pane_title_function=GlibcFunctionArguments.pane_title,
        condition=GlibcFunctionArguments.only_if_call,
    )
