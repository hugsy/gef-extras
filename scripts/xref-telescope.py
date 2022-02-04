
@register_external_command
class XRefTelescopeCommand(SearchPatternCommand):
    """Recursively search for cross-references to a pattern in memory"""

    _cmdline_ = "xref-telescope"
    _syntax_ = "{:s} PATTERN [depth]".format(_cmdline_)
    _example_ = "\n{0:s} AAAAAAAA\n{0:s} 0x555555554000 15".format(_cmdline_)

    def xref_telescope_(self, pattern, depth, tree_heading):
        """Recursively search a pattern within the whole userland memory."""

        if depth <= 0:
            return

        if is_hex(pattern):
            if gef.arch.endianness == Endianness.BIG_ENDIAN:
                pattern = "".join(["\\x" + pattern[i:i + 2] for i in range(2, len(pattern), 2)])
            else:
                pattern = "".join(["\\x" + pattern[i:i + 2] for i in range(len(pattern) - 2, 0, -2)])

        locs = []
        for section in gef.memory.maps:
            if not section.permission & Permission.READ:
                continue
            if section.path == "[vvar]":
                continue

            start = section.page_start
            end = section.page_end - 1

            locs += self.search_pattern_by_address(pattern, start, end)
        if tree_heading == "":
            gef_print(" .")
        for i, loc in enumerate(locs):
            addr_loc_start = lookup_address(loc[0])
            path = addr_loc_start.section.path
            perm = addr_loc_start.section.permission
            if i == len(locs) - 1:
                tree_suffix_pre = " └──"
                tree_suffix_post = "    "
            else:
                tree_suffix_pre = " ├──"
                tree_suffix_post = " │  "

            gef_print('{} {:#x} {} {} "{}"'
                      .format(tree_heading + tree_suffix_pre,
                              loc[0], Color.blueify(path),
                              perm, Color.pinkify(loc[2])))
            self.xref_telescope_(hex(loc[0]), depth - 1,
                                 tree_heading + tree_suffix_post)

    def xref_telescope(self, pattern, depth):
        self.xref_telescope_(pattern, depth, "")

    @only_if_gdb_running
    def do_invoke(self, argv):
        argc = len(argv)
        if argc < 1:
            self.usage()
            return

        pattern = argv[0]
        try:
            depth = int(argv[1])
        except (IndexError, ValueError):
            depth = 3

        info("Recursively searching '{:s}' in memory"
             .format(Color.yellowify(pattern)))
        self.xref_telescope(pattern, depth)
