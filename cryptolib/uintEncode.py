#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW  :  Integer encodings
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


# Little endian integers binary conversion


def uint2bin(n, sz_out):
    """Integer to n bytes for uint type"""
    return n.to_bytes(sz_out, byteorder="little")


def uint8(n):
    """Unsigned integer to 16 bits"""
    return uint2bin(n, 1)


def uint16(n):
    """Unsigned integer to 16 bits"""
    return uint2bin(n, 2)


def uint32(n):
    """Unsigned integer to 32 bits"""
    return uint2bin(n, 4)


def uint64(n):
    """Unsigned integer to 32 bits"""
    return uint2bin(n, 8)


def encode_varuint(varuint):
    """Unsigned LEB128 Encoder"""
    val = int(varuint)
    buf = []
    while True:
        bufi = val & 0x7F
        val >>= 7
        if val <= 0:
            buf.append(bufi)
            return bytes(buf)
        bufi |= 0x80
        buf.append(bufi)
