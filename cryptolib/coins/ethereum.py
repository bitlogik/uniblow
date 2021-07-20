#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW  : Ethereum utilities
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


def rlp_encode(input):
    if isinstance(input, bytearray):
        if len(input) == 1 and input[0] == 0:
            return bytearray(b"\x80")
        if len(input) == 1 and input[0] < 0x80:
            return input
        else:
            return encode_length(len(input), 0x80) + input
    elif isinstance(input, list):
        output = bytearray([])
        for item in input:
            output += rlp_encode(item)
        return encode_length(len(output), 0xC0) + output
    raise Exception("Bad input type, list or bytearray needed")


def encode_length(L, offset):
    if L < 56:
        return bytearray([L + offset])
    BL = to_binary(L)
    return bytearray([len(BL) + offset + 55]) + BL


def to_binary(x):
    if x == 0:
        return bytearray([])
    else:
        return to_binary(int(x // 256)) + bytearray([x % 256])


def int2bytearray(i):
    barr = (i).to_bytes(32, byteorder="big")
    while barr[0] == 0 and len(barr) > 1:
        barr = barr[1:]
    return bytearray(barr)


def uint256(i):
    """Integer to 256bits bytes for uint EVM"""
    return i.to_bytes(32, byteorder="big")


def read_uint256(data, offset):
    """Extract and decode utint256 at the given offset bytes"""
    return int.from_bytes(data[offset : offset + 32], "big")


def read_string(data_ans):
    """ABI String decoding"""
    data_bin = bytes.fromhex(data_ans[2:])
    str_offset = read_uint256(data_bin, 0)
    str_len = read_uint256(data_bin, str_offset)
    str_offset += 32
    return data_bin[str_offset : str_offset + str_len].decode("utf8")
