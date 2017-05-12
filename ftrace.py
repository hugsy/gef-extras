#
# Quick'n dirty function tracer scripts for GEF
#
# @_hugsy_
#
# Load with:
# gef> source /path/to/this/script.py
#
# Use with
# gef> ftrace <function_name1>,<num_of_args> <function_name2>,<num_of_args>  ...
#

import collections


class FtraceEnterBreakpoint(gdb.Breakpoint):
    def __init__(self, location, nb_args, *args, **kwargs):
        super(FtraceEnterBreakpoint, self).__init__(location, gdb.BP_BREAKPOINT, internal=True)
        self.silent = True
        self.nb_args = nb_args
        return

    def stop(self):
        regs = collections.OrderedDict()
        for r in current_arch.function_parameters[:self.nb_args]:
            regs[r] = get_register(r)
        self.retbp = FtraceExitBreakpoint(location=self.location, regs=regs)
        return False

class FtraceExitBreakpoint(gdb.FinishBreakpoint):
    def __init__(self, *args, **kwargs):
        super(FtraceExitBreakpoint, self).__init__(gdb.newest_frame(), internal=True)
        self.silent = True
        self.args = kwargs
        return

    def stop(self):
        if self.return_value:
            retval = "{:#x}".format(long(self.return_value))
        else:
            retval = get_register(current_arch.return_register)

        output = get_gef_setting("ftrace.output")
        mode = "a"
        if output is None:
            output = "/dev/stderr"
            mode = "w"

        with open(output, "w") as fd:
            fd.write("{}() = {} {{\n".format(self.args["location"], retval))
            for reg in self.args["regs"].keys():
                regval = self.args["regs"][reg]
                fd.write("\t{} {} {}\n".format(reg, right_arrow, right_arrow.join(DereferenceCommand.dereference_from(regval))))
            fd.write("}\n")
            fd.flush()
        return False

class FtraceCommand(GenericCommand):
    """Tracks a function given in parameter for arguments and return code."""
    _cmdline_ = "ftrace"
    _syntax_  = "{:s} <function_name1>,<nb_args1> [<function_name2>,<nb_args2> ...]".format(_cmdline_)

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

    def cleanup(self, events):
        for bp in self.bkps:
            bp.retbp.delete()
            bp.delete()
        gdb.events.exited.disconnect(self.cleanup)
        return


if __name__ == "__main__":
    register_external_command( FtraceCommand() )
