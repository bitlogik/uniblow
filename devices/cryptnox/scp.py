# -*- coding: utf8 -*-

# Cryptnox Secure Channel Protocol communication for Uniblow
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


"""Cryptnox Secure Channel and crypto protocols."""

from cryptolib.cryptography import (
    sha512,
    aes_encrypt,
    aes_decrypt,
    pad_data,
    unpad_data,
    gen_iv,
    compute_mac,
)
from cryptolib.ECKeyPair import EC_key_pair


# Common public pairing key
# The Basic version can't auth the host, only by PIN
BASIC_PAIRING_SECRET = b"Cryptnox Basic CommonPairingData"


def init_encrypt(session_pubkey, init_data):
    """Encrypt data for the initilalize command."""
    init_key = EC_key_pair(-1, "R1")
    aes_key = init_key.ecdh(session_pubkey)
    iv_val = gen_iv()
    enc_data = aes_encrypt(aes_key, iv_val, pad_data(init_data + BASIC_PAIRING_SECRET))
    init_pubkey = init_key.get_public_key()
    data_frame = [len(init_pubkey)] + list(init_pubkey + iv_val + enc_data)
    return data_frame


class CryptnoxSecureChannel:
    """Cryptnox Secure Channel Protocol"""

    def __init__(self):
        """Start a SCP object."""
        # Generate a host session key
        self.session_key = EC_key_pair(-1, "R1")
        self.aes_key = None
        self.aes_iv = bytes([0x5A] * 16)
        self.mac_key = None
        self.mac_iv = bytes([0] * 16)

    def get_session_pubkey(self):
        """Get the host session public key."""
        return self.session_key.get_public_key()

    def compute_keys(self, card_pubkey, session_salt, pairing_key=BASIC_PAIRING_SECRET):
        """Compute the session keys for this encrypted secure channel."""
        # Compute session keys
        dh_secret = self.session_key.ecdh(card_pubkey)
        session_secrets = sha512(dh_secret + pairing_key + session_salt)
        self.aes_key = session_secrets[:32]
        self.mac_key = session_secrets[32:]

    def encrypt(self, apdu_h, apdu_data, rcv_long_apdu):
        """Encrypt card command."""
        if self.aes_key is None:
            raise Exception("Secured channel was not opened")
        # Encrypt
        datap = pad_data(apdu_data)
        data_enc = aes_encrypt(self.aes_key, self.aes_iv, datap)
        lendata = len(datap) + 16
        # Compute MAC
        if rcv_long_apdu or lendata >= 256:
            cmdh = apdu_h + [0, (lendata) >> 8, (lendata) & 255]
            datamaclist = cmdh + [0] * 9
        else:
            cmdh = apdu_h + [lendata]
            datamaclist = cmdh + [0] * 11
        mac_data = bytes(datamaclist) + data_enc
        self.aes_iv = compute_mac(self.mac_key, self.mac_iv, mac_data)
        return cmdh + list(self.aes_iv + data_enc)

    def decrypt(self, enc_msg):
        """Decrypt card response."""
        resp_bin = bytes(enc_msg)
        resp_data = resp_bin[16:]
        resp_mac = resp_bin[:16]
        lendatarec = len(resp_bin)
        # Check MAC
        if lendatarec >= 256:
            datamaclist = [0, lendatarec >> 8, lendatarec & 255] + [0] * 13
        else:
            datamaclist = [lendatarec & 255] + [0] * 15
        mac_data = bytes(datamaclist) + resp_data
        mac_value = compute_mac(self.mac_key, self.mac_iv, mac_data)
        if mac_value != resp_mac:
            raise Exception("Error (SCP) : Bad MAC received")
        # Decrypt response
        try:
            datadec = unpad_data(aes_decrypt(self.aes_key, self.aes_iv, resp_data))
        except Exception as exc:
            raise Exception(
                "Error (SCP) : Error during decryption (bad padding, wrong key)"
            ) from exc
        self.aes_iv = resp_mac
        return datadec
