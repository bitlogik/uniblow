#!/usr/bin/python3
# -*- coding: utf8 -*-

# Satochip smartcard secure channel
# Copyright (C) 2023  BitLogiK & Satochip

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import hmac
import logging
from os import urandom
from hashlib import sha1

from cryptolib.cryptography import (
    aes_encrypt,
    aes_decrypt,
    append_PKCS7_padding,
    strip_PKCS7_padding,
)
from cryptolib.ECKeyPair import EC_key_pair
from cryptolib.uintEncode import ser32


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SecureChannel:
    def __init__(self, loglevel=logging.WARNING):
        logger.setLevel(loglevel)
        logger.debug("In __init__")
        self.initialized_secure_channel = False
        self.sc_IV = None
        self.sc_IVcounter = None
        self.shared_key = None
        self.derived_key = None
        self.mac_key = None

        # ecdh keypair
        self.sc_peer_pubkey = None
        self.ecdh_key = EC_key_pair(-1, "K1")  # generate new keypair
        self.sc_pubkey_serialized = self.ecdh_key.get_public_key(compressed=False)
        # logger.debug(f"In __init__ self.sc_pubkey_serialized: {self.sc_pubkey_serialized.hex()}")

    def initiate_secure_channel(self, peer_pubkey_bytes):
        logger.debug("In initiate_secure_channel()")

        self.sc_IVcounter = 1

        # generate shared secret through ECDH
        self.shared_key = self.ecdh_key.ecdh(peer_pubkey_bytes)
        # logger.debug("Shared key:"+ self.shared_key.hex()) #debug

        mac = hmac.new(self.shared_key, "sc_key".encode("utf-8"), sha1)
        self.derived_key = mac.digest()[:16]
        mac = hmac.new(self.shared_key, "sc_mac".encode("utf-8"), sha1)
        self.mac_key = mac.digest()

        # logger.debug("Derived_key key:"+ self.derived_key.hex()) #debug
        # logger.debug("Mac_key key:"+ self.mac_key.hex()) #debug

        self.initialized_secure_channel = True

    def encrypt_secure_channel(self, data_bytes):
        logger.debug("In encrypt_secure_channel()")
        if not self.initialized_secure_channel:
            raise UninitializedSecureChannelError("Secure channel is not initialized")

        key = self.derived_key
        iv = urandom(12) + ser32(self.sc_IVcounter)
        ciphertext = aes_encrypt(key, iv, append_PKCS7_padding(data_bytes))

        self.sc_IVcounter += 2

        data_to_mac = iv + len(ciphertext).to_bytes(2, byteorder="big") + ciphertext
        mac = hmac.new(self.mac_key, data_to_mac, sha1).digest()

        return (iv, ciphertext, mac)

    def decrypt_secure_channel(self, iv, ciphertext):
        logger.debug("In decrypt_secure_channel()")
        if not self.initialized_secure_channel:
            raise UninitializedSecureChannelError("Secure channel is not initialized")

        key = self.derived_key
        decrypted = strip_PKCS7_padding(aes_decrypt(key, iv, ciphertext))

        return list(decrypted)


class UninitializedSecureChannelError(Exception):
    """Raised when the secure channel is not initialized"""

    pass
