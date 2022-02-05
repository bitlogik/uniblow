#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Ledger hardware device for EVM
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

from logging import getLogger

from devices.BaseDevice import BaseDevice
from devices.ledger.ledgerComm import getDongle
from devices.ledger.ledgerException import LedgerException
from cryptolib.HDwallet import encode_bip39_string, BIP32node

logger = getLogger(__name__)


class NotinitException(Exception):
    pass


LEDGER_CLASS = 0xE0
INSTRUCTION_GETPUBKEY = 0x02
INSTRUCTION_GETAPPDATA = 0x06
INSTRUCTION_SIGN = 0x04
INSTRUCTION_SIGNMESSAGE = 0x08
INSTRUCTION_SIGN712 = 0x0C
INSTRUCTION_SENDTOKENDATA = 0x0A
MINIMUM_APP_VERSION = 0x010500


def unpack_vrs(vrsbin):
    """Provide serialized vrs as 3 integers."""
    v = int.from_bytes(vrsbin[:1], "big")
    r = int.from_bytes(vrsbin[1:33], "big")
    s = int.from_bytes(vrsbin[33:65], "big")
    return v, r, s


class Ledger(BaseDevice):

    is_init = False
    is_HD = True
    has_screen = True
    ledger_tokens_compat = True
    has_hardware_button = True
    internally_gen_keys = True

    def __init__(self):
        self.created = False
        self.ledger_device = None
        self.bin_path = None
        self.account = None
        self.aindex = None

    def initialize_device(self, settings):
        self.account = settings["account"]
        self.aindex = settings["index"]
        self.legacy_derive = settings["legacy_path"]

    def open_account(self):
        try:
            self.ledger_device = getDongle()
        except Exception:
            raise Exception("Ledger not found. Connect it and unlock. In Linux, allow udev rules.")
        try:
            apdu = [LEDGER_CLASS, INSTRUCTION_GETAPPDATA, 0x00, 0x00, 0x00]
            eth_app_info = self.ledger_device.exchange(bytearray(apdu))
        except LedgerException as exc:
            if exc.sw == 0x6D00:
                raise Exception("Error in Ledger. Did you open the Ethereum app in the Ledger?")
            if exc.sw == 0x6D02:
                raise Exception(
                    "No app started in the Ledger. "
                    "Install and open the Ethereum app in the Ledger."
                )
            raise Exception(f"Error {hex(exc.sw)} in Ledger.")
        eth_version = f"{eth_app_info[1]}.{eth_app_info[2]}.{eth_app_info[3]}"
        logger.debug(f"Ledger ETH app version {eth_version}")
        if int.from_bytes(eth_app_info[1:4], "big") < MINIMUM_APP_VERSION:
            raise Exception("The Ethereum app installed in the Ledger must be at least v1.5.0.")
        if self.account is None:
            raise NotinitException

    def get_address_index(self):
        """Get the account address index, last BIP44 derivation number as str"""
        return self.aindex

    def get_account(self):
        """Get the account number, third BIP44 derivation number as str"""
        return self.account

    def derive_key(self, path, key_type):
        # Check k1 ?
        path_bin = encode_bip39_string(path)
        self.bin_path = bytes([len(path_bin) >> 2]) + path_bin

    def get_public_key(self, showOnScreenCB=None):
        result = {}
        apdu = [
            LEDGER_CLASS,
            INSTRUCTION_GETPUBKEY,
            0x00 if showOnScreenCB is None else 0x01,
            0x00,
            len(self.bin_path),
        ]
        apdu.extend(self.bin_path)
        approved = False
        try:
            response = self.ledger_device.exchange(bytearray(apdu))
            approved = True
        except LedgerException as exc:
            if exc.sw == 0x6B0C:
                raise Exception("Ledger is locked. Unlock it and retry.")
            if exc.sw == 0x6511:
                raise Exception(
                    "No app started in the Ledger. Install and open "
                    "the Ethereum app in the Ledger."
                )
            if exc.sw == 0x6A15:
                raise Exception("Error in Ledger. Did you open the Ethereum app in the Ledger?")
            if exc.message == "Invalid channel":
                raise Exception(
                    "Error communicating with the Ledger. Please lock or close any web3 wallet "
                    "which can interfer with the Ledger : Metamask, Frame, Rabby, LedgerLive,..."
                )
            if exc.sw == 0x6F00:
                raise Exception(exc.message)
            if exc.sw != 0x6985:
                raise Exception(f"Ledger error {hex(exc.sw)}")
        if showOnScreenCB is not None:
            showOnScreenCB(approved)
        if approved:
            offset = 0
            result["publicKey"] = response[offset + 1 : offset + 1 + response[offset]]
            offset = offset + 1 + response[offset]
            result["address"] = str(response[offset + 1 : offset + 1 + response[offset]])
            offset = offset + 1 + response[offset]
            return result["publicKey"]

    def register_token(
        self, token_name, token_addr, token_decimals, chain_id, ledger_signature_hex
    ):
        """Send the trusted token information in to the Ledger."""
        # used when ledger_tokens_compat
        ledger_signature = bytes.fromhex(ledger_signature_hex)
        token_name_bin = token_name.encode("utf8")
        token_name_len = len(token_name_bin)
        apdu = [
            LEDGER_CLASS,
            INSTRUCTION_SENDTOKENDATA,
            0x00,
            0x00,
            29 + token_name_len + len(ledger_signature),
            token_name_len,
        ]
        apdu.extend(token_name_bin)
        apdu.extend(bytes.fromhex(token_addr))
        apdu.extend(BIP32node.ser32(token_decimals))
        apdu.extend(BIP32node.ser32(chain_id))
        apdu.extend(ledger_signature)
        self.ledger_device.exchange(bytearray(apdu))

    def sign(self, transaction):
        apdu = [LEDGER_CLASS, INSTRUCTION_SIGN, 0x00, 0x00, len(self.bin_path) + len(transaction)]
        apdu.extend(self.bin_path)
        apdu.extend(transaction)
        try:
            vrs_bin = self.ledger_device.exchange(bytearray(apdu))
        except LedgerException as exc:
            if exc.sw == 0x6A80:
                raise Exception(
                    "This transaction requires to enable blind signing in the Ledger app settings."
                )
            if exc.sw == 0x6985:
                raise Exception("You rejected the transaction.")
            raise Exception(str(exc))
        return unpack_vrs(vrs_bin)

    def sign_message(self, message):
        """Sign a personnal message, used when has_screen"""
        msg_sz = len(message)
        assert msg_sz < 225
        apdu = [LEDGER_CLASS, INSTRUCTION_SIGNMESSAGE, 0x00, 0x00, len(self.bin_path) + msg_sz + 4]
        apdu.extend(self.bin_path)
        apdu.extend(BIP32node.ser32(msg_sz))
        apdu.extend(message)
        try:
            vrs_bin = self.ledger_device.exchange(bytearray(apdu))
        except LedgerException as exc:
            if exc.sw == 0x6985:
                raise Exception("You rejected the message signature.")
            raise Exception(str(exc))
        return unpack_vrs(vrs_bin)

    def sign_eip712(self, domain_hash, message_hash):
        """Sign an EIP712 typed hash request, used when has_screen"""
        assert len(domain_hash) == 32
        assert len(message_hash) == 32
        apdu = [LEDGER_CLASS, INSTRUCTION_SIGN712, 0x00, 0x00, len(self.bin_path) + 64]
        apdu.extend(self.bin_path)
        apdu.extend(domain_hash)
        apdu.extend(message_hash)
        try:
            vrs_bin = self.ledger_device.exchange(bytearray(apdu))
        except LedgerException as exc:
            if exc.sw == 0x6985:
                raise Exception("You rejected the message signature.")
            raise Exception(str(exc))
        return unpack_vrs(vrs_bin)
