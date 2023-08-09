## Custom structures

Open repositories of custom structures for GDB Enhanced Features (GEF). Structures are available
via the `pcustom` command (often aliased as `dt`) and allow to recreate and parse at runtime a
segment of memory as-if you had the structure defined in symbols.

Example:

```text
gef➤  pcustom list
[+] Listing custom structures from '/tmp/structs'
 →  /tmp/structs/elf64_t.py (elf64_t)

gef➤  vmmap libc
[ Legend:  Code | Heap | Stack ]
Start              End                Offset             Perm Path
0x00007ffff7d9e000 0x00007ffff7dc3000 0x0000000000000000 r-- /usr/lib/x86_64-linux-gnu/libc-2.31.so
[...]

0:000 ➤  pucstom elf64_t 0x00007ffff7d9e000
0x7ffff7d9e000+0x0000 ei_magic :        b'\x7fELF' (c_char_Array_4)  →  Correct ELF header
0x7ffff7d9e000+0x0004 ei_class :        2 (c_ubyte)  →  ELFCLASS64
0x7ffff7d9e000+0x0005 ei_data :         1 (c_ubyte)
0x7ffff7d9e000+0x0006 ei_version :      1 (c_ubyte)
0x7ffff7d9e000+0x0007 ei_padd :         b'\x03' (c_char_Array_9)
0x7ffff7d9e000+0x0010 e_type :          3 (c_ushort)  →  ET_DYN
0x7ffff7d9e000+0x0012 e_machine :       62 (c_ushort)  →  EM_AMD64
0x7ffff7d9e000+0x0014 e_version :       1 (c_int)
0x7ffff7d9e000+0x0018 e_entry :         0x00000000000271f0 (c_ulong)
0x7ffff7d9e000+0x0020 e_phoff :         0x0000000000000040 (c_ulong)
0x7ffff7d9e000+0x0028 e_shoff :         0x00000000001ee568 (c_ulong)
0x7ffff7d9e000+0x0030 e_flags :         0 (c_int)
0x7ffff7d9e000+0x0034 e_ehsize :        64 (c_ushort)
0x7ffff7d9e000+0x0036 e_phentsize :     56 (c_ushort)
0x7ffff7d9e000+0x0038 e_phnum :         14 (c_ushort)
0x7ffff7d9e000+0x003a e_shentsize :     64 (c_ushort)
0x7ffff7d9e000+0x003c e_shnum :         69 (c_ushort)
0x7ffff7d9e000+0x003e e_shstrndx :      68 (c_ushort)
```

To add a new structure, use the skeleton below (refer to the
[`ctypes` documentation](https://docs.python.org/3/library/ctypes.html) for the syntax)

```python
from ctypes import *

class MyStructure(Structure):
    _fields_ = [
        ("Item1", c_short),
        ("Item2", c_void_p),
        ("Item3", 16 * c_uint32),
    ]
    _values_ = []
```

See [`pcustom`](https://hugsy.github.io/commands/pcustom/) for complete documentation
