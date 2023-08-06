"""
PE format support

To use:

```
gef➤  source /path/to/gef-extras/os/pe.py
gef➤  pi gef.binary = PE(get_filepath())
gef➤  pi reset_architecture()
```
"""

import enum
import os
import pathlib
import struct

from functools import lru_cache
from typing import Dict, Tuple, Any, Optional

class PE:
    """Basic PE parsing.
    Ref:
    - https://hshrzd.wordpress.com/pe-bear/
    - https://blog.kowalczyk.info/articles/pefileformat.html
    """
    class Constants(enum.IntEnum):
        DOS_MAGIC           = 0x4D5A
        NT_MAGIC            = 0x4550

    class MachineType(enum.IntEnum):
        X86_64              = 0x8664
        X86_32              = 0x14c
        ARM                 = 0x1c0
        ARM64               = 0xaa64

    class DosHeader:
        e_magic : int
        e_cblp : int
        e_cp : int
        e_crlc : int
        e_cparhdr : int
        e_minalloc : int
        e_maxalloc : int
        e_ss : int
        e_sp : int
        e_csum : int
        e_ip : int
        e_cs : int
        e_lfarlc : int
        e_ovno : int
        e_res : bytes
        e_oemid : int
        e_oeminfo : int
        e_res2 : bytes
        e_lfanew : int

    class ImageFileHeader:
        Machine: "PE.MachineType"
        NumberOfSections: int
        TimeDateStamp: int
        PointerToSymbolTable: int
        NumberOfSymbols: int
        SizeOfOptionalHeader: int
        Characteristics: "PE.DllCharacteristics"

    class OptionalHeader:
        Magic: int
        MajorLinkerVersion: int
        MinorLinkerVersion: int
        SizeOfCode: int
        SizeOfInitializedData: int
        SizeOfUninitializedData: int
        AddressOfEntryPoint: int
        BaseOfCode: int
        BaseOfData: int
        ImageBase: int
        SectionAlignment: int
        FileAlignment: int
        MajorOperatingSystemVersion: int
        MinorOperatingSystemVersion: int
        MajorImageVersion: int
        MinorImageVersion: int
        MajorSubsystemVersion: int
        MinorSubsystemVersion: int
        Reserved1: int
        SizeOfImage: int
        SizeOfHeaders: int
        CheckSum: int
        Subsystem: int
        DllCharacteristics: int
        SizeOfStackReserve: int
        SizeOfStackCommit: int
        SizeOfHeapReserve: int
        SizeOfHeapCommit: int
        LoaderFlags: int
        NumberOfRvaAndSizes: int
        DataDirectory: Tuple["PE.DataDirectory"]

    class DataDirectory:
        VirtualAddress: int
        Size: int

    class DllCharacteristics(enum.IntFlag):
        IMAGE_FILE_RELOCS_STRIPPED = 0x0001
        IMAGE_FILE_EXECUTABLE_IMAGE = 0x0002
        IMAGE_FILE_LINE_NUMS_STRIPPED = 0x0004
        IMAGE_FILE_LOCAL_SYMS_STRIPPED = 0x0008
        IMAGE_FILE_AGGRESSIVE_WS_TRIM = 0x0010
        IMAGE_FILE_LARGE_ADDRESS_AWARE = 0x0020
        IMAGE_FILE_BYTES_REVERSED_LO = 0x0080
        IMAGE_FILE_32BIT_MACHINE = 0x0100
        IMAGE_FILE_DEBUG_STRIPPED = 0x0200
        IMAGE_FILE_REMOVABLE_RUN_FROM_SWAP = 0x0400
        IMAGE_FILE_NET_RUN_FROM_SWAP = 0x0800
        IMAGE_FILE_SYSTEM = 0x1000
        IMAGE_FILE_DLL = 0x2000
        IMAGE_FILE_UP_SYSTEM_ONLY = 0x4000
        IMAGE_FILE_BYTES_REVERSED_HI = 0x8000

        def __str__(self) -> str:
            return super().__str__().lstrip(self.__class__.__name__+".")

    dos : DosHeader
    file_header : ImageFileHeader
    optional_header: OptionalHeader
    entry_point : int

    def __init__(self, pe: str) -> None:
        self.fpath = pathlib.Path(pe).expanduser().resolve()

        if not os.access(self.fpath, os.R_OK):
            raise FileNotFoundError(f"'{self.fpath}' not found/readable, most gef features will not work")

        endian = gef.arch.endianness
        with self.fpath.open("rb") as self.fd:
            # Parse IMAGE_DOS_HEADER
            self.dos = self.DosHeader()

            self.dos.e_magic = self.read_and_unpack("!H")[0]
            if self.dos.e_magic != PE.Constants.DOS_MAGIC:
                raise Exception(f"Corrupted PE file (bad DOS magic, expected '{PE.Constants.DOS_MAGIC:x}', got '{self.dos.e_magic:x}'")

            self.fd.seek(0x3c, 0)
            self.dos.e_lfanew = u32(self.fd.read(4))

            self.fd.seek(self.dos.e_lfanew, 0)
            pe_magic = u32(self.fd.read(4))
            if pe_magic != PE.Constants.NT_MAGIC:
                raise Exception("Corrupted PE file (bad PE magic)")

            # Parse IMAGE_FILE_HEADER
            self.file_header = self.ImageFileHeader()

            machine, self.file_header.NumberOfSections = self.read_and_unpack(f"{endian}HH")
            self.file_header.Machine = PE.MachineType(machine)

            self.file_header.TimeDateStamp, self.file_header.PointerToSymbolTable, \
                self.file_header.NumberOfSymbols, self.file_header.SizeOfOptionalHeader, \
                dll_characteristics = self.read_and_unpack(f"{endian}IIIHH")

            self.file_header.Characteristics = PE.DllCharacteristics(dll_characteristics)

            # Parse IMAGE_OPTIONAL_HEADER
            self.optional_header = self.OptionalHeader()

            self.fd.seek(0x10, 1)

            self.optional_header.AddressOfEntryPoint, self.optional_header.BaseOfCode,\
            self.optional_header.BaseOfData, self.optional_header.ImageBase = self.read_and_unpack(f"{endian}IIII")

            self.entry_point = self.optional_header.AddressOfEntryPoint
        return

    def __str__(self) -> str:
        return f"PE('{self.fpath.absolute()}', {self.file_header.Machine.name}, {str(self.file_header.Characteristics)})"

    def read_and_unpack(self, fmt: str) -> Tuple[Any, ...]:
        size = struct.calcsize(fmt)
        data = self.fd.read(size)
        return struct.unpack(fmt, data)

