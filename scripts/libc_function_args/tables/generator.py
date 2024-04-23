#!/usr/bin/env python3
__AUTHOR__ = "theguly"
__VERSION__ = 0.2

import inspect
import gzip
import json
import logging
import pathlib
from typing import Dict, List

import requests

function_dict: Dict[str, List[str]] = {}


def __get_function_name(l: str) -> str:
    pre_args = l.split(" (")[0]
    _function_name = pre_args.split(" ")[-1]
    return _function_name


def __get_function_args(l: str) -> List[str]:
    _function_args = " (".join(l.split(" (")[1:])
    _function_args = ")".join(_function_args.split(")")[:-1])
    _function_args = _function_args.split(",")
    ret_function_args = [_function_arg.strip() for _function_arg in _function_args]
    return ret_function_args


def generate_json_file(
    function_dict: dict[str, List[str]], _params: List[str], outfile_name: pathlib.Path
) -> bool:
    _dict = {}
    for _key, _value in function_dict.items():
        _dict[_key] = {}
        for i in range(0, len(_value)):
            _dict[_key][_params[i]] = _value[i]

    outfile_path = pathlib.Path(inspect.getfile(inspect.currentframe())).parent.resolve() /  outfile_name
    with outfile_path.open("w") as outfile:
        json.dump(_dict, outfile)

    logging.info(f"{outfile_name} written")
    return True


def generate_all_json_files() -> bool:
    curdir = pathlib.Path(inspect.getfile(inspect.currentframe())).parent.resolve()
    libc_file_path = curdir / "libc.txt.gz"
    libc_x86_funcdef_fpath = curdir / "x86_32.json"
    libc_x64_funcdef_fpath = curdir / "x86_64.json"
    libc_funcdef_list = [libc_x86_funcdef_fpath, libc_x64_funcdef_fpath]

    if not libc_file_path.exists():
        #
        # Try once to download if missing
        #
        url = "https://www.gnu.org/software/libc/manual/text/libc.txt.gz"
        res = requests.get(url, stream=True)
        if res.status_code == 200:
            with libc_file_path.open("wb") as fd:
                for chunk in res.iter_content(chunk_size=128):
                    fd.write(chunk)

    for f in (libc_x86_funcdef_fpath, libc_x64_funcdef_fpath):
        if f.exists():
            overwrite = input(f"File {f} exists, overwrite? [y/N]")
            if "y" in overwrite.lower():
                logging.debug(f"{f} will be overwritten")
            else:
                logging.info(f"Not overwriting {f}")
                libc_funcdef_list.remove(f)

    if libc_funcdef_list:
        #
        # looks like gzip.open doesn't raise any exception if opening a non-gzipped file. you'll end up with empty json
        #
        try:
            fh = gzip.open(libc_file_path, "r")
        except FileNotFoundError:
            logging.error(f"Missing {libc_file_path}.")
            return False

        old_pos = fh.tell()

        while True:
            line = fh.readline().decode("utf-8")

            # check for EoF
            current_pos = fh.tell()
            if current_pos == old_pos:
                break
            else:
                old_pos = current_pos

            if " -- Function: " in line:
                # some function def span two lines, join them
                line = line.replace(" -- Function: ", "").rstrip().rstrip(";").lstrip()
                if not line.endswith(")"):
                    next_line = fh.readline()
                    next_line = next_line.decode("utf-8")
                    next_line = next_line.rstrip().lstrip()
                    line = f"{line} {next_line}"

                function_name = __get_function_name(line)
                function_args = __get_function_args(line)

                # there are two dupes as of now, get around the issue by using the last one found
                if function_name in function_dict:
                    logging.warning(f"Found dupe for {function_name}")

                function_dict[function_name] = []

                for x in function_args:
                    function_dict[function_name].append(x)

        # generate x86_64
        if libc_x64_funcdef_fpath in libc_funcdef_list and not generate_json_file(
            function_dict,
            ["$rdi", "$rsi", "$rdx", "$r10", "$r8", "$r9"],
            libc_x64_funcdef_fpath,
        ):
            logging.error(
                f"An error occurred while generating {libc_x64_funcdef_fpath}"
            )

        # generate x86_32
        if libc_x86_funcdef_fpath in libc_funcdef_list and not generate_json_file(
            function_dict,
            [
                "[sp + 0x0]",
                "[sp + 0x4]",
                "[sp + 0x8]",
                "[sp + 0xc]",
                "[sp + 0x10]",
                "[sp + 0x14]",
            ],
            libc_x86_funcdef_fpath,
        ):
            logging.error(
                f"An error occurred while generating {libc_x86_funcdef_fpath}"
            )

    return True
