class RetDecCommand(GenericCommand):
    """Decompile code from GDB context using RetDec API."""

    _cmdline_ = "retdec"
    _syntax_  = "{:s} [-r RANGE1-RANGE2] [-s SYMBOL] [-a] [-h]".format(_cmdline_)
    _aliases_ = ["decompile",]
    _example_ = "{:s} -s main".format(_cmdline_)

    def __init__(self):
        super(RetDecCommand, self).__init__(complete=gdb.COMPLETE_SYMBOL)
        self.add_setting("key", "", "RetDec decompilator API key")
        self.add_setting("path", GEF_TEMP_DIR, "Path to store the decompiled code")
        self.decompiler = None
        return

    def pre_load(self):
        if PYTHON_MAJOR==2:
            msg = "Package `retdec-python` is not supported on Python2. See https://github.com/s3rvac/retdec-python#requirements"
            raise RuntimeError(msg)

        try:
            __import__("retdec")
            __import__("retdec.decompiler")
        except ImportError:
            msg = "Missing `retdec-python` package for Python{0}, install with: `pip{0} install retdec-python`.".format(PYTHON_MAJOR)
            raise ImportWarning(msg)
        return

    @only_if_gdb_running
    def do_invoke(self, argv):
        arch = current_arch.arch.lower()
        if not arch:
            err("RetDec does not decompile '{:s}'".format(get_arch()))
            return

        api_key = self.get_setting("key").strip()
        if not api_key:
            warn("No RetDec API key provided, use `gef config` to add your own key")
            return

        if self.decompiler is None:
            retdec = sys.modules["retdec"]
            self.decompiler = retdec.decompiler.Decompiler(api_key=api_key)

        params = {
            "architecture": arch,
            "target_language": "c",
            "raw_endian": "big" if is_big_endian() else "little",
            "decomp_var_names": "readable",
            "decomp_emit_addresses": "no",
            "generate_cg": "no",
            "generate_cfg": "no",
            "comp_compiler": "gcc",
        }

        opts = getopt.getopt(argv, "r:s:ah")[0]
        if not opts:
            self.usage()
            return

        for opt, arg in opts:
            if opt == "-r":
                range_from, range_to = map(lambda x: int(x,16), arg.split("-", 1))
                fd, filename = tempfile.mkstemp()
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
                range_from = long(value.address)
                fd, filename = tempfile.mkstemp()
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

        params["input_file"] = filename
        if self.send_to_retdec(params) == False:
            return

        fname = os.path.join(self.get_setting("path"), "{}.c".format(os.path.basename(filename)))
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


    def send_to_retdec(self, params):
        try:
            retdec = sys.modules["retdec"]
            path = self.get_setting("path")
            decompilation = self.decompiler.start_decompilation(**params)
            info("Task submitted, waiting for decompilation to finish... ", cr=False)
            decompilation.wait_until_finished()
            print("Done")
            decompilation.save_hll_code(self.get_setting("path"))
            fname = "{}/{}.{}".format(path, os.path.basename(params["input_file"]), params["target_language"])
            ok("Saved as '{:s}'".format(fname))
        except retdec.exceptions.AuthenticationError:
            err("Invalid RetDec API key")
            info("You can store your API key using `gef config`/`gef restore`")
            self.decompiler = None
            return False

        return True

register_external_command(RetDecCommand())
