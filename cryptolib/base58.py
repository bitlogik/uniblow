# -*- coding: utf8 -*-

# UNIBLOW  -  base58
# Copyright (C) 2021-2022 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


from math import ceil
from .cryptography import b58checksum


BASE58 = 58
b58chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def bin_to_base58(bin_data):
    base58 = ""
    int_data = int.from_bytes(bin_data, "big")
    while int_data >= BASE58:
        base58 = b58chars[int_data % BASE58] + base58
        int_data = int_data // BASE58
    base58 = b58chars[int_data % BASE58] + base58
    for charval in bin_data:
        if charval == 0:
            base58 = "1" + base58
        else:
            break
    return base58


def encode_base58(bin_data):
    """Create a Base58Check string"""
    return bin_to_base58(bin_data + b58checksum(bin_data))


def encode_base58_header(bin_data, header=0):
    """Create a Base58Check string with header"""
    if header == 0:
        bin_data = bytes([header]) + bin_data
    while header > 0:
        bin_data = bytes([header % 256]) + bin_data
        header //= 256
    return bin_to_base58(bin_data + b58checksum(bin_data))


def base58_to_bin(base58_str):
    if not all(x in b58chars for x in base58_str):
        raise ValueError("Base58 string contains invalid characters")
    int_data = 0
    pwr_rank = 1
    for i in range(-1, -len(base58_str) - 1, -1):
        int_data += b58chars.index(base58_str[i]) * pwr_rank
        pwr_rank *= 58
    out_data = int_data.to_bytes(ceil(int_data.bit_length() / 8), "big", signed=False)
    for charact in base58_str:
        if charact == "1":
            out_data = b"\0" + out_data
        else:
            break
    return out_data


def decode_base58(b58string):
    bin_data_all = base58_to_bin(b58string)
    if len(bin_data_all) < 4:
        raise ValueError("Base58 string is to short")
    if b58checksum(bin_data_all[:-4]) != bin_data_all[-4:]:
        raise ValueError("Base58 checksum is not valid")
    return bin_data_all[:-4]
