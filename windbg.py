import subprocess

class WindbgPcCommand(GenericCommand):
    """WinDBG compatibility layer: pc - run until call."""
    _cmdline_ = "pc"
    _syntax_  = "{:s}".format(_cmdline_)

    @only_if_gdb_running
    def do_invoke(self, argv):
        while True:
            set_gef_setting("context.enable", False)
            gdb.execute("si")
            insn = gef_current_instruction(current_arch.pc)
            if current_arch.is_call(insn):
                set_gef_setting("context.enable", True)
                gdb.execute("context")
                break
        return


class WindbgHhCommand(GenericCommand):
    """WinDBG compatibility layer: hh - open help in web browser."""
    _cmdline_ = "hh"
    _syntax_  = "{:s}".format(_cmdline_)

    def do_invoke(self, argv):
        url = "https://gef.readthedocs.io/en/master/"
        if len(argv):
            url += "search.html?q={}".format(argv[0])
        p = subprocess.Popen(["xdg-open", url],
                             cwd="/",
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        return


class WindbgGoCommand(GenericCommand):
    """WinDBG compatibility layer: g - go."""
    _cmdline_ = "g"
    _syntax_  = "{:s}".format(_cmdline_)

    def do_invoke(self, argv):
        if is_alive():
            gdb.execute("continue")
        else:
            gdb.execute("run {}".format(" ".join(argv)))
        return


class WindbgCommand(GenericCommand):
    """WinDBG config."""
    _cmdline_ = "windbg"
    _syntax_ = _cmdline_

    def __init__(self, *args, **kwargs):
        super(WindbgCommand, self).__init__(complete=gdb.COMPLETE_NONE)
        self.add_setting("use-windbg-prompt", False, "Use WinDBG like prompt")
        return

    @staticmethod
    def __windbg_prompt__(current_prompt):
        """WinDBG prompt function."""
        p = "0:000 "
        if PYTHON_MAJOR==3:
            p+="\u27a4  "
        else:
            p+="> "
        if get_gef_setting("gef.readline_compat")==True or \
           get_gef_setting("gef.disable_color")==True:
            return gef_prompt

        if is_alive():
            return Color.colorify(p, attrs="bold green")
        else:
            return Color.colorify(p, attrs="bold red")


def __default_prompt__(x):
    if get_gef_setting("windbg.use-windbg-prompt") == True:
        return WindbgCommand.__windbg_prompt__(x)
    else:
        return __gef_prompt__(x)


# Prompt
gdb.prompt_hook = __default_prompt__

# Aliases
GefAlias("x", "info functions", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("u", "display/16i", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("da", "display/s", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("dt", "pcustom")
GefAlias("dq", "hexdump qword", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("dd", "hexdump dword", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("dw", "hexdump word", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("db", "hexdump byte", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("eq", "patch qword", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("ed", "patch dword", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("ew", "patch word", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("eb", "patch byte", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("ea", "patch string", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("dps", "dereference", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("bp", "break", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("bl", "info breakpoints")
GefAlias("bd", "disable breakpoints")
GefAlias("bc", "delete breakpoints")
GefAlias("be", "enable breakpoints")
GefAlias("tbp", "tbreak", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("s", "grep", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("pa", "advance", completer_class=gdb.COMPLETE_LOCATION)
GefAlias("kp", "info stack")
GefAlias("ptc", "finish")

# Commands
windbg_commands = [
    WindbgCommand,
    WindbgPcCommand,
    WindbgHhCommand,
    WindbgGoCommand,
]

for _ in windbg_commands: register_external_command(_())
