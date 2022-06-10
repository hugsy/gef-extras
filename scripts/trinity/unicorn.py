
import sys
import os
from typing import Dict, Optional, Tuple, Union

import capstone
import unicorn


def get_arch(arch: Optional[str] = None, mode: Optional[str] = None, endian: Optional[bool] = None, to_string: bool = False) -> Union[Tuple[None, None], Tuple[str, Union[int, str]]]:
    unicorn = sys.modules["unicorn"]
    if (arch, mode, endian) == (None, None, None):
        return get_generic_running_arch(unicorn, "UC", to_string)
    return get_generic_arch(unicorn, "UC", arch, mode, endian, to_string)


def get_registers(to_string: bool = False) -> Union[Dict[str, int], Dict[str, str]]:
    "Return a dict matching the Unicorn identifier for a specific register."
    unicorn = sys.modules["unicorn"]
    regs = {}

    if gef.arch is not None:
        arch = gef.arch.arch.lower()
    else:
        raise OSError("Oops")

    const = getattr(unicorn, f"{arch}_const")
    for reg in gef.arch.all_registers:
        regname = f"UC_{arch.upper()}_REG_{reg[1:].upper()}"
        if to_string:
            regs[reg] = f"{const.__name__}.{regname}"
        else:
            regs[reg] = getattr(const, regname)
    return regs


