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
from secrets import randbelow, token_bytes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
import nacl.exceptions
import nacl.pwhash
import nacl.secret
import nacl.utils

import wallets.lib

CURVE_K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
EC_BYTES_SIZE = 32

FILE_NAME = "HDseed.key"


class pwdException(nacl.exceptions.CryptoError):
    pass


class NotinitException(Exception):
    pass


def encode_int(intarray):
    # encode a bytes array to a DER integer (bytes list)
    if intarray[0] >= 128:
        return [2, len(intarray) + 1, 0, *intarray]
    if intarray[0] == 0:
        return encode_int(intarray[1:])
    return [2, len(intarray), *intarray]


def encode_der_s(int_r, int_s):
    # Encode raw signature R|S (2x EC size bytes) into ASN1 DER
    # Enforce low S
    array_r = encode_int(int_r.to_bytes(EC_BYTES_SIZE, byteorder="big"))
    if int_s > (CURVE_K1_ORDER >> 1):
        s_data = (CURVE_K1_ORDER - int_s).to_bytes(EC_BYTES_SIZE, byteorder="big")
        array_s = encode_int(s_data)
    else:
        array_s = encode_int(int_s.to_bytes(EC_BYTES_SIZE, byteorder="big"))
    return bytes([0x30, len(array_r) + len(array_s), *array_r, *array_s])


def fix_s_sig(sig):
    # DER to DER with low S
    if sig[0] != 0x30:
        raise Exception("Wrong signature header")
    if sig[2] != 0x02:
        raise Exception("Wrong signature format")
    rlen = sig[3]
    r_value = int.from_bytes(sig[4 : 4 + rlen], "big")
    slen = sig[5 + rlen]
    s_value = int.from_bytes(sig[6 + rlen : 6 + rlen + slen], "big")
    if sig[1] != 4 + rlen + slen or len(sig) != 6 + rlen + slen:
        raise Exception("Wrong signature encoding")
    return encode_der_s(r_value, s_value)


class HDdevice:
    # Using Python cryptography lib

    has_password = True
    has_admin_password = False
    is_HD = True

    def __init__(self):
        self.created = False
        self.has_hardware_button = False

    def open_account(self, password):
        if path.isfile(FILE_NAME):
            # Open the current key from its file
            key_file = open(FILE_NAME, "r")
            key_content = json.load(key_file)
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
            # Compute master key from seed
            self.master_key = wallets.lib.cryptos.deterministic.bip32_master_key(seed)
            key_file.close()
        else:
            raise NotinitException()

    def generate_mnemonic(self):
        random_entropy = nacl.utils.random(32)
        return wallets.lib.cryptos.mnemonic.entropy_to_words(random_entropy)

    def check_mnemonic(self, mnemonic):
        # reutrn checksum_valid, wordlist_valid (bool, bool)
        return wallets.lib.cryptos.mnemonic.bip39_is_checksum_valid(mnemonic)

    def initialize_device(self, password, mnemonic):
        # Save the seed from the mnemonic in a file
        key_file = open(FILE_NAME, "w")
        # compute the seed
        seedg = wallets.lib.cryptos.mnemonic.mnemonic_to_seed(mnemonic)
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
            seedg,
            nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE),
        )
        # Save the encrypted data
        json.dump({"seed_enc": encrypted_content.hex(), "salt": salt.hex()}, key_file)
        key_file.close()
        self.created = True
        self.master_key = wallets.lib.cryptos.deterministic.bip32_master_key(seedg)

    def derive_key(self, path):
        pvkey_int = int(
            wallets.lib.cryptos.deterministic.bip32_descend(self.master_key, path)[:-2], 16
        )
        self.pvkey = ec.derive_private_key(pvkey_int, ec.SECP256K1())

    def get_public_key(self):
        return (
            self.pvkey.public_key()
            .public_bytes(serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint)
            .hex()
        )

    def sign(self, hashed_msg):
        raw_sig = self.pvkey.sign(hashed_msg, ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        return fix_s_sig(raw_sig)
