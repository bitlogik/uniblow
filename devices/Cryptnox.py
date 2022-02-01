#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Cryptnox card device
# Copyright (C) 2022 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


from devices.BaseDevice import BaseDevice
from devices.cryptnox import CryptnoxCard, Basic_Pairing_Secret
from cryptolib.HDwallet import encode_bip39_string

from logging import getLogger

logger = getLogger(__name__)


class pwdException(Exception):
    pass


class NotinitException(Exception):
    pass


class Cryptnox(BaseDevice):

    is_init = False
    is_HD = True
    has_password = True
    # has_admin_password = True

    def __init__(self):
        self.created = False
        self.card = None
        self.account = None
        self.aindex = None

    def initialize_device(self, settings):
        self.account = settings["account"]
        self.aindex = settings["index"]
        self.legacy_derive = settings["legacy_path"]

    def open_account(self, password):
        try:
            self.card = CryptnoxCard()
        except Exception:
            raise Exception("Cryptnox not found.")
        self.account = "0"
        self.aindex = "0"
        self.card.open_secure_channel(Basic_Pairing_Secret)
        self.pin = password
        self.pin = "123456"
        try:
            self.card.testPIN(self.pin)
        except Exception as exc:
            if str(exc) == "Error (SCP) : 63C5":
                raise NotinitException

    def get_address_index(self):
        """Get the account address index, last BIP44 derivation number as str"""
        return self.aindex

    def get_account(self):
        """Get the account number, third BIP44 derivation number as str"""
        return self.account

    def derive_key(self, path, key_type):
        self.key_type = key_type
        if key_type not in ["K1", "R1"]:
            raise Exception("Cryptnox supports only K1 and R1 derivations.")
        self.card.derive(encode_bip39_string(path), key_type)

    def get_public_key(self):
        pubkey = self.card.get_pubkey(self.key_type)
        return pubkey

    def sign(self, txdigest):
        return self.card.sign(txdigest, self.key_type, pin=self.pin)
