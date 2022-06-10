

def get_generic_arch(module: ModuleType, prefix: str, arch: str, mode: Optional[str], big_endian: Optional[bool], to_string: bool = False) -> Tuple[str, Union[int, str]]:
    """
    Retrieves architecture and mode from the arguments for use for the holy
    {cap,key}stone/unicorn trinity.
    """
    if to_string:
        arch = f"{module.__name__}.{prefix}_ARCH_{arch}"
        if mode:
            mode = f"{module.__name__}.{prefix}_MODE_{mode}"
        else:
            mode = ""
        if gef.arch.endianness == Endianness.BIG_ENDIAN:
            mode += f" + {module.__name__}.{prefix}_MODE_BIG_ENDIAN"
        else:
            mode += f" + {module.__name__}.{prefix}_MODE_LITTLE_ENDIAN"

    else:
        arch = getattr(module, f"{prefix}_ARCH_{arch}")
        if mode:
            mode = getattr(module, f"{prefix}_MODE_{mode}")
        else:
            mode = 0
        if big_endian:
            mode |= getattr(module, f"{prefix}_MODE_BIG_ENDIAN")
        else:
            mode |= getattr(module, f"{prefix}_MODE_LITTLE_ENDIAN")

    return arch, mode


def get_generic_running_arch(module: ModuleType, prefix: str, to_string: bool = False) -> Union[Tuple[None, None], Tuple[str, Union[int, str]]]:
    """
    Retrieves architecture and mode from the current context.
    """

    if not is_alive():
        return None, None

    if gef.arch is not None:
        arch, mode = gef.arch.arch, gef.arch.mode
    else:
        raise OSError("Emulation not supported for your OS")

    return get_generic_arch(module, prefix, arch, mode, gef.arch.endianness == Endianness.BIG_ENDIAN, to_string)
