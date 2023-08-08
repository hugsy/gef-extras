## WinDbg compatibility layer

This plugin is a set of commands, aliases and extensions to mimic some of the most common WinDbg commands into GEF.

### Commands

  - `hh` - open GEF help in web browser
  - `sxe` (set-exception-enable): break on loading libraries
  - `tc` - trace to next call
  - `pc` - run until call.
  - `g` - go.
  - `u` - disassemble.
  - `x` - search symbol.
  - `r` - register info


### Settings

  - `gef.use-windbg-prompt` - set to `True` to change the prompt like `0:000 ➤`


### Aliases

  - `da` : `display s`
  - `dt` : `pcustom`
  - `dq` : `hexdump qword`
  - `dd` : `hexdump dword`
  - `dw` : `hexdump word`
  - `db` : `hexdump byte`
  - `eq` : `patch qword`
  - `ed` : `patch dword`
  - `ew` : `patch word`
  - `eb` : `patch byte`
  - `ea` : `patch string`
  - `dps` : `dereference`
  - `bp` : `break`
  - `bl` : `info breakpoints`
  - `bd` : `disable breakpoints`
  - `bc` : `delete breakpoints`
  - `be` : `enable breakpoints`
  - `tbp` : `tbreak`
  - `s` : `grep`
  - `pa` : `advance`
  - `kp` : `info stack`
  - `ptc` : `finish`
  - `uf` : `disassemble`
