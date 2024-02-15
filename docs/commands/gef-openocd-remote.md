## Command gef-openocd-remote

The `gef-openocd-command` is used with the [`ARMOpenOCD`](../../archs/arm-openocd.py] architecture.

The [arm-openocd.py](../../archs/arm-openocd.py) script adds an easy way to extend the `gef-remote`
functionality to easily debug ARM targets using a OpenOCD gdbserver. It creates a custom ARM-derived
`Architecture`, as well as the `gef-openocd-remote` command, which lets you easily connect to the
target, optionally loading the accompanying ELF binary.

### Usage

```bash
gef-openocd-remote localhost 3333 --file /path/to/elf
```
