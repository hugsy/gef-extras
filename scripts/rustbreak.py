class RustMainBreakpoint(gdb.Breakpoint):
    """Breakpoint used internally to stop execution at the main function of a Rust binary."""

    def __init__(self, location):
        super(EntryBreakBreakpoint, self).__init__(location, gdb.BP_BREAKPOINT, internal=True, temporary=True)
        self.silent = True
        return

    def stop(self):
        return True


class RustMainBreakCommand(GenericCommand):
    """Finds the actual main function of a Rust binary, and sets a temporary breakpoint on it.
    It is based on the pattern that in Rust binaries, the following instructions appear right 
    before entering main:
    jmp    QWORD PTR [rsi+0x18]
    ...  (no function calls instructions in between)
    call   QWORD PTR [rdi]
    """
    _cmdline_ = "rust-main-break"
    _syntax_  = _cmdline_

    def do_invoke(self, args):
        fpath = get_filepath()
        if fpath is None:
            warn("No executable to debug, use `file` to load a binary")
            return

        if not os.access(fpath, os.X_OK):
            warn("The file '{}' is not executable.".format(fpath))
            return

        if is_alive():
            warn("gdb is already running")
            return

        disable_context()
        gdb.execute('entry-break')

        # get bytes in .text to find address with the jmp instruction
        vmmap = get_process_maps()
        base_address, end_address = [(x.page_start, x.page_end) for x in vmmap if x.path == get_filepath()][0]
        text_section = bytes(read_memory(base_address, end_address - base_address))

        info("Searching for 'jmp QWORD PTR [rsi + 0x18]' instructions")

        for addr in self.find_jmp_instruction(text_section):
            try:
                addr += base_address
                info("Trying {:s}".format(hex(addr)))
                bp = EntryBreakBreakpoint("*{:s}".format(hex(addr)))
                gdb.execute("run {}".format(" ".join(args)))

                insn = gef_current_instruction(current_arch.pc)
                while not (insn.mnemonic == "call" and " ".join(insn.operands) == "QWORD PTR [rdi]"):
                    gdb.execute("si")
                    insn = gef_current_instruction(current_arch.pc)
                    if insn.mnemonic == "ret":
                        info("Not at main yet. Trying next address.")
                        continue

                enable_context()
                gdb.execute("si")
                info("Found 'main' at {:s}".format(hex(current_arch.pc)))

                return

            except gdb.error as gdb_error:
                if 'The "remote" target does not support "run".' in str(gdb_error):
                    # this case can happen when doing remote debugging
                    gdb.execute("continue")
                    return
                continue

        gdb.execute("kill")
        err("Failed to find 'main' for Rust binary")
        enable_context()

        return

    def find_jmp_instruction(self, text):
        """Searches in the .text section for \xff\x66\x18 (jmp QWORD PTR [rsi + 0x18])"""

        opcode = b"\xff\x66\x18"
        last_found = -1  # Begin at -1 so the next position to search from is 0
        while True:
            # Find next index of opcode, by starting after its last known position
            last_found = text.find(opcode, last_found + 1)
            if last_found == -1:  
                break  # All occurrences have been found
            yield last_found


if __name__ == "__main__":
    register_external_command( RustMainBreakCommand() )
