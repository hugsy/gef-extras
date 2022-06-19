__AUTHOR__ = "hugsy"
__VERSION__ = 0.1

__AUTHOR__ = "your_name"
__VERSION__ = 0.1
__LICENSE__ = "MIT"

import collections
import pathlib
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from . import *
    from . import gdb


PLUGIN_FTRACE_DEFAULT_OUTPUT = "/dev/stderr"


class FtraceEnterBreakpoint(gdb.Breakpoint):
    def __init__(self, location: str, nb_args: int):
        super().__init__(location, gdb.BP_BREAKPOINT, internal=True)
        self.silent: bool = True
        self.nb_args: int = nb_args
        self.retbp: Optional[FtraceExitBreakpoint] = None
        return

    def stop(self):
        regs = collections.OrderedDict()
        for idx, r in enumerate(gef.arch.function_parameters):
            if idx >= self.nb_args:
                break
            regs[r] = gef.arch.register(r)
            self.retbp = FtraceExitBreakpoint(
                location=self.location, regs=regs)
        return False


class FtraceExitBreakpoint(gdb.FinishBreakpoint):
    def __init__(self, *args, **kwargs):
        super(FtraceExitBreakpoint, self).__init__(
            gdb.newest_frame(), internal=True)
        self.silent = True
        self.args = kwargs
        return

    def stop(self):
        if self.return_value:
            retval = format_address(abs(self.return_value))
        else:
            retval = gef.arch.register(gef.arch.return_register)

        output = pathlib.Path(gef.config["ftrace.output"])
        use_color = PLUGIN_FTRACE_DEFAULT_OUTPUT == gef.config["ftrace.output"]

        with output.open("w") as fd:
            if use_color:
                fd.write("{:s}() = {} {{\n".format(
                    Color.yellowify(self.args["location"]), retval))
            else:
                fd.write("{:s}() = {} {{\n".format(
                    self.args["location"], retval))
            for reg in self.args["regs"].keys():
                regval = self.args["regs"][reg]
                fd.write("\t{} {} {}\n".format(reg, RIGHT_ARROW,
                         RIGHT_ARROW.join(dereference_from(regval))))
            fd.write("}\n")
            fd.flush()
        return False


@register
class FtraceCommand(GenericCommand):
    """Tracks a function given in parameter for arguments and return code."""
    _cmdline_ = "ftrace"
    _syntax_ = "{:s} <function_name1>,<nb_args1> [<function_name2>,<nb_args2> ...]".format(
        _cmdline_)

    def __init__(self) -> None:
        super().__init__()
        self["output"] = (PLUGIN_FTRACE_DEFAULT_OUTPUT,
                          "Path to store/load the syscall tables files")
        return

    def do_invoke(self, args):
        if len(args) < 1:
            self.usage()
            return

        self.bkps = []

        for item in args:
            funcname, nb_args = item.split(",")
            self.bkps.append(FtraceEnterBreakpoint(funcname, int(nb_args)))
            ok("added '{}()' (with {} args) to tracking list".format(funcname, nb_args))

        gdb.events.exited.connect(self.cleanup)
        return

    def cleanup(self, _: gdb.ExitedEvent):
        for bp in self.bkps:
            if bp.retbp:
                bp.retbp.delete()
            bp.delete()
        gdb.events.exited.disconnect(self.cleanup)
        return
