"""
PE format support

To use:

```
gef➤  source /path/to/gef-extras/os/pe.py
```
"""


__AUTHOR__ = "hugsy"
__VERSION__ = 0.2
__LICENSE__ = "MIT"


import collections
import enum
import pathlib
import struct
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from ..scripts import *
    from ..scripts import gdb


class Pe(FileFormat):
    """Basic PE parsing."""

    class Constants(enum.IntEnum):
        DOS_MAGIC = 0x4d5a
        NT_MAGIC = 0x50450000

    class MachineType(enum.IntEnum):
        UNKNOWN = 0
        I386 = 332
        R4000 = 358
        WCEMIPSV2 = 361
        ALPHA = 388
        SH3 = 418
        SH3DSP = 419
        SH4 = 422
        SH5 = 424
        ARM = 448
        THUMB = 450
        ARMNT = 452
        AM33 = 467
        POWERPC = 496
        POWERPCFP = 497
        IA64 = 512
        MIPS16 = 614
        MIPSFPU = 870
        MIPSFPU16 = 1126
        EBC = 3772
        RISCV32 = 20530
        RISCV64 = 20580
        RISCV128 = 20776
        AMD64 = 34404
        M32R = 36929
        ARM64 = 43620

    class DosHeader:
        e_magic: int
        e_cblp: int
        e_cp: int
        e_crlc: int
        e_cparhdr: int
        e_minalloc: int
        e_maxalloc: int
        e_ss: int
        e_sp: int
        e_csum: int
        e_ip: int
        e_cs: int
        e_lfarlc: int
        e_ovno: int
        e_res: bytes
        e_oemid: int
        e_oeminfo: int
        e_res2: bytes
        e_lfanew: int

    class ImageFileHeader:
        Machine: "Pe.MachineType"
        NumberOfSections: int
        TimeDateStamp: int
        PointerToSymbolTable: int
        NumberOfSymbols: int
        SizeOfOptionalHeader: int
        Characteristics: "Pe.FileCharacteristics"

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
        DataDirectory: Tuple["Pe.DataDirectory"]

    class DataDirectory:
        VirtualAddress: int
        Size: int

    class ImageSectionHeader(FileFormatSection):
        Name: bytes
        VirtualSize: int
        VirtualAddress: int
        SizeOfRawData: int
        PointerToRawData: int
        PointerToRelocations: int
        PointerToLinenumbers: int
        NumberOfRelocations: int
        NumberOfLinenumbers: int
        Characteristics: "Pe.ImageSectionFlags"

        def __str__(self) -> str:
            return f"{self.Name}, VA={self.VirtualAddress:#x}, Size={self.SizeOfRawData:#x} Flags={str(self.Characteristics)}"

    class FileCharacteristics(enum.IntFlag):
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

    class DllCharacteristics(enum.IntFlag):
        IMAGE_LIBRARY_PROCESS_INIT = 0x0001
        IMAGE_LIBRARY_PROCESS_TERM = 0x0002
        IMAGE_LIBRARY_THREAD_INIT = 0x0004
        IMAGE_LIBRARY_THREAD_TERM = 0x0008
        IMAGE_DLLCHARACTERISTICS_10h = 0x0010
        IMAGE_DLLCHARACTERISTICS_20h = 0x0020
        IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE = 0x0040
        IMAGE_DLLCHARACTERISTICS_FORCE_INTEGRITY = 0x0080
        IMAGE_DLLCHARACTERISTICS_NX_COMPAT = 0x0100
        IMAGE_DLLCHARACTERISTICS_NO_ISOLATION = 0x0200
        IMAGE_DLLCHARACTERISTICS_NO_SEH = 0x0400
        IMAGE_DLLCHARACTERISTICS_NO_BIND = 0x0800
        IMAGE_DLLCHARACTERISTICS_1000h = 0x1000
        IMAGE_DLLCHARACTERISTICS_WDM_DRIVER = 0x2000
        IMAGE_DLLCHARACTERISTICS_4000h = 0x4000
        IMAGE_DLLCHARACTERISTICS_TERMINAL_SERVER_AWARE = 0x8000

        def __str__(self) -> str:
            return super().__str__().lstrip(self.__class__.__name__+".")

    class ImageSectionFlags(enum.IntFlag):
        IMAGE_SCN_TYPE_NO_PAD = 0x00000008
        IMAGE_SCN_CNT_CODE = 0x00000020
        IMAGE_SCN_CNT_INITIALIZED_DATA = 0x00000040
        IMAGE_SCN_CNT_UNINITIALIZED_DATA = 0x00000080
        IMAGE_SCN_LNK_OTHER = 0x00000100
        IMAGE_SCN_LNK_INFO = 0x00000200
        IMAGE_SCN_LNK_REMOVE = 0x00000800
        IMAGE_SCN_LNK_COMDAT = 0x00001000
        IMAGE_SCN_GPREL = 0x00008000
        IMAGE_SCN_MEM_PURGEABLE = 0x00020000
        IMAGE_SCN_MEM_16BIT = 0x00020000
        IMAGE_SCN_MEM_LOCKED = 0x00040000
        IMAGE_SCN_MEM_PRELOAD = 0x00080000
        IMAGE_SCN_ALIGN_1BYTES = 0x00100000
        IMAGE_SCN_ALIGN_2BYTES = 0x00200000
        IMAGE_SCN_ALIGN_4BYTES = 0x00300000
        IMAGE_SCN_ALIGN_8BYTES = 0x00400000
        IMAGE_SCN_ALIGN_16BYTES = 0x00500000
        IMAGE_SCN_ALIGN_32BYTES = 0x00600000
        IMAGE_SCN_ALIGN_64BYTES = 0x00700000
        IMAGE_SCN_ALIGN_128BYTES = 0x00800000
        IMAGE_SCN_ALIGN_256BYTES = 0x00900000
        IMAGE_SCN_ALIGN_512BYTES = 0x00A00000
        IMAGE_SCN_ALIGN_1024BYTES = 0x00B00000
        IMAGE_SCN_ALIGN_2048BYTES = 0x00C00000
        IMAGE_SCN_ALIGN_4096BYTES = 0x00D00000
        IMAGE_SCN_ALIGN_8192BYTES = 0x00E00000
        IMAGE_SCN_LNK_NRELOC_OVFL = 0x01000000
        IMAGE_SCN_MEM_DISCARDABLE = 0x02000000
        IMAGE_SCN_MEM_NOT_CACHED = 0x04000000
        IMAGE_SCN_MEM_NOT_PAGED = 0x08000000
        IMAGE_SCN_MEM_SHARED = 0x10000000
        IMAGE_SCN_MEM_EXECUTE = 0x20000000
        IMAGE_SCN_MEM_READ = 0x40000000
        IMAGE_SCN_MEM_WRITE = 0x80000000

    dos: DosHeader
    file_header: ImageFileHeader
    optional_header: OptionalHeader
    name: str = "PE"
    __sections: List[FileFormatSection]
    __entry_point: Optional[int] = None
    __checksec: Dict[str, bool]

    def __init__(self, path: Union[str, pathlib.Path]) -> None:
        """Instantiate a PE object. A valid PE must be provided, or an exception will be thrown."""

        if isinstance(path, str):
            self.path = pathlib.Path(path).expanduser()
        elif isinstance(path, pathlib.Path):
            self.path = path
        else:
            raise TypeError

        if not self.path.exists():
            raise FileNotFoundError(
                f"'{self.path}' not found/readable, most gef features will not work")

        self.__checksec = {}

        endian = gef.arch.endianness
        with self.path.open("rb") as self.fd:
            # Parse IMAGE_DOS_HEADER
            self.dos = self.DosHeader()
            self.dos.e_magic = self.read_and_unpack("!H")[0]
            if self.dos.e_magic != Pe.Constants.DOS_MAGIC:
                raise RuntimeError(
                    f"Corrupted DOS file (bad DOS magic, expected '{Pe.Constants.DOS_MAGIC:x}', got '{self.dos.e_magic:x}'")

            self.seek(0x3c)
            self.dos.e_lfanew = self.read_and_unpack(f"{endian}H")[0]

            self.seek(self.dos.e_lfanew)
            pe_magic = self.read_and_unpack("!I")[0]
            if pe_magic != Pe.Constants.NT_MAGIC:
                raise RuntimeError("Corrupted PE file (bad PE magic)")

            # Parse IMAGE_FILE_HEADER
            self.file_header = self.ImageFileHeader()
            offsetImageFileHeader = self.fd.seek(0, 1)
            sizeOfImageFileHeader = struct.calcsize("HHIIIHH")

            machine, \
                self.file_header.NumberOfSections, \
                self.file_header.TimeDateStamp, \
                self.file_header.PointerToSymbolTable, \
                self.file_header.NumberOfSymbols, \
                self.file_header.SizeOfOptionalHeader, \
                pe_characteristics = self.read_and_unpack(f"{endian}HHIIIHH")

            self.file_header.Machine = Pe.MachineType(machine)
            self.file_header.Characteristics = Pe.FileCharacteristics(
                pe_characteristics)

            # Parse IMAGE_OPTIONAL_HEADER
            self.optional_header = self.OptionalHeader()

            self.fd.seek(0x10, 1)

            self.optional_header.AddressOfEntryPoint, \
                self.optional_header.BaseOfCode, \
                self.optional_header.BaseOfData, \
                self.optional_header.ImageBase, \
                self.optional_header.SectionAlignment, \
                self.optional_header.FileAlignment, \
                self.optional_header.MajorOperatingSystemVersion, \
                self.optional_header.MinorOperatingSystemVersion, \
                self.optional_header.MajorImageVersion, \
                self.optional_header.MinorImageVersion, \
                self.optional_header.MajorSubsystemVersion, \
                self.optional_header.MinorSubsystemVersion, \
                self.optional_header.Reserved1, \
                self.optional_header.SizeOfImage, \
                self.optional_header.SizeOfHeaders, \
                self.optional_header.CheckSum, \
                self.optional_header.Subsystem, \
                self.optional_header.DllCharacteristics, \
                self.optional_header.SizeOfStackReserve, \
                self.optional_header.SizeOfStackCommit, \
                self.optional_header.SizeOfHeapReserve, \
                self.optional_header.SizeOfHeapCommit, \
                self.optional_header.LoaderFlags, \
                self.optional_header.NumberOfRvaAndSizes = self.read_and_unpack(
                    f"{endian}IIIIIIIIIIIIIIIIIIIIIIII")

            # go to sections
            self.fd.seek(offsetImageFileHeader + sizeOfImageFileHeader +
                         self.file_header.SizeOfOptionalHeader)

            offsetSectionHeaders = self.fd.seek(0, 1)
            sizeOfSectionHeaders = struct.calcsize("8sIIIIIIHHI")

            self.__sections = []

            for i in range(self.file_header.NumberOfSections):
                section = Pe.ImageSectionHeader()
                section.Name, \
                    section.VirtualSize, \
                    section.VirtualAddress, \
                    section.SizeOfRawData, \
                    section.PointerToRawData, \
                    section.PointerToRelocations, \
                    section.PointerToLinenumbers, \
                    section.NumberOfRelocations, \
                    section.NumberOfLinenumbers, \
                    characteristics = self.read_and_unpack(
                        f"{endian}8sIIIIIIHHI")
                section.Characteristics = Pe.ImageSectionFlags(characteristics)
                self.__sections.append(section)

            self.__entry_point = self.optional_header.AddressOfEntryPoint
        return

    def __str__(self) -> str:
        return f"PE('{self.path.absolute()}', {self.file_header.Machine.name}, {str(self.file_header.Characteristics)})"

    def seek(self, off: int) -> None:
        self.fd.seek(off, 0)

    def read_and_unpack(self, fmt: str) -> Tuple[Any, ...]:
        size = struct.calcsize(fmt)
        data = self.fd.read(size)
        return struct.unpack(fmt, data)

    @ classmethod
    def is_valid(cls, path: pathlib.Path) -> bool:
        return u16(path.open("rb").read(2), e=Endianness.BIG_ENDIAN) == Pe.Constants.DOS_MAGIC

    @ property
    def checksec(self) -> Dict[str, bool]:
        warn("`checksec` doesn't apply for PE files")
        if not self.__checksec:
            self.__checksec["dynamic_base"] = self.optional_header.DllCharacteristics & Pe.DllCharacteristics.IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE != 0
            self.__checksec["force_integrity"] = self.optional_header.DllCharacteristics & Pe.DllCharacteristics.IMAGE_DLLCHARACTERISTICS_FORCE_INTEGRITY != 0
            self.__checksec["nx_compat"] = self.optional_header.DllCharacteristics & Pe.DllCharacteristics.IMAGE_DLLCHARACTERISTICS_NX_COMPAT != 0
            self.__checksec["no_isolation"] = self.optional_header.DllCharacteristics & Pe.DllCharacteristics.IMAGE_DLLCHARACTERISTICS_NO_ISOLATION != 0
            self.__checksec["no_seh"] = self.optional_header.DllCharacteristics & Pe.DllCharacteristics.IMAGE_DLLCHARACTERISTICS_NO_SEH != 0
        return self.__checksec

    @ property
    def entry_point(self) -> int:
        if self.__entry_point is None:
            raise RuntimeError("PE parsing failed to retrieve the entry point")
        return self.__entry_point

    @property
    def sections(self) -> List[FileFormatSection]:
        return self.__sections
