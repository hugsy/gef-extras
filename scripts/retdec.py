__AUTHOR__ = "Minato-TW"
__VERSION__ = 0.1

import getopt
import subprocess
import gdb
import os
import re
import tempfile
from shlex import quote


class RetDecCommand(GenericCommand):
    """Decompile code from GDB context using RetDec API."""

    _cmdline_ = "retdec"
    _syntax_ = "{:s} [-r RANGE1-RANGE2] [-s SYMBOL] [-a] [-h]".format(_cmdline_)
    _aliases_ = ["decompile"]
    _example_ = "{:s} -s main".format(_cmdline_)

    def __init__(self):
        super(RetDecCommand, self).__init__(complete=gdb.COMPLETE_SYMBOL)
        self.add_setting("path", GEF_TEMP_DIR, "Path to store the decompiled code")
        self.add_setting("retdec_path", "", "Path to the retdec installation")
        return

    @only_if_gdb_running
    def do_invoke(self, argv):
        arch = current_arch.arch.lower()
        if not arch:
            err("RetDec does not decompile '{:s}'".format(get_arch()))
            return

        retdec_path = self.get_setting("retdec_path").strip()
        if not retdec_path:
            msg = "Path to retdec installation not provided, use `gef config` to set the path"
            err(msg)
            return

        retdec_decompiler = "{}/bin/retdec-decompiler.py".format(retdec_path)
        if not os.path.exists(retdec_decompiler):
            msg = "Retdec decompiler not found! Verify your installation"
            err(msg)
            return

        params = {
            "architecture": arch,
            "target_language": "c",
            "raw_endian": "big" if is_big_endian() else "little",
        }

#        raw_cmd = "{} -m {} --raw-section-vma {} --raw-entry-point {} -e {} -f plain -a {} -o {} -l {} {} --cleanup"
#        bin_cmd = "{} -m {} -e {} -f plain -a {} -o {} -l {} {} --cleanup"

        opts = getopt.getopt(argv, "r:s:ah")[0]
        if not opts:
            self.usage()
            return

        for opt, arg in opts:
            if opt == "-r":
                range_from, range_to = map(lambda x: int(x, 16), arg.split("-", 1))
                fd, filename = tempfile.mkstemp(dir=self.get_setting("path"))
                with os.fdopen(fd, "wb") as f:
                    length = range_to - range_from
                    f.write(read_memory(range_from, length))
                params["mode"] = "raw"
                params["file_format"] = "elf"
                params["raw_section_vma"] = hex(range_from)
                params["raw_entry_point"] = hex(range_from)
            elif opt == "-s":
                try:
                    value = gdb.parse_and_eval(arg)
                except gdb.error:
                    err("No symbol named '{:s}'".format(arg))
                    return
                range_from = int(value.address)
                fd, filename = tempfile.mkstemp(dir=self.get_setting("path"))
                with os.fdopen(fd, "wb") as f:
                    f.write(read_memory(range_from, get_function_length(arg)))
                params["mode"] = "raw"
                params["file_format"] = "elf"
                params["raw_section_vma"] = hex(range_from)
                params["raw_entry_point"] = hex(range_from)
            elif opt == "-a":
                filename = get_filepath()
                params["mode"] = "bin"
            else:
                self.usage()
                return

        # Set up variables
        path = self.get_setting("path")
        params["input_file"] = filename
        fname = "{}/{}.{}".format(path, os.path.basename(params["input_file"]), params["target_language"])
        logfile = "{}/{}.log".format(path, os.path.basename(params["input_file"]))
        if params["mode"] == "bin":
            cmd = [
                retdec_decompiler,
                "-m", params["mode"],
                "-e", params["raw_endian"],
                "-f", "plain",
                "-a", params["architecture"],
                "-o", fname, 
                "-l", params["target_language"],
                params["input_file"],
                "--cleanup"
            ]

        else:
            cmd = [
              retdec_decompiler, 
              "-m", params["mode"], 
              "--raw-section-vma", params["raw_section_vma"], 
              "--raw-entry-point", params["raw_entry_point"], 
              "-e", params["raw_endian"],
              "-f", "plain",
              "-a", params["architecture"],
              "-o",fname,
              "-l", params["target_language"],
              params["input_file"],
              "--cleanup"
            ]
        if self.send_to_retdec(params, cmd, logfile) is False:
            return

        ok("Saved as '{:s}'".format(fname))
        with open(fname, "r") as f:
            pattern = re.compile(r"unknown_([a-f0-9]+)")
            for line in f:
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                # try to fix the unknown with the current context
                for match in pattern.finditer(line):
                    s = match.group(1)
                    pc = int(s, 16)
                    insn = gef_current_instruction(pc)
                    if insn.location:
                        line = line.replace("unknown_{:s}".format(s), insn.location)
                print(line)
        return

    def send_to_retdec(self, params, cmd, logfile):
        try:
            with open(logfile, "wb") as log:
                subprocess.run(cmd, stdout=log)
        except Exception:
            msg = "Error encountered during decompilation. Check the log file at {}".format(logfile)
            err(msg)
            return False

        return True


if __name__ == "__main__":
    register_external_command(RetDecCommand())
