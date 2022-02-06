#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW  -  Wallets Utilities
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


from decimal import DefaultContext, Decimal


utils_decimal_ctx = DefaultContext.copy()
# Setup up to 999'999 billion at 18 decimals
utils_decimal_ctx.prec = 33
POINT_CHAR = "."
ZERO_CHAR = "0"


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
    return int(utils_decimal_ctx.scaleb(Decimal(num_str, utils_decimal_ctx), shift))


def balance_string(amount, decimshift=0):
    """Convert integer shifted by decimshift decimals units
    into a human float string.
    """
    if not isinstance(amount, int):
        raise ValueError("amount arg must be int")
    if decimshift < 0:
        raise ValueError("decimshift must be postive or null")
    num = utils_decimal_ctx.scaleb(Decimal(amount, utils_decimal_ctx), -decimshift)
    if num.is_zero():
        return ZERO_CHAR
    bal_res = f"{num:.{decimshift}f}"
    if len(bal_res) > 1 and POINT_CHAR in bal_res[:-1]:
        bal_res = bal_res.rstrip(ZERO_CHAR)
    if bal_res[-1] == POINT_CHAR:
        bal_res = bal_res[:-1]
    return bal_res


def compare_eth_addresses(addr1, addr2):
    """Compare 2 ethereum-compatible addresses.
    Accept 0x or hex, lower, upper or mixed "checksummed".
    Does not check for their validity.
    """
    if addr1.startswith("0x"):
        addr1 = addr1[2:]
    if addr2.startswith("0x"):
        addr2 = addr2[2:]
    return addr1.lower() == addr2.lower()


class InvalidOption(Exception):
    pass


class NotEnoughTokens(Exception):
    pass
