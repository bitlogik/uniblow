# -*- coding: utf8 -*-

# RS1024 checksum for SLIP39
# Copyright (C) 2024 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


GENERATOR = (
    0xE0E040,
    0x1C1C080,
    0x3838100,
    0x7070200,
    0xE0E0009,
    0x1C0C2412,
    0x38086C24,
    0x3090FC48,
    0x21B1F890,
    0x3F3F120,
)


def polymod_rs1024(values: list) -> int:
    """Reed-Solomon code over GF(1024), for 10-bit blocks"""
    if len(values) < 1:
        raise ValueError("Must check values.")
    chk = 1
    for v in values:
        b = chk >> 20
        chk &= 0xFFFFF
        chk <<= 10
        chk ^= v
        for i in range(10):
            if (b >> i) & 1:
                chk ^= GENERATOR[i]
    return chk


def verify_checksum(header: bytes, data: list) -> bool:
    return polymod_rs1024(list(header) + data) == 1
