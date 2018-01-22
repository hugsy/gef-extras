class CurrentFrameStack(GenericCommand):
    """Show the entire stack of the current frame."""
    _cmdline_ = "current-stack-frame"
    _syntax_  = "{:s}".format(_cmdline_)
    _aliases_ = ["stack", "full-stack",]
    _example_ = "{:s}".format(_cmdline_)

    @only_if_gdb_running
    def do_invoke(self, argv):
        ptrsize = current_arch.ptrsize
        frame = gdb.selected_frame()

        if not frame.older():
            reason = frame.unwind_stop_reason()
            reason_str = gdb.frame_stop_reason_string( frame.unwind_stop_reason() )
            warn("Cannot determine frame boundary, reason: {:s}".format(reason_str))
            return

        saved_ip = frame.older().pc()
        base_address_color = get_gef_setting("theme.dereference_base_address")
        stack_hi = long(frame.older().read_register("sp"))
        stack_lo = long(frame.read_register("sp"))
        should_stack_grow_down = get_gef_setting("context.grow_stack_down") == True
        results = []

        for offset, address in enumerate(range(stack_lo, stack_hi, ptrsize)):
            pprint_str = DereferenceCommand.pprint_dereferenced(stack_lo, offset)
            if dereference(address) == saved_ip:
                pprint_str += " " + Color.colorify("($savedip)", attrs="gray underline")
            results.append(pprint_str)

        if should_stack_grow_down:
            results.reverse()
            print(titlify("Stack top (higher address)"))
        else:
            print(titlify("Stack bottom (lower address)"))

        for res in results:
            print(res)

        if should_stack_grow_down:
            print(titlify("Stack bottom (lower address)"))
        else:
            print(titlify("Stack top (higher address)"))
        return


register_external_command(CurrentFrameStack())