#
# redirect calls
#
@lru_cache()
def get_elf_headers(filename: str = None) -> PE:
    """Return an PE object with info from `filename`. If not provided, will return
    the currently debugged file."""
    return PE(filename) if filename else PE(str(gef.session.file.absolute()))


def checksec(filename: str) -> Dict[str, bool]:
    warn("`checksec` doesn't apply for PE files")
    return {"Canary": False, "NX": False, "PIE": False, "Fortify": False}


elf_reset_architecture = reset_architecture

def pe_reset_architecture(arch: Optional[str] = None, default: Optional[str] = None) -> None:
    if gef.binary.file_header.Machine == PE.MachineType.X86_32:
        gef.arch = __registered_architectures__.get(Elf.Abi.X86_32)()
    elif gef.binary.file_header.Machine == PE.MachineType.X86_64:
        gef.arch = __registered_architectures__.get(Elf.Abi.X86_64)()
    else:
        raise Exception("unknown architecture")
    return

def reset_architecture(arch: Optional[str] = None, default: Optional[str] = None) -> None:
    if isinstance(gef.binary, PE):
        pe_reset_architecture(arch, default)
    elif isinstance(gef.binary, ELF):
        elf_reset_architecture(arch, default)
    else:
        raise Exception("unknown architecture")
    return

