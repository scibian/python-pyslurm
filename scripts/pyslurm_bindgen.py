#!/usr/bin/env python3
#########################################################################
# pyslurm_bindgen.py - generate cython compatible bindings for Slurm
#########################################################################
# Copyright (C) 2022 Toni Harzendorf <toni.harzendorf@gmail.com>
#
# This file is part of PySlurm
#
# PySlurm is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# PySlurm is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with PySlurm; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import autopxd
import click
from datetime import datetime
import os
import re
import pathlib
from collections import OrderedDict

UINT8_RANGE = range((2**8))
UINT16_RANGE = range((2**16))
UINT32_RANGE = range((2**32))
UINT64_RANGE = range((2**64))
INT8_RANGE = range(-128, 127+1)

# TODO: also translate slurm enums automatically as variables like:
# <ENUM-NAME> = slurm.<ENUM_NAME>

def get_data_type(val):
    if val in UINT8_RANGE:
        return "uint8_t"
    elif val in UINT16_RANGE:
        return "uint16_t"
    elif val in UINT32_RANGE:
        return "uint32_t"
    elif val in UINT64_RANGE:
        return "uint64_t"
    elif val in INT8_RANGE:
        return "int8_t"
    else:
        raise ValueError("Cannot get data type for value: {}".format(val))


def capture_copyright(hdr_file):
    out = []
    for line in hdr_file:
        if line.startswith("/"):
            line = line.replace("/", "#").replace("\\", "")
        line = line.replace("*", "#").lstrip()
        out.append(line)
        if "CODE-OCEC" in line:
            break

    return "".join(out)


def try_get_macro_value(s):
    if s.startswith("SLURM_BIT"):
        val = int(s[s.find("(")+1:s.find(")")])
        return 1 << val

    if s.startswith("0x"):
        return int(s, 16)

    if s.startswith("(0x"):
        _s = s[s.find("(")+1:s.find(")")]
        return int(_s, 16)

    try:
        return int(s)
    except ValueError:
        pass

    return None


def write_to_file(content, hdr):
    c = click.get_current_context()
    output_dir = c.params["output_dir"]

    output_file = os.path.join(output_dir, hdr + ".pxi")
    with open(output_file, "w") as ofile:
        ofile.write(content)


def translate_slurm_header(hdr_dir, hdr):
    hdr_path = os.path.join(hdr_dir, hdr)

    with open(hdr_path) as f:
        lines = f.readlines()
        copyright_notice = capture_copyright(lines)
        macros = "".join(translate_hdr_macros(lines, hdr))

        c = click.get_current_context()
        if c.params["show_unparsed_macros"] or c.params["generate_python_const"]:
            return

        codegen = autopxd.AutoPxd("slurm/" + hdr)
        codegen.visit(
            autopxd.parse(
                f.read(),
                extra_cpp_args=[hdr_path],
                whitelist=[hdr_path],
            )
        )

    disclaimer = f"""\
##############################################################################
# NOTICE: This File has been generated by scripts/pyslurm_bindgen.py, which
# uses the autopxd2 tool in order to generate Cython compatible definitions
# from the {hdr} C-Header file. Basically, this can be seen as a modified
# version of the original header, with the following changes:
#
# * have the correct cython syntax for type definitions, e.g. "typedef struct
# <name>" is converted to "ctypedef struct <name>"
# * C-Macros are listed with their appropriate uint type
# * Any definitions that cannot be translated are not included in this file
#
# Generated on {datetime.now().isoformat()}
#
# The Original Copyright notice from {hdr} has been included
# below:
#
{copyright_notice}#
# Slurm is licensed under the GNU GPLv2. For the full text of Slurm's License,
# please see here: pyslurm/slurm/SLURM_LICENSE
#
# Please, as mentioned above, also have a look at Slurm's DISCLAIMER under
# pyslurm/slurm/SLURM_DISCLAIMER
##############################################################################
"""

    pyslurm_copyright = """#
# Copyright (C) 2023 PySlurm Developers (Modifications as described above)
#
# This file is part of PySlurm
#
# PySlurm is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PySlurm is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with PySlurm; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
    c = click.get_current_context()
    code = disclaimer + pyslurm_copyright + macros + "\n" + str(codegen)
    code = code.replace("cpdef", "cdef")
    if c.params["stdout"]:
        print(code)
    else:
        write_to_file(code, hdr)


def handle_special_cases(name, hdr):
    if hdr == "slurm.h":
        if name == "PARTITION_DOWN":
            return "uint8_t"
        elif name == "PARTITION_UP":
            return "uint8_t"
        elif name == "PARTITION_DRAIN":
            return "uint8_t"

    return None


def parse_macro(s, hdr):
    vals = " ".join(s.split()).split()
    if not len(vals) >= 3:
        return None, None

    name = vals[1]
    val = vals[2]

    v = try_get_macro_value(val)

    if v is None:
        v = handle_special_cases(name, hdr)
        return name, v

    return name, get_data_type(v)


def translate_hdr_macros(s, hdr):
    vals = OrderedDict()
    unknown = []
    for line in s:
        if line.startswith("#define"):
            name, ty = parse_macro(line.rstrip('\n'), hdr)
            if ty:
                vals.update({name: ty})
            elif name and not ty:
                unknown.append(name)

    c = click.get_current_context()
    if c.params["show_unparsed_macros"]:
        if unknown:
            print("Unknown Macros in {}: \n".format(hdr))
            for u in unknown:
                print(u)
            print("")
        return

    out = []
    if vals:
        if c.params["generate_python_const"]:
            for name, ty in vals.items():
                print("{} = slurm.{}".format(name, name))
        else:
            hdr_file = "slurm/" + hdr
            out.append(f"cdef extern from \"{hdr_file}\":\n")
            out.append("\n")
            for name, ty in vals.items():
                out.append(f"    {ty} {name}\n")

    return out

def setup_include_path(hdr_dir):
    include_dir = pathlib.Path(hdr_dir).parent.as_posix()
    if not os.environ.get("C_INCLUDE_PATH", None):
        os.environ["C_INCLUDE_PATH"] = include_dir


@click.command(
    context_settings=dict(help_option_names=["-h", "--help"]),
    help="Generate Slurm API as Cython pxd file from C Headers.",
)
@click.option(
    "--slurm-header-dir",
    "-D",
    metavar="<dir>",
    help="Directory where the Slurm header files are located.",
)
@click.option(
    "--show-unparsed-macros",
    "-u",
    default=False,
    is_flag=True,
    help="Show only names of macros that cannot be translated and exit.",
)
@click.option(
    "--generate-python-const",
    "-c",
    default=False,
    is_flag=True,
    help="Generate variables acting as constants from Slurm macros.",
)
@click.option(
    "--output-dir",
    "-o",
    metavar="<odir>",
    default="pyslurm/slurm",
    help="Output Directory for the files",
)
@click.option(
    "--stdout",
    "-s",
    default=False,
    is_flag=True,
    help="Instead of writing everything to files, just print to stdout.",
)
def main(slurm_header_dir, show_unparsed_macros,
         generate_python_const, output_dir, stdout):
    setup_include_path(slurm_header_dir)
    translate_slurm_header(slurm_header_dir, "slurm_errno.h")
    translate_slurm_header(slurm_header_dir, "slurm.h")
    translate_slurm_header(slurm_header_dir, "slurmdb.h")


if __name__ == '__main__':
    main()
