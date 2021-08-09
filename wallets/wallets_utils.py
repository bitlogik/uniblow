#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW  -  Wallets Utilities
# Copyright (C) 2021 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


def shift_10(num_str, shift):
    """Multiply by power of 10 at the string level, args >= 0"""
    # Act like a point shifter
    # Avoid floating point issues
    if not isinstance(num_str, str):
        raise ValueError("num_str must be string")
    if not isinstance(shift, int):
        raise ValueError("shift must be integer")
    if shift < 0:
        raise ValueError("shift must be postive or null")
    num_str_parts = num_str.split(".")
    int_str = num_str_parts[0]
    if len(num_str_parts) == 1:
        new_int = int_str + "0" * shift
    elif len(num_str_parts) == 2:
        dec_str = num_str_parts[1]
        while len(dec_str) < shift:
            dec_str += "0"
        new_int = int_str + dec_str[:shift]
    else:
        raise Exception("Invalid value")
    if set(new_int) != {"0"}:
        return int(new_int.lstrip("0"))
    return 0

class InvalidOption(Exception):
    pass
