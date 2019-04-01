import subprocess

class BreakOnLoadSharedLibrary(gdb.Breakpoint):
    def __init__(self, module_name):
        super(BreakOnLoadSharedLibrary, self).__init__("dlopen", type=gdb.BP_BREAKPOINT, internal=False)
        self.module_name = module_name
        self.silent = True
        self.enabled = True
        return

    def stop(self):
        reg = current_arch.function_parameters[0]
        addr = lookup_address(get_register(reg))
        if addr.value==0:
            return False
        path = read_cstring_from_memory(addr.value, max_length=None)
        if path.endswith(self.module_name):
            return True
        return False


class WindbgSxeCommand(GenericCommand):
    """WinDBG compatibility layer: sxe (set-exception-enable): break on loading libraries."""
    _cmdline_ = "sxe"
    _syntax_  = "{:s} [ld,ud]:module".format(_cmdline_)
    _example_ = "{:s} ld:mylib.so".format(_cmdline_)

    def __init__(self):
        super(WindbgSxeCommand, self).__init__(complete=gdb.COMPLETE_NONE)
        self.breakpoints = []
        return

    def do_invoke(self, argv):
        if len(argv) < 1:
            self.usage()
            return

        action, module = argv[0].split(":", 1)
        if action=="ld":
            self.breakpoints.append(BreakOnLoadSharedLibrary(module))
        elif action=="ud":
            bkps = [bp for bp in self.breakpoints if bp.module_name == module]
            if len(bkps):
                bkp = bkps[0]
                bkp.enabled = False
                bkp.delete()
                bkps.remove(bkp)
        else:
            self.usage()
        return


class WindbgTcCommand(GenericCommand):
    """WinDBG compatibility layer: tc - trace to next call."""
    _cmdline_ = "tc"
    _syntax_  = "{:s} [COUNT]".format(_cmdline_)

    @only_if_gdb_running
    def do_invoke(self, argv):
        cnt = int(argv[0]) if len(argv) else 0xffffffffffffffff
        while cnt:
            cnt -= 1
            set_gef_setting("context.enable", False)
            gdb.execute("stepi")
            insn = gef_current_instruction(current_arch.pc)
            if current_arch.is_call(insn):
                break
        set_gef_setting("context.enable", True)
        gdb.execute("context")
        return


class WindbgPcCommand(GenericCommand):
    """WinDBG compatibility layer: pc - run until call."""
    _cmdline_ = "pc"
    _syntax_  = "{:s} [COUNT]".format(_cmdline_)

    @only_if_gdb_running
    def do_invoke(self, argv):
        cnt = int(argv[0]) if len(argv) else 0xffffffffffffffff
        while cnt:
            cnt -= 1
            set_gef_setting("context.enable", False)
            gdb.execute("nexti")
            insn = gef_current_instruction(current_arch.pc)
            if current_arch.is_call(insn):
                break

        set_gef_setting("context.enable", True)
        gdb.execute("context")
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


class WindbgUCommand(GenericCommand):
    """WinDBG compatibility layer: u - disassemble."""
    _cmdline_ = "u"
    _syntax_  = "{:s}".format(_cmdline_)

    def __init__(self):
        super(WindbgUCommand, self).__init__(complete=gdb.COMPLETE_LOCATION)
        return

    @only_if_gdb_running
    def do_invoke(self, argv):
        length = 16
        location = current_arch.pc
        for arg in argv:
            if arg[0] in ("l","L"):
                length = int(arg[1:])
            else:
                location = safe_parse_and_eval(arg)
                if location is not None:
                    if hasattr(location, "address"):
                        location = long(location.address)
                    else:
                        location = long(location)

        for insn in gef_disassemble(location, length):
            print(insn)
        return


class WindbgXCommand(GenericCommand):
    """WinDBG compatibility layer: x - search symbol."""
    _cmdline_ = "xs"
    _syntax_  = "{:s} REGEX".format(_cmdline_)

    def __init__(self):
        super(WindbgXCommand, self).__init__(complete=gdb.COMPLETE_LOCATION)
        return

    def do_invoke(self, argv):
        if len(argv) < 1:
            err("Missing REGEX")
            return

        sym = argv[0]
        try:
            gdb.execute("info function {}".format(sym))
            gdb.execute("info address {}".format(sym))
        except gdb.error:
            pass
        return


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
        return __windbg_prompt__(x)
    else:
        return __gef_prompt__(x)


# Prompt
set_gef_setting("gef.use-windbg-prompt", False, bool, "Use WinDBG like prompt")
gdb.prompt_hook = __default_prompt__

# Aliases
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
    WindbgTcCommand,
    WindbgPcCommand,
    WindbgHhCommand,
    WindbgGoCommand,
    WindbgXCommand,
    WindbgUCommand,
    WindbgSxeCommand,
]

for _ in windbg_commands: register_external_command(_())
