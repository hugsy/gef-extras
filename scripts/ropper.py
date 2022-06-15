__AUTHOR__    = "hugsy"
__VERSION__   = 0.1
__NAME__      = "ropper"

import sys
import readline

import gdb
import ropper


@register
class RopperCommand(GenericCommand):
    """Ropper (https://scoding.de/ropper/) plugin."""

    _cmdline_ = "ropper"
    _syntax_  = f"{_cmdline_} [ROPPER_OPTIONS]"

    def __init__(self) -> None:
        super().__init__(complete=gdb.COMPLETE_NONE)
        return

    @only_if_gdb_running
    def do_invoke(self, argv: List[str]) -> None:
        ropper = sys.modules["ropper"]
        if "--file" not in argv:
            path = gef.session.file
            if not path:
                err("No file provided")
                return
            sect = next(filter(lambda x: x.path == path, gef.memory.maps))
            argv.append("--file")
            argv.append(path)
            argv.append("-I")
            argv.append(f"{sect.page_start:#x}")

        # ropper set up own autocompleter after which gdb/gef autocomplete don't work
        old_completer_delims = readline.get_completer_delims()
        old_completer = readline.get_completer()

        try:
            ropper.start(argv)
        except RuntimeWarning:
            return

        readline.set_completer(old_completer)
        readline.set_completer_delims(old_completer_delims)
        return
