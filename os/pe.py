import struct
import os


current_pe = None


class PE:
    """Basic PE parsing.
    Ref:
    - https://hshrzd.wordpress.com/pe-bear/
    - https://blog.kowalczyk.info/articles/pefileformat.html
    """
    X86_64              = 0x8664
    X86_32              = 0x14c
    ARM                 = 0x1c0
    ARM64               = 0xaa64
    ARMNT               = 0x1c4
    AM33                = 0x1d3
    IA64                = 0x200
    EFI                 = 0xebc
    MIPS                = 0x166
    MIPS16              = 0x266
    MIPSFPU             = 0x366
    MIPSFPU16           = 0x466
    WCEMIPSV2           = 0x169
    POWERPC             = 0x1f0
    POWERPCFP           = 0x1f1
    SH3                 = 0x1a2
    SH3DSP              = 0x1a3
    SH4                 = 0x1a6
    SH5                 = 0x1a8
    THUMP               = 0x1c2
    RISCV32             = 0x5032
    RISCV64             = 0x5064
    RISCV128            = 0x5128
    M32R                = 0x9041

    dos_magic           = b'MZ'
    ptr_to_pe_header    = None
    pe_magic            = b'PE'
    machine             = X86_32
    num_of_sections     = None
    size_of_opt_header  = None
    dll_charac          = None
    opt_magic           = b'\x02\x0b'
    entry_point         = None
    base_of_code        = None
    image_base          = None


    def __init__(self, pe=""):
        if not os.access(pe, os.R_OK):
            err("'{0}' not found/readable".format(pe))
            err("Failed to get file debug information, most of gef features will not work")
            return

        with open(pe, "rb") as fd:
            # off 0x0
            self.dos_magic = fd.read(2)
            if self.dos_magic != PE.dos_magic:
                self.machine = None
                return

            # off 0x3c
            fd.seek(0x3c)
            self.ptr_to_pe_header, = struct.unpack("<I", fd.read(4))
            # off_pe + 0x0
            fd.seek(self.ptr_to_pe_header)
            self.pe_magic = fd.read(2)
            # off_pe + 0x4
            fd.seek(self.ptr_to_pe_header + 0x4)
            self.machine, self.num_of_sections = struct.unpack("<HH", fd.read(4))
            # off_pe + 0x14
            fd.seek(self.ptr_to_pe_header + 0x14)
            self.size_of_opt_header, self.dll_charac = struct.unpack("<HH", fd.read(4))
            # off_pe + 0x18
            self.opt_magic = fd.read(2)
            # off_pe + 0x28
            fd.seek(self.ptr_to_pe_header + 0x28)
            self.entry_point, self.base_of_code = struct.unpack("<II", fd.read(8))
            # off_pe + 0x30
            self.image_base, = struct.unpack("<I", fd.read(4))
        return

    def is_valid(self):
        return self.dos_magic == PE.DOS_MAGIC and self.pe_magic == PE.pe_magic

    def get_machine_name(self):
        return {
            0x14c: "X86",
            0x166: "MIPS",
            0x169: "WCEMIPSV2",
            0x1a2: "SH3",
            0x1a3: "SH3DSP",
            0x1a6: "SH4",
            0x1a8: "SH5",
            0x1c0: "ARM",
            0x1c2: "THUMP",
            0x1c4: "ARMNT",
            0x1d3: "AM33",
            0x1f0: "PowerPC",
            0x1f1: "PowerPCFP",
            0x200: "IA64",
            0x266: "MIPS16",
            0x366: "MIPSFPU",
            0x466: "MIPSFPU16",
            0xebc: "EFI",
            0x5032: "RISCV32",
            0x5064: "RISCV64",
            0x5128: "RISCV128",
            0x8664: "X86_64",
            0x9041: "M32R",
            0xaa64: "ARM64",
            None: None
        }[self.machine]



@lru_cache()
def get_pe_headers(filename=None):
    """Return an PE object with info from `filename`. If not provided, will return
    the currently debugged file."""
    if filename is None:
        filename = get_filepath()

    if filename.startswith("target:"):
        warn("Your file is remote, you should try using `gef-remote` instead")
        return

    return PE(filename)


@lru_cache()
def is_pe64(filename=None):
    """Checks if `filename` is an PE64."""
    pe = current_pe or get_pe_headers(filename)
    return pe.machine == PE.X86_64


@lru_cache()
def is_pe32(filename=None):
    """Checks if `filename` is an PE32."""
    pe = current_pe or get_pe_headers(filename)
    return pe.machine == PE.X86_32