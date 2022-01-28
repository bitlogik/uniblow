#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Ledger hardware device for EVM
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

from logging import getLogger

from devices.BaseDevice import BaseDevice
from devices.btchip.btchipComm import getDongle
from devices.btchip.btchipHelpers import parse_bip32_path, writeUint32BE, read_uint8, read_uint256
from devices.btchip.btchipException import BTChipException


logger = getLogger(__name__)


class NotinitException(Exception):
    pass


def unpack_vrs(vrsbin):
    """Provide serialized vrs as 3 integers."""
    v = read_uint8(vrsbin, 0)
    r = read_uint256(vrsbin, 1)
    s = read_uint256(vrsbin, 33)
    return v, r, s


class Ledger(BaseDevice):

    is_HD = True
    has_screen = True
    ledger_tokens_compat = True
    has_hardware_button = True

    def __init__(self):
        self.created = False
        self.ledger_device = None
        self.bin_path = None

    def open_account(self):
        try:
            self.ledger_device = getDongle()
        except:
            raise Exception("Ledger not found. Connect it and unlock. In Linux, allow udev rules.")
        try:
            apdu = [0xE0, 0x06, 0x00, 0x00, 0x00, 0x04]
            eth_app_info = self.ledger_device.exchange(bytearray(apdu))
        except BTChipException as exc:
            if exc.sw == 0x6D00:
                raise Exception("Error in Ledger. Did you open the Ethereum app in the Ledger?")
            if exc.sw == 0x6D02:
                raise Exception(
                    "No app started in the Ledger. Install and open the Ethereum app in the Ledger."
                )
            raise Exception(f"Error {hex(exc.sw)} in Ledger.")
        eth_version = f"{eth_app_info[1]}.{eth_app_info[2]}.{eth_app_info[3]}"
        logger.debug(f"Ledger ETH app version {eth_version}")

    def get_address_index(self):
        """Get the account address index, last BIP44 derivation number as str"""
        return self.aindex

    def get_account(self):
        """Get the account number, third BIP44 derivation number as str"""
        return self.account

    def derive_key(self, path, key_type):
        self.bin_path = parse_bip32_path(path[2:])

    def get_public_key(self, showOnScreenCB=None):
        result = {}
        apdu = [0xE0, 0x02, 0x00 if showOnScreenCB is None else 0x01, 00, len(self.bin_path)]
        apdu.extend(self.bin_path)
        approved = False
        try:
            response = self.ledger_device.exchange(bytearray(apdu))
            approved = True
        except BTChipException as exc:
            if exc.sw == 0x6B0C:
                raise Exception("Ledger is locked. Unlock it and retry.")
            if exc.sw == 0x6511:
                raise Exception(
                    "No app started in the Ledger. Install and open the Ethereum app in the Ledger."
                )
            if exc.sw == 0x6A15:
                raise Exception("Error in Ledger. Did you open the Ethereum app in the Ledger?")
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
            return result["publicKey"].hex()

    def register_token(
        self, token_name, token_addr, token_decimals, chain_id, ledger_signature_hex
    ):
        """Send the trusted token information in to the Ledger."""
        # used when ledger_tokens_compat
        ledger_signature = bytes.fromhex(ledger_signature_hex)
        token_name_bin = token_name.encode("utf8")
        token_name_len = len(token_name_bin)
        apdu = [0xE0, 0x0A, 0x00, 0x00, 29 + token_name_len + len(ledger_signature), token_name_len]
        apdu.extend(token_name_bin)
        apdu.extend(bytes.fromhex(token_addr))
        apdu.extend(writeUint32BE(token_decimals))
        apdu.extend(writeUint32BE(chain_id))
        apdu.extend(ledger_signature)
        self.ledger_device.exchange(bytearray(apdu))

    def sign(self, transaction):
        apdu = [0xE0, 0x04, 0x00, 0x00, len(self.bin_path) + len(transaction)]
        apdu.extend(self.bin_path)
        apdu.extend(transaction)
        try:
            vrs_bin = self.ledger_device.exchange(bytearray(apdu))
        except BTChipException as exc:
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
        apdu = [0xE0, 0x08, 0x00, 0x00, len(self.bin_path) + msg_sz + 4]
        apdu.extend(self.bin_path)
        apdu.extend(writeUint32BE(msg_sz))
        apdu.extend(message)
        try:
            vrs_bin = self.ledger_device.exchange(bytearray(apdu))
        except BTChipException as exc:
            if exc.sw == 0x6985:
                raise Exception("You rejected the message signature.")
            raise Exception(str(exc))
        return unpack_vrs(vrs_bin)

    def sign_eip712(self, domain_hash, message_hash):
        """Sign an EIP712 typed hash request, used when has_screen"""
        # version 0 ?
        assert len(domain_hash) == 32
        assert len(message_hash) == 32
        apdu = [0xE0, 0x0C, 0x00, 0x00, len(self.bin_path) + 64]
        apdu.extend(self.bin_path)
        apdu.extend(domain_hash)
        apdu.extend(message_hash)
        try:
            vrs_bin = self.ledger_device.exchange(bytearray(apdu))
        except BTChipException as exc:
            if exc.sw == 0x6985:
                raise Exception("You rejected the message signature.")
            raise Exception(str(exc))
        return unpack_vrs(vrs_bin)
