#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Base Device
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

from abc import ABC, abstractmethod


class BaseDevice(ABC):
    # Default values - Override if different
    created = False
    has_password = False
    password_name = "local user password"
    password_min_len = 8
    password_max_len = 24
    is_pin_numeric = False
    default_password = "NoPasswd"
    password_retries_inf = False
    password_softlock = 0
    has_admin_password = False
    admin_pass_name = "Administrator Password"
    admin_pwd_minlen = 8
    admin_pwd_maxlen = 24
    default_admin_password = ""
    is_HD = False
    has_screen = False
    ledger_tokens_compat = False
    has_hardware_button = False
    internally_gen_keys = False
    account = "0"
    aindex = "0"
    legacy_derive = False

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
    def get_public_key(self, cb=None):
        """Provide the public key in bytes X962 format.
        Uncompressed format.
        May have a callback argument if device has screen (to check on screen).
        For EdDSA it provides the "raw" 32 bytes public key.
        """
        pass

    @abstractmethod
    def sign(self, hashed_msg):
        """Sign a hash and return with ASN1 DER encoding.
        In case has_screen :
            hashed_msg is the message, hash is perfomed on device.
            For EVM, return v,r,s.
        For EdDSA it returns the "raw" 64 bytes RS signature.
        """
        pass
