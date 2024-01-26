"""
ARM through OpenOCD support for GEF

To use, source this file *after* gef

Author: Grazfather
"""

class ARMOpenOCD(ARM):
    arch = "ARMOpenOCD"
    aliases = ("ARMOpenOCD",)
    all_registers = ("$r0", "$r1", "$r2", "$r3", "$r4", "$r5", "$r6",
                     "$r7", "$r8", "$r9", "$r10", "$r11", "$r12", "$sp",
                     "$lr", "$pc", "$xPSR")
    flag_register = "$xPSR"
    @staticmethod
    def supports_gdb_arch(arch: str) -> Optional[bool]:
        if "arm" in arch and arch.endswith("-m"):
            return True
        return None
