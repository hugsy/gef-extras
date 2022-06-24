"""
MachO compatibility layer
"""

__AUTHOR__ = "hugsy"
__VERSION__ = 0.2
__LICENSE__ = "MIT"


import enum
import pathlib
import struct
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from ..scripts import *
    from ..scripts import gdb


class MachO(FileFormat):
    """Basic MachO parsing."""

    class Constants(enum.IntEnum):
        MAGIC = 0xbebafeca
        MAGIC_64 = 0xfeedfacf
        FAT_BINARY_MAGIC = 0x0ef1fab9

    class CpuType(enum.IntFlag):
        UNKNOWN = 0
        VAX = 1
        ROMP = 2
        NS32032 = 4
        NS32332 = 5
        I386 = 7
        MIPS = 8
        NS32532 = 9
        HPPA = 11
        ARM = 12
        MC88000 = 13
        SPARC = 14
        I860 = 15
        I860_LITTLE = 16
        RS6000 = 17
        POWERPC = 18
        ABI64 = 0x1000000
        X86_64 = ABI64 | I386
        POWERPC64 = ABI64 | POWERPC
        ARM64 = ABI64 | ARM

    class CpuSubType(enum.IntEnum):
        X86_ALL = 3
        X86_64_ALL = 3
        ARM_V7 = 9
        ARM64_ALL = 0
        POWERPC_ALL = 0

    class FileType(enum.IntEnum):
        OBJECT = 0x1
        EXECUTE = 0x2
        FVMLIB = 0x3
        CORE = 0x4
        PRELOAD = 0x5
        DYLIB = 0x6
        DYLINKER = 0x7
        BUNDLE = 0x8
        DYLIB_STUB = 0x9
        DSYM = 0xa
        KEXT_BUNDLE = 0xb

    class CommandType(enum.IntEnum):
        REQ_DYLD = 0x80000000
        SEGMENT = 0x1
        SYMTAB = 0x2
        SYMSEG = 0x3
        THREAD = 0x4
        UNIX_THREAD = 0x5
        LOAD_FVM_LIB = 0x6
        ID_FVM_LIB = 0x7
        IDENT = 0x8
        FVM_FILE = 0x9
        PREPAGE = 0xa
        DYSYMTAB = 0xb
        LOAD_DYLIB = 0xc
        ID_DYLIB = 0xd
        LOAD_DYLINKER = 0xe
        ID_DYLINKER = 0xf
        PREBOUND_DYLIB = 0x10
        ROUTINES = 0x11
        SUB_FRAMEWORK = 0x12
        SUB_UMBRELLA = 0x13
        SUB_CLIENT = 0x14
        SUB_LIBRARY = 0x15
        TWOLEVEL_HINTS = 0x16
        PREBIND_CKSUM = 0x17
        LOAD_WEAK_DYLIB = 0x80000018
        SEGMENT_64 = 0x19
        ROUTINES_64 = 0x1a
        UUID = 0x1b
        RPATH = 0x8000001c
        CODE_SIGNATURE = 0x1d
        SEGMENT_SPLIT_INFO = 0x1e
        REEXPORT_DYLIB = 0x8000001f
        LAZY_LOAD_DYLIB = 0x20
        ENCRYPTION_INFO = 0x21
        DYLD_INFO = 0x22
        DYLD_INFO_ONLY = 0x80000022
        LOAD_UPWARD_DYLIB = 0x80000023
        VERSION_MIN_MACOSX = 0x24
        VERSION_MIN_IPHONEOS = 0x25
        FUNCTION_STARTS = 0x26
        DYLD_ENVIRONMENT = 0x27
        MAIN = 0x80000028
        DATA_IN_CODE = 0x29
        SOURCE_VERSION = 0x2A
        DYLIB_CODE_SIGN_DRS = 0x2B
        ENCRYPTION_INFO_64 = 0x2C
        LINKER_OPTION = 0x2D
        LINKER_OPTIMIZATION_HINT = 0x2E
        VERSION_MIN_TVOS = 0x2F
        VERSION_MIN_WATCHOS = 0x30
        BUILD_VERSION = 0x32

    class MachHeaderFlags(enum.IntFlag):
        MH_NOUNDEFS = 0x00000001
        MH_INCRLINK = 0x00000002
        MH_DYLDLINK = 0x00000004
        MH_BINDATLOAD = 0x00000008
        MH_PREBOUND = 0x00000010
        MH_SPLIT_SEGS = 0x00000020
        MH_LAZY_INIT = 0x00000040
        MH_TWOLEVEL = 0x00000080
        MH_FORCE_FLAT = 0x00000100
        MH_NOMULTIDEFS = 0x00000200
        MH_NOFIXPREBINDING = 0x00000400
        MH_PREBINDABLE = 0x00000800
        MH_ALLMODSBOUND = 0x00001000
        MH_SUBSECTIONS_VIA_SYMBOLS = 0x00002000
        MH_CANONICAL = 0x00004000
        MH_WEAK_DEFINES = 0x00008000
        MH_BINDS_TO_WEAK = 0x00010000
        MH_ALLOW_STACK_EXECUTION = 0x00020000
        MH_ROOT_SAFE = 0x00040000
        MH_SETUID_SAFE = 0x00080000
        MH_NO_REEXPORTED_DYLIBS = 0x00100000
        MH_PIE = 0x00200000
        MH_DEAD_STRIPPABLE_DYLIB = 0x00400000
        MH_HAS_TLV_DESCRIPTORS = 0x00800000
        MH_NO_HEAP_EXECUTION = 0x01000000

    class MachHeader:
        magic: "MachO.Constants"
        cputype: "MachO.CpuType"
        cpusubtype: "MachO.CpuSubType"
        filetype: "MachO.FileType"
        ncmds: int
        sizeofcmds: int
        flags: "MachO.MachHeaderFlags"

    name: str = "MachO"
    __entry_point: Optional[int] = None
    __checksec: Dict[str, bool]

    def __init__(self, path: Union[str, pathlib.Path]) -> None:
        """
        References:
        - http://www.stonedcoder.org/~kd/lib/MachORuntime.pdf
        """
        if isinstance(path, str):
            self.path = pathlib.Path(path).expanduser()
        elif isinstance(path, pathlib.Path):
            self.path = path
        else:
            raise TypeError

        if not self.path.exists():
            raise FileNotFoundError

        self.__checksec = {}

        endian = gef.arch.endianness
        with self.path.open("rb") as self.fd:
            # TODO
            pass

        return

    def __str__(self) -> str:
        return f"{self.name}('{self.path.absolute()}')"

    def seek(self, off: int) -> None:
        self.fd.seek(off, 0)

    def read_and_unpack(self, fmt: str) -> Tuple[Any, ...]:
        size = struct.calcsize(fmt)
        data = self.fd.read(size)
        return struct.unpack(fmt, data)

    @classmethod
    def is_valid(cls, path: pathlib.Path) -> bool:
        return u32(path.open("rb").read(4)) == MachO.Constants.MAGIC

    @property
    def checksec(self) -> Dict[str, bool]:
        warn("Not implemented")
        return self.__checksec

    @property
    def entry_point(self) -> int:
        if self.__entry_point is None:
            raise RuntimeError(
                "MachO parsing failed to retrieve the entry point")
        return self.__entry_point

    @property
    def sections(self) -> Generator[Section, None, None]:
        sp = gef.arch.sp
        for line in gdb.execute("info mach-regions", to_string=True).splitlines():
            line = line.strip()
            addr, perm, _ = line.split(" ", 2)
            addr_start, addr_end = [int(x, 16) for x in addr.split("-")]
            perm = Permission.from_process_maps(perm.split("/")[0])

            zone = file_lookup_address(addr_start)
            if zone:
                path = zone.filename
            else:
                path = "[stack]" if sp >= addr_start and sp < addr_end else ""

            yield Section(page_start=addr_start,
                          page_end=addr_end,
                          offset=0,
                          permission=perm,
                          inode=None,
                          path=path)
        return
