#!/usr/bin/python3
# -*- coding: utf8 -*-

# Satochip smartcard utilities
# Copyright (C) 2023  BitLogiK & Satochip

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import hashlib
import binascii
from typing import Union, Tuple, Optional

# from https://github.com/Electron-Cash/Electron-Cash/blob/master/lib/util.py
# from https://github.com/Electron-Cash/Electron-Cash/blob/master/lib/bitcoin.py


#private
def to_bytes(something, encoding="utf8"):
    """
    cast string to bytes() like object, but for python2 support it's bytearray copy
    """
    if isinstance(something, bytes):
        return something
    if isinstance(something, str):
        return something.encode(encoding)
    elif isinstance(something, bytearray):
        return bytes(something)
    else:
        raise TypeError("Not a string or bytes like object")

# private
def sha256(x: Union[bytes, str]) -> bytes:
    x = to_bytes(x, "utf8")
    return bytes(hashlib.sha256(x).digest())


def sha256d(x: Union[bytes, str]) -> bytes:
    x = to_bytes(x, 'utf8')
    out = bytes(sha256(sha256(x)))
    return out
    
# cardConnector
def hash_160(x: bytes) -> bytes:
    return ripemd(sha256(x))

# private
def ripemd(x: bytes) -> bytes:
    md = hashlib.new("ripemd160")
    md.update(x)
    return md.digest()


def assert_bytes(*args):
    """
    porting helper, assert args type
    """
    try:
        for x in args:
            assert isinstance(x, (bytes, bytearray))
    except:
        print("assert bytes failed", list(map(type, args)))
        raise







__b58chars = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def EncodeBase58Check(vchIn: bytes) -> str:
    hash = sha256d(vchIn)
    return base_encode(vchIn + hash[0:4], base=58)


def base_encode(v: bytes, *, base: int) -> str:
    """encode v, which is a string of bytes, to base58."""
    assert_bytes(v)
    if base not in (58, 43):
        raise ValueError("not supported base: {}".format(base))
    chars = __b58chars
    if base == 43:
        chars = __b43chars
    long_value = 0
    power_of_base = 1
    for c in v[::-1]:
        # naive but slow variant:   long_value += (256**i) * c
        long_value += power_of_base * c
        power_of_base <<= 8
    result = bytearray()
    while long_value >= base:
        div, mod = divmod(long_value, base)
        result.append(chars[mod])
        long_value = div
    result.append(chars[long_value])
    # Bitcoin does a little leading-zero-compression:
    # leading 0-bytes in the input become leading-1s
    nPad = 0
    for c in v:
        if c == 0x00:
            nPad += 1
        else:
            break
    result.extend([chars[0]] * nPad)
    result.reverse()
    return result.decode("ascii")
