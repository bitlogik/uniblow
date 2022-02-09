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
from devices.cryptnox import CryptnoxCard, CryptnoxInvalidException
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
    password_max_len = 9
    is_pin_numeric = True
    password_retries_inf = False
    password_softlock = 3
    default_password = "1234"
    admin_pass_name = "admin code"
    admin_pwd_minlen = 12
    admin_pwd_maxlen = 12
    default_admin_password = "123456789012"
    internally_gen_keys = False
    basic_card_id = 0x42

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
        self.card.init("Init by Uniblow", " ", settings["file_password"], self.PUK)
        delattr(self, "PUK")
        # Now upload the seed in the Cryptnox
        self.card.open_secure_channel()
        self.card.load_seed(seedg, self.pin)

    def open_account(self, password):
        if not self.card.initialized:
            raise NotinitException()
        if not self.card.seeded:
            # Must be initalized and seeded
            raise Exception("Reset or inject/generate a key in this Cryptnox card.")
        # Check PIN auth enabled
        if not self.card.pinauth:
            raise Exception(
                "PIN auth needs to be enabled in the Cryptnox card to be used with uniblow."
            )
        self.account = "0"
        self.aindex = "0"
        try:
            self.card.open_secure_channel()
        except Exception as exc:
            if str(exc).endswith("disconnected."):
                raise exc
            raise Exception(
                "Error while opening the Cryptnox encrypted tunnel.\n\n"
                "Possible causes :\n"
                " * Invalid PairingKey for this card \n"
                " * Card is fake, not genuine\n"
                " * Card was disconnected from the reader\n\n"
                "Log of the error :\n" + str(exc)
            )
        # Check the key loaded is a HD seed key
        card_info = self.card.get_card_info()
        if card_info.key_type not in ["X", "S", "D", "L"]:
            raise Exception("This Cryptnox card wasn't setup with a derivable key type.")
        try:
            self.card.testPIN(password)
        except Exception as exc:
            if str(exc).startswith("Error (SCP) : 63C"):
                raise pwdException(str(exc)[-1])
            if exc == "Error (SCP) : 6700":
                raise Exception("PIN input is too long")
            raise exc
        self.pin = password

    def get_pw_left(self):
        """When has_password and not password_retries_inf"""
        self.card.open_secure_channel()
        return self.card.get_pin_left()

    def is_init(self):
        """Required when has_password and not password_retries_inf"""
        try:
            self.card = CryptnoxCard()
        except CryptnoxInvalidException as exc:
            raise exc
        except Exception:
            raise Exception("No Cryptnox card found.")
        # Check card version must be Basic
        if self.card.cardtype != Cryptnox.basic_card_id:
            raise Exception("Cryptnox compatible with uniblow are only BG-1 models.")
        # Check minimal applet version
        if int.from_bytes(self.card.applet_version, "big") < 0x010202:
            raise Exception("Cryptnox firmware is too old. Required v>=1.2.2")
        isinit = self.card.initialized
        return isinit

    def generate_mnemonic(self):
        return generate_mnemonic(12)

    def set_admin(self, PUKcode):
        self.PUK = PUKcode.encode("utf8")

    def set_path(self, settings):
        self.account = settings["account"]
        self.aindex = settings["index"]

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
