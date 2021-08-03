#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW  : EOS utilities
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


from datetime import datetime as dt
from datetime import timedelta
from math import ceil


# Little endian integers binary conversion for EOS


def uint2bin(n, sz_out):
    """Integer to n bytes for uint type"""
    return n.to_bytes(sz_out, byteorder="little")


def uint16(n):
    """Unsigned integer to 16 bits"""
    return uint2bin(n, 2)


def uint32(n):
    """Unsigned integer to 32 bits"""
    return uint2bin(n, 4)


def uintvar(n):
    """Unsigned integer, adaptative size"""
    lenn = ceil(n.bit_length() / 8)
    return uint2bin(n, lenn)


BASE32_EOS = ".12345abcdefghijklmnopqrstuvwxyz"


def string_to_binname(s):
    """Kind of compact base32 encoding for EOS"""
    i = 0
    name = 0
    while i < len(s):
        name += (BASE32_EOS.find(s[i]) & 0x1F) << (64 - 5 * (i + 1))
        i += 1
    if i > 12:
        name |= BASE32_EOS.find(s[11]) & 0x0F
    return uintvar(name)


def encode_varuint(varuint):
    """Unsigned LEB128 Encoder"""
    val = int(varuint)
    buf = b""
    while True:
        bufi = val & 0x7F
        val >>= 7
        if val <= 0:
            return buf + uint2bin(bufi, 1)
        bufi |= 0x80
        buf += uint2bin(bufi, 1)


def near_future_iso_str(n_sec):
    """Return the current UTC time plus n seconds, in a ISO8601 data time format string"""
    return (dt.utcnow() + timedelta(seconds=n_sec)).isoformat(timespec="seconds")


def expiration_string_epoch_int(exp_str):
    """Convert ISO8601 string date time to the corresponding unix epoch integer"""
    return int((dt.fromisoformat(exp_str) - dt(1970, 1, 1)).total_seconds())
