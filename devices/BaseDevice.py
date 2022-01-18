#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Base Device
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

from abc import ABC, abstractmethod


class BaseDevice(ABC):

    # Default values - Override if different
    created = False
    has_password = False
    has_admin_password = False
    is_HD = False
    is_hardware = False
    has_hardware_button = False
    account = "0"
    aindex = "0"

    @abstractmethod
    def open_account(self):
        """Start/connect to the device."""
        pass

    def set_key_type(self, ktype):
        """Set the wallet key type as "K1", "R1", or "ED". In case not is_HD."""
        pass

    def initialize_device(self, settings):
        """Setup and generate the device keys in case has_password and can be created in Uniblow.
        settings is the password string.
        In case is_HD, settings is {"mnemonic":"", "HD_password":"", "seed_gen":hd_type}
        """
        pass

    def set_admin(self, admin_password):
        """Setup the admin password in case has_admin_password."""
        pass

    def get_address_index(self):
        """Get the address index, in case is_HD."""
        pass

    def get_account(self):
        """Get the account number, in case is_HD."""
        pass

    def derive_key(self, path, key_type):
        """Setup the device to use the key at the given SLIP10/BIP39 path, in case is_HD."""
        pass

    @abstractmethod
    def get_public_key(self):
        """Provide the publie key in hex X962.
        Compressed format, can be provided uncompressed for EVM wallets.
        For EdDSA provide the "raw" 32 bytes public key in hex.
        """
        pass

    @abstractmethod
    def sign(self, hashed_msg):
        """Sign a hash and return with ASN DER encoding.
        For EdDSA it returns the "raw" 64 bytes RS signature in hex.
        And in case is_hardware : return v,r,s for EVM transactions.
        """
        pass
