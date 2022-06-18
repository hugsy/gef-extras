"""

Script to control headlessly IDA from GEF using RPyC

"""

import functools
import pprint
from typing import TYPE_CHECKING, Any, List, Set, Dict, Optional

import gdb
import rpyc

if TYPE_CHECKING:
    from . import *
    from . import gdb

__AUTHOR__ = "hugsy"
__VERSION__ = 0.2


@register
class RemoteDecompilerSession:
    sock: Optional[int] = None
    breakpoints: Set[str] = set()
    old_colors: Dict[int, str] = {}

    # IDA aliases
    @property
    def idc(self):
        return self.sock.root.idc

    @property
    def idaapi(self):
        return self.sock.root.idaapi

    def reconnect(self) -> bool:
        try:
            host = gef.config["ida-rpyc.host"]
            port = gef.config["ida-rpyc.port"]
            self.sock = rpyc.connect(host, port)
            gef_on_stop_hook(ida_rpyc_resync)
            gef_on_continue_hook(ida_rpyc_resync)
            return False
        except ConnectionRefusedError:
            self.sock = None
            gef_on_stop_unhook(ida_rpyc_resync)
            gef_on_continue_unhook(ida_rpyc_resync)
        return False

    def print_info(self) -> None:
        connection_status = "Connection status to "\
                            f"{gef.config['ida-rpyc.host']}:{gef.config['ida-rpyc.port']} ... "
        if self.sock is None:
            warn(f"{connection_status} {Color.redify('DISCONNECTED')}")
            return

        ok(f"{connection_status} {Color.greenify('CONNECTED')}")

        major, minor = self.idaapi.IDA_SDK_VERSION // 100, self.idaapi.IDA_SDK_VERSION % 100
        info(f"Version: {Color.boldify('IDA Pro')} v{major}.{minor}")

        info("Breakpoints")
        gef_print(str(self.breakpoints))

        info("Colors")
        gef_print(str(self.old_colors))
        return


sess = RemoteDecompilerSession()


def is_current_elf_pie():
    sp = checksec(str(gef.session.file))
    return sp["PIE"] == True


def get_rva(addr):
    base_address = [
        x.page_start for x in gef.memory.maps if x.path == get_filepath()][0]
    return addr - base_address


def ida_rpyc_resync(evt):
    return gdb.execute("ida-rpyc synchronize", from_tty=True)


