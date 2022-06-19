__AUTHOR__ = "hugsy"
__VERSION__ = 0.1


@register
class CurrentFrameStack(GenericCommand):
    """Show the entire stack of the current frame."""
    _cmdline_ = "current-stack-frame"
    _syntax_  = "{:s}".format(_cmdline_)
    _aliases_ = ["stack-view",]
    _example_ = "{:s}".format(_cmdline_)

    @only_if_gdb_running
    def do_invoke(self, argv):
        ptrsize = gef.arch.ptrsize
        frame = gdb.selected_frame()

        if not frame.older():
            #reason = frame.unwind_stop_reason()
            reason_str = gdb.frame_stop_reason_string( frame.unwind_stop_reason() )
            warn("Cannot determine frame boundary, reason: {:s}".format(reason_str))
            return

        saved_ip = frame.older().pc()
        stack_hi = align_address(int(frame.older().read_register("sp")))
        stack_lo = align_address(int(frame.read_register("sp")))
        should_stack_grow_down = gef.config["context.grow_stack_down"] == True
        results = []

        for offset, address in enumerate(range(stack_lo, stack_hi, ptrsize)):
            pprint_str = DereferenceCommand.pprint_dereferenced(stack_lo, offset)
            if dereference(address) == saved_ip:
                pprint_str += " " + Color.colorify("($savedip)", attrs="gray underline")
            results.append(pprint_str)

        if should_stack_grow_down:
            results.reverse()
            gef_print(titlify("Stack top (higher address)"))
        else:
            gef_print(titlify("Stack bottom (lower address)"))

        gef_print("\n".join(results))

        if should_stack_grow_down:
            gef_print(titlify("Stack bottom (lower address)"))
        else:
            gef_print(titlify("Stack top (higher address)"))
        return

