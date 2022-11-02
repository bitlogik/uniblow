#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW  : Ethereum utilities
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


def rlp_encode(input_data):
    if isinstance(input_data, int):
        if input_data < 0:
            raise ValueError("RLP encoding error : integer must be positive or null")
        return rlp_encode(to_binary(input_data))
    if isinstance(input_data, bytearray):
        if len(input_data) == 1 and input_data[0] == 0:
            return bytearray(b"\x80")
        if len(input_data) == 1 and input_data[0] < 0x80:
            return input_data
        return encode_length(len(input_data), 0x80) + input_data
    if isinstance(input_data, list):
        output = bytearray([])
        for item in input_data:
            output += rlp_encode(item)
        return encode_length(len(output), 0xC0) + output
    raise ValueError("Bad input_data type : int, list or bytearray required")


def encode_length(Lon, offset):
    if Lon < 56:
        return bytearray([Lon + offset])
    BLon = to_binary(Lon)
    return bytearray([len(BLon) + offset + 55]) + BLon


def to_binary(x):
    if x == 0:
        return bytearray([])
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


def read_int_array(data_hex):
    """Decode an int (uint256) array from ABI."""
    data_bin = bytes.fromhex(data_hex[2:])
    idx = 32
    datasz = 32
    if read_uint256(data_bin, 0) != datasz:
        raise ValueError("Bad uint[] format.")
    out = []
    n_int = read_uint256(data_bin, idx)
    if len(data_bin) != datasz * (n_int + 2):
        raise ValueError("Bad ABI data.")
    idx += datasz
    while n_int > 0:
        out.append(read_uint256(data_bin, idx))
        n_int -= 1
        idx += datasz
    return out
