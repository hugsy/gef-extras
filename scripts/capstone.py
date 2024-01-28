__AUTHOR__ = "hugsy"
__VERSION__ = 0.3
__LICENSE__ = "MIT"

from typing import TYPE_CHECKING, Any, Callable, Generator, List, Optional, Tuple

import gdb
import capstone

if TYPE_CHECKING:
    from . import *
    from . import gdb


__cs: Optional[capstone.Cs] = None


def gef_to_cs_arch() -> Tuple[str, str, str]:
    if gef.arch.arch == "ARM":
        if isinstance(gef.arch, ARM):
            if gef.arch.is_thumb():
                return (
                    "CS_ARCH_ARM",
                    "CS_MODE_THUMB",
                    f"CS_MODE_{repr(gef.arch.endianness).upper()}",
                )
            return (
                "CS_ARCH_ARM",
                "CS_MODE_ARM",
                f"CS_MODE_{repr(gef.arch.endianness).upper()}",
            )

    if gef.arch.arch == "ARM64":
        return "CS_ARCH_ARM64", "0", f"CS_MODE_{repr(gef.arch.endianness).upper()}"

    if gef.arch.arch == "X86":
        if gef.arch.mode == "32":
            return (
                "CS_ARCH_X86",
                "CS_MODE_32",
                f"CS_MODE_{repr(gef.arch.endianness).upper()}",
            )
        if gef.arch.mode == "64":
            return (
                "CS_ARCH_X86",
                "CS_MODE_64",
                f"CS_MODE_{repr(gef.arch.endianness).upper()}",
            )

    if gef.arch.arch == "PPC":
        if gef.arch.mode == "PPC32":
            return (
                "CS_ARCH_PPC",
                "CS_MODE_PPC32",
                f"CS_MODE_{repr(gef.arch.endianness).upper()}",
            )
        if gef.arch.mode == "PPC64":
            return (
                "CS_ARCH_PPC",
                "CS_MODE_PPC64",
                f"CS_MODE_{repr(gef.arch.endianness).upper()}",
            )

    if gef.arch.arch == "MIPS":
        if gef.arch.mode == "MIPS32":
            return (
                "CS_ARCH_MIPS",
                "CS_MODE_MIPS32",
                f"CS_MODE_{repr(gef.arch.endianness).upper()}",
            )
        if gef.arch.mode == "MIPS64":
            return (
                "CS_ARCH_MIPS32",
                "CS_MODE_MIPS64",
                f"CS_MODE_{repr(gef.arch.endianness).upper()}",
            )

    raise ValueError


def cs_disassemble(
    location: int, nb_insn: int, **kwargs: Any
) -> Generator[Instruction, None, None]:
    """Disassemble `nb_insn` instructions after `addr` and `nb_prev` before
    `addr` using the Capstone-Engine disassembler, if available.
    Return an iterator of Instruction objects."""

    def cs_insn_to_gef_insn(cs_insn: capstone.CsInsn) -> Instruction:
        sym_info = gdb_get_location_from_symbol(cs_insn.address)
        loc = f"<{sym_info[0]}+{sym_info[1]}>" if sym_info else ""
        ops = [] + cs_insn.op_str.split(", ")
        return Instruction(cs_insn.address, loc, cs_insn.mnemonic, ops, cs_insn.bytes)

    arch_s, mode_s, endian_s = gef_to_cs_arch()
    cs_arch: int = getattr(capstone, arch_s)
    cs_mode: int = getattr(capstone, mode_s)
    cs_endian: int = getattr(capstone, endian_s)

    cs = capstone.Cs(cs_arch, cs_mode | cs_endian)
    cs.detail = True
    page_start = align_address_to_page(location)
    offset = location - page_start

    skip = int(kwargs.get("skip", 0))
    nb_prev = int(kwargs.get("nb_prev", 0))
    pc = gef.arch.pc
    if nb_prev > 0:
        location = gdb_get_nth_previous_instruction_address(pc, nb_prev) or -1
        if location < 0:
            err(f"failed to read previous instruction")
            return
        nb_insn += nb_prev

    code = kwargs.get(
        "code", gef.memory.read(location, gef.session.pagesize - offset - 1)
    )
    for insn in cs.disasm(code, location):
        if skip:
            skip -= 1
            continue
        nb_insn -= 1
        yield cs_insn_to_gef_insn(insn)
        if nb_insn == 0:
            break
    return


@register
class CapstoneDisassembleCommand(GenericCommand):
    """Use capstone disassembly framework to disassemble code."""

    _cmdline_ = "capstone-disassemble"
    _syntax_ = f"{_cmdline_} [-h] [--show-opcodes] [--length LENGTH] [LOCATION]"
    _aliases_ = ["cs-dis"]
    _example_ = f"{_cmdline_} --length 50 $pc"

    def __init__(self) -> None:
        super().__init__(complete=gdb.COMPLETE_LOCATION)
        gef.config[f"{self._cmdline_}.use-capstone"] = GefSetting(
            False,
            bool,
            "Replace the GDB disassembler in the `context` with Capstone",
            hooks={
                "on_write": [
                    self.switch_disassembler,
                ]
            },
        )
        self.__original_disassembler: Optional[
            Callable[[int, int, Any], Generator[Instruction, None, None]]
        ] = None
        return

    def switch_disassembler(self, _) -> None:
        ctx = gef.gdb.commands["context"]
        assert isinstance(ctx, ContextCommand)
        if gef.config[f"{self._cmdline_}.use-capstone"]:
            self.__original_disassembler = ctx.instruction_iterator
            ctx.instruction_iterator = cs_disassemble
        else:
            # `use-capstone` set to False
            if (
                ctx.instruction_iterator == cs_disassemble
                and self.__original_disassembler
            ):
                # restore the original
                ctx.instruction_iterator = self.__original_disassembler
        return

    def __del__(self):
        ctx = gef.gdb.commands["context"]
        assert isinstance(ctx, ContextCommand)
        if ctx.instruction_iterator == cs_disassemble and self.__original_disassembler:
            ctx.instruction_iterator = self.__original_disassembler
        return

    @only_if_gdb_running
    @parse_arguments(
        {("location"): "$pc"}, {("--show-opcodes", "-s"): False, "--length": 0}
    )
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
        for insn in cs_disassemble(
            location, length, skip=length * self.repeat_count, **kwargs
        ):
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
            for i, new_insn in enumerate(cs_disassemble(target_address, nb_insn)):
                msg.append(f"   {DOWN_ARROW if i == 0 else ' '}  {new_insn!s}")
            return (True, "\n".join(msg))

        return (False, "")
