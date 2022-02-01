import functools
import gdb
import rpyc
import pprint

__AUTHOR__ = "hugsy"
__VERSION__ = 0.1
__DESCRIPTION_ = """Control headlessly IDA from GEF using RPyC"""


sess = {
    "sock": None,
    "breakpoints": set(),
    "old_colors": {},
}


def is_current_elf_pie():
    return checksec(get_filepath())["PIE"]


def get_rva(addr):
    base_address = [x.page_start for x in get_process_maps() if x.path == get_filepath()][0]
    return addr - base_address


def ida_rpyc_resync(evt):
    return gdb.execute("ida-rpyc synchronize", from_tty=True)


def reconnect():
    try:
        host = get_gef_setting("ida-rpyc.host")
        port = get_gef_setting("ida-rpyc.port")
        sock = rpyc.connect(host, port)

        gef_on_stop_hook(ida_rpyc_resync)
        gef_on_continue_hook(ida_rpyc_resync)
    except ConnectionRefusedError:
        sock = None
        gef_on_stop_unhook(ida_rpyc_resync)
        gef_on_continue_unhook(ida_rpyc_resync)
    return sock


def only_if_active_rpyc_session(f):
    """Decorator wrapper to check if the RPyC session is running."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        global sess

        for i in range(2):
            if sess["sock"]:
                return f(*args, **kwargs)
            sess["sock"] = reconnect()

        if not sess["sock"]:
            warn("No RPyC session running")
    return wrapper


class RpycIdaCommand(GenericCommand):
    """RPyCIda root command"""
    _cmdline_ = "ida-rpyc"
    _syntax_ = "{:s} (breakpoints|comments|info|highlight|jump)".format(_cmdline_)
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        global sess
        super(RpycIdaCommand, self).__init__(prefix=True)
        self["host"] = ("127.0.0.1", "IDA host IP address")
        self["port"] = (18812, "IDA host port")
        self["sync_cursor"] = (False, "Enable real-time $pc synchronisation")
        self.last_hl_ea = -1
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        if not argv:
            self.usage()
            return

        if argv[0] == "synchronize" or self.get_setting("sync_cursor"):
            self.synchronize()
        return

    def synchronize(self):
        """Submit all active breakpoint addresses to IDA/BN."""
        pc = current_arch.pc
        vmmap = get_process_maps()
        base_address = min([x.page_start for x in vmmap if x.path == get_filepath()])
        end_address = max([x.page_end for x in vmmap if x.path == get_filepath()])
        if not (base_address <= pc < end_address):
            return

        if self.last_hl_ea >= 0:
            gdb.execute("ida-rpyc highlight del {:#x}".format(self.last_hl_ea))

        gdb.execute("ida-rpyc jump {:#x}".format(pc))

        gdb.execute("ida-rpyc highlight add {:#x}".format(pc))
        self.last_hl_ea = pc
        return


class RpycIdaHighlightCommand(RpycIdaCommand):
    """RPyC IDA: highlight root command"""
    _cmdline_ = "ida-rpyc highlight"
    _syntax_ = "{:s} (add|del)".format(_cmdline_)
    _aliases_ = ["ida-rpyc hl", ]
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(prefix=True) #pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        pass


class RpycIdaHighlightAddCommand(RpycIdaHighlightCommand):
    """RPyC IDA: highlight a specific line in the IDB"""
    _cmdline_ = "ida-rpyc highlight add"
    _syntax_ = "{:s} [*0xAddress|Symbol]".format(_cmdline_)
    _aliases_ = []
    _example_ = "{:s} main".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(complete=gdb.COMPLETE_SYMBOL) #pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        global sess
        if not argv:
            self.usage()
            return

        addr = current_arch.pc if not argv else parse_address(argv[0])
        if is_current_elf_pie():
            addr = get_rva(addr)

        color = int(argv[1], 0) if len(argv) > 1 else 0x00ff00
        ok("highlight ea={:#x} as {:#x}".format(addr, color))
        sess["old_colors"][addr] = sess["sock"].root.idc.get_color(addr, sess["sock"].root.idc.CIC_ITEM)
        sess["sock"].root.idc.set_color(addr, sess["sock"].root.idc.CIC_ITEM, color)
        return


class RpycIdaHighlightDeleteCommand(RpycIdaHighlightCommand):
    """RPyC IDA: remove the highlighting of the given line in the IDB"""
    _cmdline_ = "ida-rpyc highlight del"
    _syntax_ = "{:s} [*0xAddress|Symbol]".format(_cmdline_)
    _aliases_ = []
    _example_ = "{:s} main".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(complete=gdb.COMPLETE_SYMBOL) #pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        global sess
        if not argv:
            self.usage()
            return

        addr = current_arch.pc if not argv else parse_address(argv[0])
        if is_current_elf_pie():
            addr = get_rva(addr)

        if addr not in sess["old_colors"]:
            warn("{:#x} was not highlighted".format(addr))
            return

        color = sess["old_colors"].pop(addr)
        ok("unhighlight ea={:#x} back to {:#x}".format(addr, color))
        sess["sock"].root.idc.set_color(addr, sess["sock"].root.idc.CIC_ITEM, color)
        return


class RpycIdaBreakpointCommand(RpycIdaCommand):
    """RPyC IDA: breakpoint root command"""
    _cmdline_ = "ida-rpyc breakpoints"
    _syntax_ = "{:s} (add|del|list)".format(_cmdline_)
    _aliases_ = ["ida-rpyc bp", ]
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(prefix=True) #pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        pass


class RpycIdaBreakpointListCommand(RpycIdaBreakpointCommand):
    """RPyC IDA: breakpoint list command"""
    _cmdline_ = "ida-rpyc breakpoints list"
    _syntax_ = "{:s}".format(_cmdline_)
    _aliases_ = []
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        super(RpycIdaBreakpointCommand, self).__init__() #pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        if not argv:
            self.usage()
        pprint.pprint(sess["breakpoints"])
        return


class RpycIdaInfoSessionCommand(RpycIdaCommand):
    """RPyC IDA: display info about the current session"""
    _cmdline_ = "ida-rpyc info"
    _syntax_ = "{:s}".format(_cmdline_)
    _aliases_ = []
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__() #pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        if not argv:
            self.usage()
            return

        pprint.pprint(sess)
        return


class RpycIdaJumpCommand(RpycIdaCommand):
    """RPyC IDA: display info about the current session"""
    _cmdline_ = "ida-rpyc jump"
    _syntax_ = "{:s} [0xaddress|symbol]".format(_cmdline_)
    _aliases_ = ["ida-rpyc goto"]
    _example_ = "{:s} main".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(complete=gdb.COMPLETE_SYMBOL) #pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        addr = current_arch.pc if not argv else parse_address(argv[0])
        if is_current_elf_pie():
            addr = get_rva(addr)
        # ok("jumping to {:#x}".format(addr))
        sess["sock"].root.idaapi.jumpto(addr)
        return


class RpycIdaCommentCommand(RpycIdaCommand):
    """RPyCIda comment root command"""
    _cmdline_ = "ida-rpyc comments"
    _syntax_ = "{:s} (add|del)".format(_cmdline_)
    _aliases_ = ["ida-rpyc cmt", ]
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(prefix=True) #pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        return


class RpycIdaCommentAddCommand(RpycIdaCommentCommand):
    """RPyCIda add comment command"""
    _cmdline_ = "ida-rpyc comments add"
    _syntax_ = "{:s} \"My comment\" [*0xaddress|register|symbol]".format(_cmdline_)
    _aliases_ = []
    _example_ = "{:s} \"I was here\" $pc".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(complete=gdb.COMPLETE_SYMBOL) #pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        repeatable_comment = 1

        if not argv:
            self.usage()
            return

        comment = argv[0]
        ea = current_arch.pc

        if len(argv) > 1:
            ea = parse_address(argv[1])

        if is_current_elf_pie():
            ea = get_rva(ea)

        idc = sess["sock"].root.idc
        idc.set_cmt(ea, comment, repeatable_comment)
        return


if __name__ == "__main__":
    cmds = [
        RpycIdaCommand,

        RpycIdaInfoSessionCommand,
        RpycIdaJumpCommand,

        RpycIdaBreakpointCommand,
        RpycIdaBreakpointListCommand,

        RpycIdaCommentCommand,
        RpycIdaCommentAddCommand,

        RpycIdaHighlightCommand,
        RpycIdaHighlightAddCommand,
        RpycIdaHighlightDeleteCommand,
    ]

    for cmd in cmds:
        register_external_command(cmd())
