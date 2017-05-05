#
# Quick'n dirty function tracer scripts for GEF
#
# @_hugsy_
#
# Load with:
# gef> source /path/to/this/script.py
#
# Use with
# gef> ftrace <function_name>,<num_of_args>
#
class FtraceEnterBreakpoint(gdb.Breakpoint):
    def __init__(self, location, nb_args, *args, **kwargs):
        super(FtraceEnterBreakpoint, self).__init__(location, gdb.BP_BREAKPOINT, internal=True)
        self.silent = True
        self.nb_args = nb_args
        return

    def stop(self):
        regs = [ "{:#x}".format(get_register(r)) for r in current_arch.function_parameters[:self.nb_args] ]
        self.retbp = FtraceExitBreakpoint(location=self.location, regs=regs)
        return False

class FtraceExitBreakpoint(gdb.FinishBreakpoint):
    def __init__(self, *args, **kwargs):
        super(FtraceExitBreakpoint, self).__init__(gdb.newest_frame(), internal=True)
        self.silent = True
        self.args = kwargs
        return

    def stop(self):
        retval = "(void)" if self.return_value is None else "{:#x}".format(long(self.return_value))
        output = get_gef_setting("ftrace.output") or "/dev/stderr"
        with open(output, "a") as f:
            f.write("{}({}) = {}\n".format(self.args["location"], ','.join(self.args["regs"]), retval))
        return False

class FtraceCommand(GenericCommand):
    """Tracks a function given in parameter for arguments and return code."""
    _cmdline_ = "ftrace"
    _syntax_  = "{:s} <function_name>".format(_cmdline_)

    def do_invoke(self, args):
        if len(args) < 1: return
        for item in args:
            funcname, nb_args = item.split(",")
            FtraceEnterBreakpoint(funcname, int(nb_args))
            ok("added '{}' to ltrace list".format(funcname))
        return

if __name__ == "__main__":
    register_external_command( FtraceCommand() )
