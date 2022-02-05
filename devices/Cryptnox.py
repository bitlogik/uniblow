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
from cryptolib.HDwallet import encode_bip39_string, mnemonic_to_seed, generate_mnemonic

from logging import getLogger

logger = getLogger(__name__)


class pwdException(Exception):
    pass


class NotinitException(Exception):
    pass


class Cryptnox(BaseDevice):

    is_HD = True
    has_password = True
    has_admin_password = True
    password_name = "PIN"
    password_min_len = 4
    default_password = "1234"
    admin_pass_name = "admin code"
    admin_pwd_minlen = 12
    default_admin_password = "123456789012"
    internally_gen_keys = False
    password_retries_inf = False

    def __init__(self):
        self.created = False
        self.card = None
        self.account = None
        self.aindex = None

    def initialize_device(self, settings):
        self.account = settings["account"]
        self.aindex = settings["index"]
        # Compute the seed
        seedg = mnemonic_to_seed(
            settings["mnemonic"], settings["HD_password"], method=settings["seed_gen"]
        )
        # Initialize the Cryptnox card
        self.pin = settings["file_password"]
        logger.debug("PIN %s", self.pin)
        logger.debug("PUK %s", self.PUK)
        self.card.init("Init by Uniblow", "aaaa", settings["file_password"], self.PUK)
        delattr(self, "PUK")
        # Now upload the seed in the Cryptnox
        self.card.open_secure_channel(Basic_Pairing_Secret)
        self.card.load_seed(seedg, self.pin)

    def open_account(self, password):
        try:
            self.card = CryptnoxCard()
        except Exception:
            raise Exception("Cryptnox not found.")
        # ToDo : Check minimal applet version
        if not self.card.initialized:
            raise NotinitException()
        if not self.card.seeded:
            raise Exception("Reset or inject a key in this Cryptnox card.")
        # Todo Check the key loaded is a HD seed key
        self.account = "0"
        self.aindex = "0"
        try:
            self.card.open_secure_channel(Basic_Pairing_Secret)
        except Exception as exc:
            raise Exception("Invalid pairing key for this card.", str(exc))
        try:
            self.card.testPIN(password)
        except Exception as exc:
            if str(exc).startswith("Error (SCP) : 63C"):
                delattr(self, "card")
                self.card = None
                raise pwdException
        self.pin = password

    def get_pw_left(self):
        """When has_password and not password_retries_inf"""
        try:
            card = CryptnoxCard()
        except Exception:
            raise Exception("Cryptnox not found.")
        card.open_secure_channel(Basic_Pairing_Secret)
        tries_left = card.get_pin_left()
        del card
        return tries_left

    def is_init(self):
        """Required when has_password and not password_retries_inf"""
        try:
            card = CryptnoxCard()
        except Exception:
            raise Exception("Cryptnox not found.")
        # ToDo check card version must be Basic
        # ToDo Check PIN auth enabled
        isinit = card.initialized
        del card
        return isinit

    def generate_mnemonic(self):
        return generate_mnemonic(12)

    def set_admin(self, PUKcode):
        self.PUK = PUKcode.encode("utf8")

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
