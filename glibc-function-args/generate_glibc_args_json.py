#!/usr/bin/env python3
__AUTHOR__ = "theguly"
__VERSION__ = 0.1

import gzip
import json
import os
import sys

function_dict = {}


def get_function_name(l):
    pre_args = l.split(" (")[0]
    _function_name = pre_args.split(" ")[-1]
    return _function_name


def get_function_args(l):
    _function_args = " (".join(l.split(" (")[1:])
    _function_args = ")".join(_function_args.split(")")[:-1])
    _function_args = _function_args.split(",")
    ret_function_args = []
    for _function_arg in _function_args:
        ret_function_args.append(_function_arg.lstrip().rstrip())
    return ret_function_args


def gen_json(function_dict, _params, outfile_name):
    _dict = {}
    for _key, _value in function_dict.items():
        _dict[_key] = {}
        for i in range(0, len(_value)):
            _dict[_key][_params[i]] = _value[i]

    if os.path.isfile(outfile_name):
        print("file {} exists, overwrite? [y/N]".format(outfile_name))
        overwrite = input()
        if "y" in overwrite.lower():
            print("overwriting {}".format(outfile_name))
        else:
            print("not overwriting {}".format(outfile_name))
            return
    with open(outfile_name, "w") as outfile:
        json.dump(_dict, outfile)
    print("{} written".format(outfile_name))

    return


if __name__ == "__main__":
    file_name = "libc.txt.gz"

    # looks like gzip.open doesn't raise any exception if opening a non-gzipped file. you'll end up with empty json
    try:
        fh = gzip.open(file_name, "r")
    except FileNotFoundError:
        print(
            "file {} cannot be found. download it from https://www.gnu.org/software/libc/manual/text/libc.txt.gz".format(
                file_name
            )
        )
        sys.exit(-1)

    old_pos = fh.tell()

    while True:
        line = fh.readline()
        line = line.decode("utf-8")

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
                line = "{} {}".format(line, next_line)

            function_name = get_function_name(line)
            function_args = get_function_args(line)

            # there are two dupes as of now, get around the issue by using the last one found
            if function_name in function_dict:
                print("DUPE! {}".format(function_name))

            function_dict[function_name] = []

            for x in function_args:
                function_dict[function_name].append(x)

    # generate x86_64
    gen_json(
        function_dict, ["$rdi", "$rsi", "$rdx", "$r10", "$r8", "$r9"], "x86_64.json"
    )
    # generate x86_32
    gen_json(
        function_dict,
        [
            "[sp + 0x0]",
            "[sp + 0x4]",
            "[sp + 0x8]",
            "[sp + 0xc]",
            "[sp + 0x10]",
            "[sp + 0x14]",
        ],
        "x86_32.json",
    )