class UnicornEmulateCommand(GenericCommand):
    """Use Unicorn-Engine to emulate the behavior of the binary, without affecting the GDB runtime.
    By default the command will emulate only the next instruction, but location and number of
    instruction can be changed via arguments to the command line. By default, it will emulate
    the next instruction from current PC."""

    _cmdline_ = "unicorn-emulate"
    _syntax_ = (f"{_cmdline_} [--start LOCATION] [--until LOCATION] [--skip-emulation] [--output-file PATH] [NB_INSTRUCTION]"
                "\n\t--start LOCATION specifies the start address of the emulated run (default $pc)."
                "\t--until LOCATION specifies the end address of the emulated run."
                "\t--skip-emulation\t do not execute the script once generated."
                "\t--output-file /PATH/TO/SCRIPT.py writes the persistent Unicorn script into this file."
                "\tNB_INSTRUCTION indicates the number of instructions to execute"
                "\nAdditional options can be setup via `gef config unicorn-emulate`")
    _aliases_ = ["emulate", ]
    _example_ = f"{_cmdline_} --start $pc 10 --output-file /tmp/my-gef-emulation.py"

    def __init__(self) -> None:
        super().__init__(complete=gdb.COMPLETE_LOCATION)
        self["verbose"] = (False, "Set unicorn-engine in verbose mode")
        self["show_disassembly"] = (False, "Show every instruction executed")
        return

    @only_if_gdb_running
    @parse_arguments({"nb": 1}, {"--start": "", "--until": "", "--skip-emulation": True, "--output-file": ""})
    def do_invoke(self, _: List[str], **kwargs: Any) -> None:
        args = kwargs["arguments"]
        start_address = parse_address(str(args.start or gef.arch.pc))
        end_address = parse_address(
            str(args.until or self.get_unicorn_end_addr(start_address, args.nb)))
        self.run_unicorn(start_address, end_address,
                         skip_emulation=args.skip_emulation, to_file=args.output_file)
        return

    def get_unicorn_end_addr(self, start_addr: int, nb: int) -> int:
        dis = list(gef_disassemble(start_addr, nb + 1))
        last_insn = dis[-1]
        return last_insn.address

    def run_unicorn(self, start_insn_addr: int, end_insn_addr: int, **kwargs: Any) -> None:
        verbose = self["verbose"] or False
        skip_emulation = kwargs.get("skip_emulation", False)
        arch, mode = get_unicorn_arch(to_string=True)
        unicorn_registers = get_unicorn_registers(to_string=True)
        cs_arch, cs_mode = get_capstone_arch(to_string=True)
        fname = gef.session.file.name
        to_file = kwargs.get("to_file", None)
        emulate_segmentation_block = ""
        context_segmentation_block = ""

        if to_file:
            tmp_filename = to_file
            to_file = open(to_file, "w")
            tmp_fd = to_file.fileno()
        else:
            tmp_fd, tmp_filename = tempfile.mkstemp(
                suffix=".py", prefix="gef-uc-")

        if is_x86():
            # need to handle segmentation (and pagination) via MSR
            emulate_segmentation_block = """
# from https://github.com/unicorn-engine/unicorn/blob/master/tests/regress/x86_64_msr.py
SCRATCH_ADDR = 0xf000
SEGMENT_FS_ADDR = 0x5000
SEGMENT_GS_ADDR = 0x6000
FSMSR = 0xC0000100
GSMSR = 0xC0000101

def set_msr(uc, msr, value, scratch=SCRATCH_ADDR):
    buf = b"\\x0f\\x30"  # x86: wrmsr
    uc.mem_map(scratch, 0x1000)
    uc.mem_write(scratch, buf)
    uc.reg_write(unicorn.x86_const.UC_X86_REG_RAX, value & 0xFFFFFFFF)
    uc.reg_write(unicorn.x86_const.UC_X86_REG_RDX, (value >> 32) & 0xFFFFFFFF)
    uc.reg_write(unicorn.x86_const.UC_X86_REG_RCX, msr & 0xFFFFFFFF)
    uc.emu_start(scratch, scratch+len(buf), count=1)
    uc.mem_unmap(scratch, 0x1000)
    return

def set_gs(uc, addr):    return set_msr(uc, GSMSR, addr)
def set_fs(uc, addr):    return set_msr(uc, FSMSR, addr)

"""

            context_segmentation_block = """
    emu.mem_map(SEGMENT_FS_ADDR-0x1000, 0x3000)
    set_fs(emu, SEGMENT_FS_ADDR)
    set_gs(emu, SEGMENT_GS_ADDR)
"""

        content = """#!{pythonbin} -i
#
# Emulation script for "{fname}" from {start:#x} to {end:#x}
#
# Powered by gef, unicorn-engine, and capstone-engine
#
# @_hugsy_
#
import collections
import capstone, unicorn

registers = collections.OrderedDict(sorted({{{regs}}}.items(), key=lambda t: t[0]))
uc = None
verbose = {verbose}
syscall_register = "{syscall_reg}"

def disassemble(code, addr):
    cs = capstone.Cs({cs_arch}, {cs_mode})
    for i in cs.disasm(code, addr):
        return i

def hook_code(emu, address, size, user_data):
    code = emu.mem_read(address, size)
    insn = disassemble(code, address)
    print(">>> {{:#x}}: {{:s}} {{:s}}".format(insn.address, insn.mnemonic, insn.op_str))
    return

def code_hook(emu, address, size, user_data):
    code = emu.mem_read(address, size)
    insn = disassemble(code, address)
    print(">>> {{:#x}}: {{:s}} {{:s}}".format(insn.address, insn.mnemonic, insn.op_str))
    return

def intr_hook(emu, intno, data):
    print(" \\-> interrupt={{:d}}".format(intno))
    return

def syscall_hook(emu, user_data):
    sysno = emu.reg_read(registers[syscall_register])
    print(" \\-> syscall={{:d}}".format(sysno))
    return

def print_regs(emu, regs):
    for i, r in enumerate(regs):
        print("{{:7s}} = {{:#0{ptrsize}x}}  ".format(r, emu.reg_read(regs[r])), end="")
        if (i % 4 == 3) or (i == len(regs)-1): print("")
    return

{emu_block}

def reset():
    emu = unicorn.Uc({arch}, {mode})

{context_block}
""".format(pythonbin=PYTHONBIN, fname=fname, start=start_insn_addr, end=end_insn_addr,
           regs=",".join(
               [f"'{k.strip()}': {unicorn_registers[k]}" for k in unicorn_registers]),
           verbose="True" if verbose else "False",
           syscall_reg=gef.arch.syscall_register,
           cs_arch=cs_arch, cs_mode=cs_mode,
           ptrsize=gef.arch.ptrsize * 2 + 2,  # two hex chars per byte plus "0x" prefix
           emu_block=emulate_segmentation_block if is_x86() else "",
           arch=arch, mode=mode,
           context_block=context_segmentation_block if is_x86() else "")

        if verbose:
            info("Duplicating registers")

        for r in gef.arch.all_registers:
            gregval = gef.arch.register(r)
            content += f"    emu.reg_write({unicorn_registers[r]}, {gregval:#x})\n"

        vmmap = gef.memory.maps
        if not vmmap:
            warn("An error occurred when reading memory map.")
            return

        if verbose:
            info("Duplicating memory map")

        for sect in vmmap:
            if sect.path == "[vvar]":
                # this section is for GDB only, skip it
                continue

            page_start = sect.page_start
            page_end = sect.page_end
            size = sect.size
            perm = sect.permission

            content += f"    # Mapping {sect.path}: {page_start:#x}-{page_end:#x}\n"
            content += f"    emu.mem_map({page_start:#x}, {size:#x}, {perm.value:#o})\n"

            if perm & Permission.READ:
                code = gef.memory.read(page_start, size)
                loc = f"/tmp/gef-{fname}-{page_start:#x}.raw"
                with open(loc, "wb") as f:
                    f.write(bytes(code))

                content += f"    emu.mem_write({page_start:#x}, open('{loc}', 'rb').read())\n"
                content += "\n"

        content += "    emu.hook_add(unicorn.UC_HOOK_CODE, code_hook)\n"
        content += "    emu.hook_add(unicorn.UC_HOOK_INTR, intr_hook)\n"
        if is_x86_64():
            content += "    emu.hook_add(unicorn.UC_HOOK_INSN, syscall_hook, None, 1, 0, unicorn.x86_const.UC_X86_INS_SYSCALL)\n"
        content += "    return emu\n"

        content += """
def emulate(emu, start_addr, end_addr):
    print("========================= Initial registers =========================")
    print_regs(emu, registers)

    try:
        print("========================= Starting emulation =========================")
        emu.emu_start(start_addr, end_addr)
    except Exception as e:
        emu.emu_stop()
        print("========================= Emulation failed =========================")
        print("[!] Error: {{}}".format(e))

    print("========================= Final registers =========================")
    print_regs(emu, registers)
    return


uc = reset()
emulate(uc, {start:#x}, {end:#x})

# unicorn-engine script generated by gef
""".format(start=start_insn_addr, end=end_insn_addr)

        os.write(tmp_fd, gef_pybytes(content))
        os.close(tmp_fd)

        if kwargs.get("to_file", None):
            info(f"Unicorn script generated as '{tmp_filename}'")
            os.chmod(tmp_filename, 0o700)

        if skip_emulation:
            return

        ok(f"Starting emulation: {start_insn_addr:#x} {RIGHT_ARROW} {end_insn_addr:#x}")

        res = gef_execute_external([PYTHONBIN, tmp_filename], as_list=True)
        gef_print("\n".join(res))

        if not kwargs.get("to_file", None):
            os.unlink(tmp_filename)
        return
