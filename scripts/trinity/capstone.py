import capstone

import sys

def disassemble(location: int, nb_insn: int, **kwargs: Any) -> Generator[Instruction, None, None]:
    """Disassemble `nb_insn` instructions after `addr` and `nb_prev` before
    `addr` using the Capstone-Engine disassembler, if available.
    Return an iterator of Instruction objects."""

    def cs_insn_to_gef_insn(cs_insn: "capstone.CsInsn") -> Instruction:
        sym_info = gdb_get_location_from_symbol(cs_insn.address)
        loc = "<{}+{}>".format(*sym_info) if sym_info else ""
        ops = [] + cs_insn.op_str.split(", ")
        return Instruction(cs_insn.address, loc, cs_insn.mnemonic, ops, cs_insn.bytes)

    capstone    = sys.modules["capstone"]
    arch, mode  = get_capstone_arch(arch=kwargs.get("arch"), mode=kwargs.get("mode"), endian=kwargs.get("endian"))
    cs          = capstone.Cs(arch, mode)
    cs.detail   = True

    page_start  = align_address_to_page(location)
    offset      = location - page_start
    pc          = gef.arch.pc

    skip       = int(kwargs.get("skip", 0))
    nb_prev    = int(kwargs.get("nb_prev", 0))
    if nb_prev > 0:
        location = gdb_get_nth_previous_instruction_address(pc, nb_prev)
        nb_insn += nb_prev

    code = kwargs.get("code", gef.memory.read(location, gef.session.pagesize - offset - 1))
    for insn in cs.disasm(code, location):
        if skip:
            skip -= 1
            continue
        nb_insn -= 1
        yield cs_insn_to_gef_insn(insn)
        if nb_insn == 0:
            break
    return


def get_arch(arch: Optional[str] = None, mode: Optional[str] = None, endian: Optional[bool] = None, to_string: bool = False) -> Union[Tuple[None, None], Tuple[str, Union[int, str]]]:
    capstone = sys.modules["capstone"]

    # hacky patch to unify capstone/ppc syntax with keystone & unicorn:
    # CS_MODE_PPC32 does not exist (but UC_MODE_32 & KS_MODE_32 do)
    if is_arch(Elf.Abi.POWERPC64):
        raise OSError("Capstone not supported for PPC64 yet.")

    if is_alive() and is_arch(Elf.Abi.POWERPC):

        arch = "PPC"
        mode = "32"
        endian = (gef.arch.endianness == Endianness.BIG_ENDIAN)
        return get_generic_arch(capstone, "CS",
                                arch or gef.arch.arch,
                                mode or gef.arch.mode,
                                endian,
                                to_string)

    if (arch, mode, endian) == (None, None, None):
        return get_generic_running_arch(capstone, "CS", to_string)
    return get_generic_arch(capstone, "CS",
                            arch or gef.arch.arch,
                            mode or gef.arch.mode,
                            endian or gef.arch.endianness == Endianness.BIG_ENDIAN,
                            to_string)


@register
class CapstoneDisassembleCommand(GenericCommand):
    """Use capstone disassembly framework to disassemble code."""

    _cmdline_ = "capstone-disassemble"
    _syntax_  = f"{_cmdline_} [-h] [--show-opcodes] [--length LENGTH] [LOCATION]"
    _aliases_ = ["cs-dis"]
    _example_ = f"{_cmdline_} --length 50 $pc"

    def pre_load(self) -> None:
        try:
            __import__("capstone")
        except ImportError:
            msg = "Missing `capstone` package for Python. Install with `pip install capstone`."
            raise ImportWarning(msg)
        return

    def __init__(self) -> None:
        super().__init__(complete=gdb.COMPLETE_LOCATION)
        return

    @only_if_gdb_running
    @parse_arguments({("location"): "$pc"}, {("--show-opcodes", "-s"): True, "--length": 0})
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        args = kwargs["arguments"]
        show_opcodes = args.show_opcodes
        length = args.length or gef.config["context.nb_lines_code"]
        location = parse_address(args.location)
        if not location:
            info(f"Can't find address for {args.location}")
            return

        insns = []
        opcodes_len = 0
        for insn in capstone_disassemble(location, length, skip=length * self.repeat_count, **kwargs):
            insns.append(insn)
            opcodes_len = max(opcodes_len, len(insn.opcodes))

        for insn in insns:
            insn_fmt = f"{{:{opcodes_len}o}}" if show_opcodes else "{}"
            text_insn = insn_fmt.format(insn)
            msg = ""

            if insn.address == gef.arch.pc:
                msg = Color.colorify(f"{RIGHT_ARROW}   {text_insn}", "bold red")
                valid, reason = self.capstone_analyze_pc(insn, length)
                if valid:
                    gef_print(msg)
                    gef_print(reason)
                    break
            else:
                msg = f"      {text_insn}"

            gef_print(msg)
        return

    def capstone_analyze_pc(self, insn: Instruction, nb_insn: int) -> Tuple[bool, str]:
        if gef.arch.is_conditional_branch(insn):
            is_taken, reason = gef.arch.is_branch_taken(insn)
            if is_taken:
                reason = f"[Reason: {reason}]" if reason else ""
                msg = Color.colorify(f"\tTAKEN {reason}", "bold green")
            else:
                reason = f"[Reason: !({reason})]" if reason else ""
                msg = Color.colorify(f"\tNOT taken {reason}", "bold red")
            return (is_taken, msg)

        if gef.arch.is_call(insn):
            target_address = int(insn.operands[-1].split()[0], 16)
            msg = []
            for i, new_insn in enumerate(capstone_disassemble(target_address, nb_insn)):
                msg.append(f"   {DOWN_ARROW if i == 0 else ' '}  {new_insn!s}")
            return (True, "\n".join(msg))

        return (False, "")
