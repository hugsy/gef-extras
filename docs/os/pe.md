# PE support

Even though vanilla GEF was oriented around Linux executable ELF support originally, it was also built around an abstraction layer that allows other file formats and architectures via GEF-Extras.

This page explains how to debug [Portable Executable](https://en.wikipedia.org/wiki/Portable_Executable) (or PE) files running on Windows or Wine/Linux.

## Setup

Clone GEF-Extras and
 - either edit your `~/.gdbinit` to source the PE module
 - execute the command directly in the prompt

```text
source /path/to/gef-extras/os/pe.py
```

This will register the PE format allowing GEF to autodetect the loading of PE. Then just load your file:

```text

```

If you're using Wine/Linux, you can either use `winedbg --gdb` to debug directly the binary, or `winedbg --gdb --no-start` which will allow to connect remotely using `gef-remote`

```text
$ winedbg --gdb --no-start ./stackoverflow.exe
002c:002d: create process 'C:\temp\int3.exe'/0x10900 @0x140001480 (0<0>)
002c:002d: create thread I @0x140001480
target remote localhost:58523
```

Then on your host:

```text
gef➤ source /dev/gef-extras/os/pe.py
gef➤ gef-remote localhost 58523
```

*TODO: screenshot*

You can freely interact with the `gef` object direct:

```text

```


Most of the commands from GEF should be available, but some specific ones were desised
