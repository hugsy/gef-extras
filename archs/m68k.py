"""
M68K support for GEF

To use, source this file *after* gef

Original PR: https://github.com/hugsy/gef/pull/453
Author: zhuyifei1999
"""

class M68K(Architecture):
    arch = "M68K"
    mode = ""

    nop_insn = b"\x4e\x71"
    flag_register = "$ps"
    all_registers = ["$d0", "$d1", "$d2", "$d3", "$d4", "$d5", "$d6", "$d7",
                     "$a0", "$a1", "$a2", "$a3", "$a4", "$a5", "$fp", "$sp",
                     "$ps", "$pc"]
    instruction_length = None
    return_register = "$d0"
    function_parameters = ["$sp", ]
    flags_table = {
        0: "carry",
        1: "overflow",
        2: "zero",
        3: "negative",
        4: "extend",
        12: "master",
        13: "supervisor",
    }
    syscall_register = "$d0"
    syscall_instructions = ["trap #0"]

    def flag_register_to_human(self, val=None):
        reg = self.flag_register
        if not val:
            val = get_register(reg)
        return flags_to_human(val, self.flags_table)

    def is_call(self, insn):
        mnemo = insn.mnemonic
        call_mnemos = {"jsr", "bsrb", "bsrw", "bsrl"}
        return mnemo in call_mnemos

    def is_ret(self, insn):
        return insn.mnemonic == "rts"

    def is_conditional_branch(self, insn):
        mnemo = insn.mnemonic
        branch_mnemos = {
            "bccb", "bcsb", "beqb", "bgeb", "bgtb", "bhib", "bleb",
            "blsb", "bltb", "bmib", "bneb", "bplb", "bvcb", "bvsb",
            "bccw", "bcsw", "beqw", "bgew", "bgtw", "bhiw", "blew",
            "blsw", "bltw", "bmiw", "bnew", "bplw", "bvcw", "bvsw",
            "bccl", "bcsl", "beql", "bgel", "bgtl", "bhil", "blel",
            "blsl", "bltl", "bmil", "bnel", "bpll", "bvcl", "bvsl",
        }
        return mnemo in branch_mnemos

    def is_branch_taken(self, insn):
        mnemo = insn.mnemonic
        flags = dict((self.flags_table[k], k) for k in self.flags_table)
        val = get_register(self.flag_register)

        taken, reason = False, ""

        if mnemo in ("bccs", "bccw", "bccl"):
            taken, reason = not val&(1<<flags["carry"]), "!C"
        elif mnemo in ("bcss", "bcsw", "bcsl"):
            taken, reason = val&(1<<flags["carry"]), "C"
        elif mnemo in ("beqs", "beqw", "beql"):
            taken, reason = val&(1<<flags["zero"]), "Z"
        elif mnemo in ("bges", "bgew", "bgel"):
            taken, reason = bool(val&(1<<flags["negative"])) == bool(val&(1<<flags["overflow"])), "N==O"
        elif mnemo in ("bgts", "bgtw", "bgtl"):
            taken, reason = not val&(1<<flags["zero"]) and bool(val&(1<<flags["overflow"])) == bool(val&(1<<flags["negative"])), "!Z && N==O"
        elif mnemo in ("bhis", "bhiw", "bhil"):
            taken, reason = not val&(1<<flags["carry"]) and not val&(1<<flags["zero"]), "!C && !Z"
        elif mnemo in ("bles", "blew", "blel"):
            taken, reason = val&(1<<flags["zero"]) or bool(val&(1<<flags["overflow"])) != bool(val&(1<<flags["negative"])), "Z || N!=O"
        elif mnemo in ("blss", "blsw", "blsl"):
            taken, reason = val&(1<<flags["carry"]) or val&(1<<flags["zero"]), "C || Z"
        elif mnemo in ("blts", "bltw", "bltl"):
            taken, reason = val&(1<<flags["overflow"]) != val&(1<<flags["negative"]), "N!=O"
        elif mnemo in ("bmis", "bmiw", "bmil"):
            taken, reason = val&(1<<flags["negative"]), "N"
        elif mnemo in ("bnes", "bnew", "bnel"):
            taken, reason = not val&(1<<flags["zero"]), "!Z"
        elif mnemo in ("bpls", "bplw", "bpll"):
            taken, reason = not val&(1<<flags["negative"]), "!N"
        elif mnemo in ("bvcs", "bvcw", "bvcl"):
            taken, reason = not val&(1<<flags["overflow"]), "!O"
        elif mnemo in ("bvss", "bvsw", "bvsl"):
            taken, reason = val&(1<<flags["overflow"]), "O"
        return taken, reason

    def get_ra(self, insn, frame):
        ra = None
        if self.is_ret(insn):
            ra = to_unsigned_long(dereference(current_arch.sp))
        if frame.older():
            ra = frame.older().pc()
        return ra

    @classmethod
    def mprotect_asm(cls, addr, size, perm):
        raise NotImplementedError()

SUPPORTED_ARCHITECTURES["M68K"] = (M68K, Elf.M68K: M68K)
