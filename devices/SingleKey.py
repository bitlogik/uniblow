#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Single Key Wallet
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


from secrets import randbelow
from cryptolib.cryptography import CURVES_ORDER
from cryptolib.ECKeyPair import EC_key_pair

from devices.BaseDevice import BaseDevice
from wallets.wallets_utils import InvalidOption

CURVE_K1_ORDER = CURVES_ORDER["K1"]
EC_BYTES_SIZE = 32


class SKdevice(BaseDevice):

    has_password = True

    def __init__(self):
        self.ktype = None
        self.eckey = None

    def open_account(self):
        raise InvalidOption("SingleKey device can't be opened using this method.")

    def open_account_fromint(self, key_int):
        self.eckey_k1 = EC_key_pair(key_int, "K1")
        # self.eckey_r1 = EC_key_pair(key_int, "R1")
        self.eckey_ed = EC_key_pair(key_int, "ED")

    def try_keep_keytype(self, keytype):
        if self.eckey is None or self.eckey.curve != keytype:
            raise InvalidOption("SingleKey device key type can't be changed.")

    def get_key_type(self):
        if self.eckey is None:
            return None
        return self.eckey.curve

    def set_key_type(self, ktype):
        """Select the key type to use"""
        if ktype == "K1":
            if hasattr(self, "eckey_k1"):
                self.eckey = self.eckey_k1
            else:
                self.try_keep_keytype(ktype)
        # if ktype == "R1":
        # if hasattr(self, "eckey_r1"):
        # self.eckey = self.eckey_r1
        # else:
        # self.try_keep_keytype(ktype)
        elif ktype == "ED":
            if hasattr(self, "eckey_ed"):
                self.eckey = self.eckey_ed
            else:
                self.try_keep_keytype(ktype)
        else:
            raise Exception("SingleKey only manages K1 or ED key type")

    def load_key(self, ecpair_obj):
        self.eckey = ecpair_obj

    def initialize_device(self):
        """Generate a new key"""
        # K1 cardinal is used whatever the key type
        pvkey_int = randbelow(CURVE_K1_ORDER)
        self.open_account_fromint(pvkey_int)
        self.created = True
        return pvkey_int

    def get_public_key(self, compressed=True):
        # compressed has no effect if type is Ed
        return self.eckey.get_public_key(compressed).hex()

    def sign(self, hashed_msg):
        # If Ed, hashed_msg is the full message
        return self.eckey.sign(hashed_msg)