def only_if_active_rpyc_session(f):
    """Decorator wrapper to check if the RPyC session is running."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        global sess
        for _ in range(2):
            if sess.sock:
                return f(*args, **kwargs)
            sess.reconnect()

        if not sess.sock:
            warn("No RPyC session running")
    return wrapper


@register
class RpycIdaCommand(GenericCommand):
    """RPyCIda root command"""
    _cmdline_ = "ida-rpyc"
    _syntax_ = "{:s} (breakpoints|comments|info|highlight|jump)".format(
        _cmdline_)
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        global sess
        super().__init__(prefix=True)
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

        if argv[0] == "synchronize" or self["sync_cursor"]:
            self.synchronize()
        return

    def synchronize(self):
        """Submit all active breakpoint addresses to IDA/BN."""
        pc = gef.arch.pc
        vmmap = gef.memory.maps
        base_address = min(
            [x.page_start for x in vmmap if x.path == get_filepath()])
        end_address = max(
            [x.page_end for x in vmmap if x.path == get_filepath()])
        if not (base_address <= pc < end_address):
            return

        if self.last_hl_ea >= 0:
            gdb.execute(f"ida-rpyc highlight del {self.last_hl_ea:#x}")

        gdb.execute(f"ida-rpyc jump {pc:#x}")
        gdb.execute(f"ida-rpyc highlight add {pc:#x}")
        self.last_hl_ea = pc
        return


@register
class RpycIdaHighlightCommand(RpycIdaCommand):
    """RPyC IDA: highlight root command"""
    _cmdline_ = "ida-rpyc highlight"
    _syntax_ = "{:s} (add|del)".format(_cmdline_)
    _aliases_ = ["ida-rpyc hl", ]
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(
            prefix=True)  # pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        pass


@register
class RpycIdaHighlightAddCommand(RpycIdaHighlightCommand):
    """RPyC IDA: highlight a specific line in the IDB"""
    _cmdline_ = "ida-rpyc highlight add"
    _syntax_ = "{:s} [*0xAddress|Symbol]".format(_cmdline_)
    _aliases_ = []
    _example_ = "{:s} main".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(
            complete=gdb.COMPLETE_SYMBOL)  # pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    @parse_arguments({"location": "$pc", }, {"--color": 0x00ff00})
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        args = kwargs["arguments"]
        ea = parse_address(args.location)
        if is_current_elf_pie():
            ea = get_rva(ea)
        color = args.color
        ok("highlight ea={:#x} as {:#x}".format(ea, color))
        sess.old_colors[ea] = sess.idc.get_color(ea, sess.idc.CIC_ITEM)
        sess.idc.set_color(ea, sess.idc.CIC_ITEM, color)
        return


@register
class RpycIdaHighlightDeleteCommand(RpycIdaHighlightCommand):
    """RPyC IDA: remove the highlighting of the given line in the IDB"""
    _cmdline_ = "ida-rpyc highlight del"
    _syntax_ = "{:s} [*0xAddress|Symbol]".format(_cmdline_)
    _aliases_ = []
    _example_ = "{:s} main".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(
            complete=gdb.COMPLETE_SYMBOL)  # pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    @parse_arguments({"location": "$pc", }, {})
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        args = kwargs["arguments"]
        ea = parse_address(args.location)
        if is_current_elf_pie():
            ea = get_rva(ea)

        if ea not in sess.old_colors:
            warn("{:#x} was not highlighted".format(ea))
            return

        color = sess.old_colors.pop(ea)
        ok("unhighlight ea={:#x} back to {:#x}".format(ea, color))
        sess.idc.set_color(ea, sess.idc.CIC_ITEM, color)
        return


@register
class RpycIdaBreakpointCommand(RpycIdaCommand):
    """RPyC IDA: breakpoint root command"""
    _cmdline_ = "ida-rpyc breakpoints"
    _syntax_ = "{:s} (add|del|list)".format(_cmdline_)
    _aliases_ = ["ida-rpyc bp", ]
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(
            prefix=True)  # pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, _):
        pass


@register
class RpycIdaBreakpointListCommand(RpycIdaBreakpointCommand):
    """RPyC IDA: breakpoint list command"""
    _cmdline_ = "ida-rpyc breakpoints list"
    _syntax_ = "{:s}".format(_cmdline_)
    _aliases_ = ["ida-rpyc bl", ]
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        super(RpycIdaBreakpointCommand, self).__init__(
        )  # pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        if not argv:
            self.usage()
        pprint.pprint(sess.breakpoints)
        return


@register
class RpycIdaInfoSessionCommand(RpycIdaCommand):
    """RPyC IDA: display info about the current session"""
    _cmdline_ = "ida-rpyc info"
    _syntax_ = "{:s}".format(_cmdline_)
    _aliases_ = []
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(
        )  # pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, argv):
        sess.print_info()
        return


@register
class RpycIdaJumpCommand(RpycIdaCommand):
    """RPyC IDA: display info about the current session"""
    _cmdline_ = "ida-rpyc jump"
    _syntax_ = "{:s} [0xaddress|symbol]".format(_cmdline_)
    _aliases_ = ["ida-rpyc goto"]
    _example_ = "{:s} main".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(
            complete=gdb.COMPLETE_SYMBOL)  # pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    @parse_arguments({"location": "$pc", }, {})
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        args = kwargs["arguments"]
        ea = parse_address(args.location)
        if is_current_elf_pie():
            ea = get_rva(ea)
        sess.idaapi.jumpto(ea)
        return


@register
class RpycIdaCommentCommand(RpycIdaCommand):
    """RPyCIda comment root command"""
    _cmdline_ = "ida-rpyc comments"
    _syntax_ = "{:s} (add|del)".format(_cmdline_)
    _aliases_ = ["ida-rpyc cmt", ]
    _example_ = "{:s}".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(
            prefix=True)  # pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        pass


@register
class RpycIdaCommentAddCommand(RpycIdaCommentCommand):
    """RPyCIda add comment command"""
    _cmdline_ = "ida-rpyc comments add"
    _syntax_ = "{:s} \"My comment\" --location [*0xaddress|register|symbol]".format(
        _cmdline_)
    _aliases_ = []
    _example_ = "{:s} \"I was here\" --location $pc".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(
            complete=gdb.COMPLETE_SYMBOL)  # pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    @parse_arguments({"comment": ""}, {"--location": "$pc", })
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        args = kwargs["arguments"]
        ea = parse_address(args.location)
        if is_current_elf_pie():
            ea = get_rva(ea)
        comment = args.comment
        repeatable_comment = 1
        sess.idc.set_cmt(ea, comment, repeatable_comment)
        return


@register
class RpycIdaCommentDeleteCommand(RpycIdaCommentCommand):
    """RPyCIda delete comment command"""
    _cmdline_ = "ida-rpyc comments del"
    _syntax_ = "{:s} [LOCATION]".format(_cmdline_)
    _aliases_ = []
    _example_ = "{:s} $pc".format(_cmdline_)

    def __init__(self):
        super(RpycIdaCommand, self).__init__(
            complete=gdb.COMPLETE_SYMBOL)  # pylint: disable=bad-super-call
        return

    @only_if_gdb_running
    @only_if_active_rpyc_session
    @parse_arguments({"location": "$pc", }, {})
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        args = kwargs["arguments"]
        ea = parse_address(args.location)
        if is_current_elf_pie():
            ea = get_rva(ea)
        repeatable_comment = 1
        sess.idc.set_cmt(ea, "", repeatable_comment)
        return
