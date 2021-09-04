#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Single Key Wallet
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


from secrets import randbelow
from cryptolib.cryptography import CURVES_ORDER
from cryptolib.ECKeyPair import EC_key_pair


CURVE_K1_ORDER = CURVES_ORDER["K1"]
CURVE_R1_ORDER = CURVES_ORDER["R1"]
EC_BYTES_SIZE = 32


class SKdevice:

    has_password = True
    has_admin_password = False
    is_HD = False

    def __init__(self, ktype="K1"):
        # KType is K1, R1 or ED
        self.ktype = ktype
        self.created = False
        self.has_hardware_button = False

    def open_account_fromint(self, key_int):
        self.eckey = EC_key_pair(key_int, self.ktype)

    def load_key(self, ecpair_obj):
        self.eckey = ecpair_obj

    def initialize_device(self):
        # Generate a new key
        if self.ktype == "K1":
            pvkey_int = randbelow(CURVE_K1_ORDER)
        elif self.ktype == "R1":
            pvkey_int = randbelow(CURVE_R1_ORDER)
        else:
            pvkey_int = randbelow(2 ** 256)
        self.open_account_fromint(pvkey_int)
        self.created = True
        return pvkey_int

    def get_public_key(self, compressed=True):
        # compressed has no effect if type id Ed
        return self.eckey.get_public_key(compressed).hex()

    def sign(self, hashed_msg):
        # If Ed, hashed_msg is the full message
        return self.eckey.sign(hashed_msg)
