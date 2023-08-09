"""
MachO compatibility layer
"""

@lru_cache()
def inferior_is_macho():
    """Return True if the current file is a Mach-O binary."""
    for x in gdb.execute("info files", to_string=True).splitlines():
        if "file type mach-o" in x:
            return True
    return False


@lru_cache()
def is_macho(filename):
    """Return True if the specified file is a Mach-O binary."""
    file_bin = gef.session.constants["file"]
    cmd = [file_bin, filename]
    out = gef_execute_external(cmd)
    if "Mach-O" in out:
        return True
    return False


def get_mach_regions():
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


def get_process_maps():
    return list(get_mach_regions())


def checksec(filename):
    return {
        "Canary": False,
        "NX": False,
        "PIE": False,
        "Fortify": False,
        "Partial RelRO": False,
    }
