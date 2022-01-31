#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Basic File key device
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


from os import path
from secrets import token_bytes

import nacl.exceptions
import nacl.pwhash
import nacl.secret
from devices.file_path import WalletFile
from devices.SingleKey import SKdevice

EC_BYTES_SIZE = 32

FILE_NAME = "BasicFileWallet.key"


class pwdException(nacl.exceptions.CryptoError):
    pass


class NotinitException(Exception):
    pass


class BasicFile(SKdevice):
    """Single key wallet, with file read/save."""

    def open_account(self, password):
        wallet_file = WalletFile(FILE_NAME)
        if path.isfile(wallet_file.file_path):
            # Open the current key from its file
            key_content = wallet_file.read_data()
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
                key_data = nacl.secret.SecretBox(decryption_key).decrypt(
                    bytes.fromhex(key_content["keyenc"])
                )
            except nacl.exceptions.CryptoError:
                raise pwdException("BadPass")
            # load private key
            pvkey_int = int.from_bytes(key_data, "big")
            super().open_account_fromint(pvkey_int)
        else:
            raise NotinitException()

    def initialize_device(self, password):
        # Generate a new key and save it in a file
        pvkey_int = super().initialize_device()
        # Encrypt the private key
        salt = token_bytes(nacl.pwhash.argon2i.SALTBYTES)
        encryption_key = nacl.pwhash.argon2id.kdf(
            nacl.secret.SecretBox.KEY_SIZE,
            password.encode("utf8"),
            salt,
            opslimit=nacl.pwhash.argon2i.OPSLIMIT_MODERATE,
            memlimit=nacl.pwhash.argon2i.MEMLIMIT_MODERATE,
        )
        encrypted_content = nacl.secret.SecretBox(encryption_key).encrypt(
            pvkey_int.to_bytes(EC_BYTES_SIZE, byteorder="big"),
            nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE),
        )
        # Save the encrypted data
        wallet_file = WalletFile(FILE_NAME)
        wallet_file.save_data({"keyenc": encrypted_content.hex(), "salt": salt.hex()})
        self.created = True
