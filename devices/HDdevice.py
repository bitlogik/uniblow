#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Basic File Wallet manager
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


import json
from os import path
from secrets import token_bytes
import nacl.exceptions
import nacl.pwhash
import nacl.secret
import nacl.utils

from cryptolib.HDwallet import (
    HD_Wallet,
    bip39_is_checksum_valid,
    mnemonic_to_seed,
    generate_mnemonic,
)


FILE_NAME = "HDseed.key"


class pwdException(nacl.exceptions.CryptoError):
    pass


class NotinitException(Exception):
    pass


class HDdevice:
    # Using Python cryptography lib

    has_password = True
    has_admin_password = False
    is_HD = True

    def __init__(self):
        self.created = False
        self.has_hardware_button = False
        self.aindex = "0"

    def open_account(self, password):
        if path.isfile(FILE_NAME):
            # Open the current key from its file
            key_file = open(FILE_NAME, "r")
            try:
                key_content = json.load(key_file)
            finally:
                key_file.close()
            salt = bytes.fromhex(key_content["salt"])
            # decrypt
            decryption_key = nacl.pwhash.argon2id.kdf(
                nacl.secret.SecretBox.KEY_SIZE,
                password.encode("utf8"),
                salt,
                opslimit=nacl.pwhash.argon2i.OPSLIMIT_MODERATE,
                memlimit=nacl.pwhash.argon2i.MEMLIMIT_MODERATE,
            )
            try:
                seed = nacl.secret.SecretBox(decryption_key).decrypt(
                    bytes.fromhex(key_content["seed_enc"])
                )
            except nacl.exceptions.CryptoError:
                raise pwdException("BadPass")
            idx = key_content.get("account_number")
            if idx:
                self.aindex = idx
            # Compute master key from seed
            self.master_node = HD_Wallet.from_seed(seed)
        else:
            raise NotinitException()

    def generate_mnemonic(self):
        return generate_mnemonic(12)

    def check_mnemonic(self, mnemonic):
        # return checksum_valid, wordlist_valid (bool, bool)
        return bip39_is_checksum_valid(mnemonic)

    def initialize_device(self, settings):
        # Save the seed from the mnemonic in a file
        key_file = open(FILE_NAME, "w")
        # compute the seed
        seedg = mnemonic_to_seed(
            settings["mnemonic"], settings["HD_password"], method=settings["seed_gen"]
        )
        # Encrypt the private key
        salt = token_bytes(nacl.pwhash.argon2i.SALTBYTES)
        encryption_key = nacl.pwhash.argon2id.kdf(
            nacl.secret.SecretBox.KEY_SIZE,
            settings["file_password"].encode("utf8"),
            salt,
            opslimit=nacl.pwhash.argon2i.OPSLIMIT_MODERATE,
            memlimit=nacl.pwhash.argon2i.MEMLIMIT_MODERATE,
        )
        encrypted_content = nacl.secret.SecretBox(encryption_key).encrypt(
            seedg,
            nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE),
        )
        # Save the encrypted data
        json.dump({"seed_enc": encrypted_content.hex(), "salt": salt.hex()}, key_file)
        key_file.close()
        self.aindex = settings["account_index"]
        self.created = True
        self.master_node = HD_Wallet.from_seed(seedg)

    def get_address_index(self):
        """Get the account address index, last BIP44 derivation number as str"""
        return self.aindex

    def derive_key(self, path):
        self.pvkey = self.master_node.derive_key(path)

    def get_public_key(self):
        return self.pvkey.get_public_key().hex()

    def sign(self, hashed_msg):
        return self.pvkey.sign(hashed_msg)
