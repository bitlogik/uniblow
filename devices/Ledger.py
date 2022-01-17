#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Ledger hardware device
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


from devices.btchip.btchipComm import getDongle
from devices.btchip.btchipHelpers import parse_bip32_path, read_uint8, read_uint256
from devices.btchip.btchipException import BTChipException


class NotinitException(Exception):
    pass


class Ledger:

    has_password = False
    has_admin_password = False
    is_HD = True
    is_hardware = True

    def __init__(self):
        self.created = False
        self.has_hardware_button = True
        self.account = "0"
        self.aindex = "0"
        self.ledger_device = None
        self.bin_path = None

    def open_account(self):
        try:
            self.ledger_device = getDongle()
        except:
            raise Exception("Ledger not found. In Linux, allow udev rules.")

    def get_address_index(self):
        """Get the account address index, last BIP44 derivation number as str"""
        return self.aindex

    def get_account(self):
        """Get the account number, third BIP44 derivation number as str"""
        return self.account

    def derive_key(self, path, key_type):
        self.bin_path = parse_bip32_path(path[2:])

    def get_public_key(self):
        result = {}
        showOnScreen = False
        # P2 : 00 not returning chain code, 01 give chain code
        apdu = [0xE0, 0x02, 0x01 if showOnScreen else 0x00, 00, len(self.bin_path)]
        apdu.extend(self.bin_path)
        try:
            response = self.ledger_device.exchange(bytearray(apdu))
        except BTChipException as exc:
            if exc.sw == 0x6B0C:
                raise Exception("Ledger is locked. Unlock it and retry.")
            if exc.sw == 0x6511:
                raise Exception("No app started in the Ledger.")
            if exc.sw == 0x6A15:
                raise Exception("Error in Ledger. Did you open the right app in the Ledger?")
            if exc.sw == 0x6F00:
                raise Exception(exc.message)
            raise Exception(f"Ledger error {hex(exc.sw)}")
        offset = 0
        result["publicKey"] = response[offset + 1 : offset + 1 + response[offset]]
        offset = offset + 1 + response[offset]
        result["address"] = str(response[offset + 1 : offset + 1 + response[offset]])
        offset = offset + 1 + response[offset]
        return result["publicKey"].hex()

    def sign(self, transaction):
        apdu = [0xE0, 0x04, 0x00, 0x00, len(self.bin_path) + len(transaction)]
        apdu.extend(self.bin_path)
        apdu.extend(transaction)
        try:
            vrs_bin = self.ledger_device.exchange(bytearray(apdu))
        except BTChipException as exc:
            if exc.sw == 0x6A80:
                raise Exception("This transaction requires to enable blind signing in the app settings.")
            if exc.sw == 0x6985:
                raise Exception("You rejected the transaction.")
            raise Exception(exc.sw)
        v = read_uint8(vrs_bin, 0)
        r = read_uint256(vrs_bin, 1)
        s = read_uint256(vrs_bin, 33)
        return v, r, s
