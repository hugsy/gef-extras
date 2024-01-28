## Additional architectures for GEF

Experiments for adding support for new architectures in GEF

### Black Magic Probe

The [Black Magic Probe](https://black-magic.org/) isa JTAG/SWD debugging that handles communicating
with your device and exposes a _gdbserver_. This allows you to connect to it via GDB with the
`remote` command. However, because this is exposed via a tty, GEF cannot handle it with its
`gef-remote` command (which assumes a host:port connection). The
[arm-blackmagicprobe.py](./arm-blackmagicprobe.py) script offers a way around this. It creates a
custom ARM-derived `Architecture`, as well as the `gef-bmp-remote` command, which lets you scan for
devices, power the target, and ultimately connect to the target device.

#### Scan for devices

```bash
gef➤  gef-bmp-remote --scan /dev/ttyUSB1"
[=] [remote] Executing 'monitor swdp_scan'
Target voltage: 3.3V
Available Targets:
No. Att Driver
 1      Raspberry RP2040 M0+
 2      Raspberry RP2040 M0+
 3      Raspberry RP2040 Rescue (Attach to reset!)
```

This will connect to the BMP and use its scan feature to find valid targets connected. They will be
numbered. Use the appropriate number to later `--attach`.

If you are powering the device through the BMP, then make sure to add the `--power` arguments,
otherwise the target may not be powered up when you attempt the scan.

If you want to keep power between scanning and attaching, then use `--keep-power`.

```bash
gef➤  gef-bmp-remote --file /path/to/binary.elf --attach 1 /dev/ttyUSB1",
gef➤  gef-bmp-remote --file /path/to/binary.elf --attach 1 --power /dev/ttyUSB1",
```
