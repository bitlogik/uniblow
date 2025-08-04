#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW OpenPGP Wallet manager
# Copyright (C) 2021-2025 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


import OpenPGPpy
from cryptolib.cryptography import encode_der_s
from devices.BaseDevice import BaseDevice


ECDSA_K1 = "132B8104000A"


class pwdException(Exception):
    pass


class NotinitException(Exception):
    pass


def fix_s_sig(sigRS):
    # Quick MPI decoder
    ec_sz = len(sigRS) // 2
    r_value = int.from_bytes(sigRS[:ec_sz], "big")
    s_value = int.from_bytes(sigRS[ec_sz:], "big")
    # to DER with low S
    return encode_der_s(r_value, s_value, "K1")


class OpenPGP(BaseDevice):
    # Using an OpenPGP device

    has_password = True
    has_admin_password = True
    password_name = "PIN"
    password_min_len = 6
    password_retries_inf = False
    admin_pass_name = "Administrator PIN3"
    admin_pwd_minlen = 8
    has_hardware_button = True
    internally_gen_keys = True

    def __init__(self):
        self.PGPdevice = OpenPGPpy.OpenPGPcard()
        self.password_max_len = self.PGPdevice.pw1_maxlen
        self.admin_pwd_maxlen = self.PGPdevice.pw3_maxlen

    def __del__(self):
        if hasattr(self, "PGPdevice"):
            if hasattr(self.PGPdevice, "connection"):
                del self.PGPdevice.connection
            del self.PGPdevice

    def disconnect(self):
        self.__del__()

    def set_key_type(self, ktype):
        if ktype != "K1":
            raise Exception("Incompatible key type. OpenPGP is set to EC 256k1.")

    def set_admin(self, admin_password):
        self.PIN3 = admin_password
        self.PGPdevice.change_pin("12345678", self.PIN3, 3)

    def get_pw_left(self):
        """When has_password and not password_retries_inf"""
        return self.PGPdevice.get_pin_status(1)

    def is_init(self):
        """Required when has_password and not password_retries_inf"""
        try:
            # Check if has a key generated
            self.PGPdevice.get_public_key("B600")
            return True
        except OpenPGPpy.PGPCardException as exc:
            # SW = 0x6581 or 0x6A8x or 0x6F00 ?
            if exc.sw_code not in [0x6581, 0x6A88, 0x6A80, 0x6A82, 0x6F00]:
                raise exc
            return False

    def open_account(self, password):
        self.PIN = password
        try:
            self.PGPdevice.get_public_key("B600")
        except OpenPGPpy.ConnectionException:
            raise Exception("OpenPGP device was disconnected.")
        except OpenPGPpy.PGPCardException as exc:
            # SW = 0x6581 or 0x6A8x or 0x6F00 ?
            if exc.sw_code not in [0x6581, 0x6A88, 0x6A80, 0x6A82, 0x6F00]:
                raise
            # SIGn key is not present
            raise NotinitException()
        if not self.PIN:
            raise pwdException("BadPass")
        try:
            self.PGPdevice.verify_pin(1, self.PIN)
        except OpenPGPpy.ConnectionException:
            raise Exception("OpenPGP device was disconnected.")
        except OpenPGPpy.PGPCardException as exc:
            if exc.sw_code == 0x6982:
                raise pwdException("BadPass")
            if exc.sw_code == 0x6A80:
                raise Exception("Error: Incorrect PIN format")
            if exc.sw_code == 0x6983:
                raise Exception("Error: PIN 1 is blocked")
        # Read and check sign key type in slot C1
        app_data = self.PGPdevice.get_application_data()
        algo_key = app_data["73"]["C1"]
        if not algo_key.startswith(ECDSA_K1):
            raise Exception("Error: This OpenPGP device has a sign key not setup as k1.")

    def initialize_device(self, password):
        self.PIN = password
        if self.PIN == "NoPasswd":
            self.PIN = "123456"
        # Setup the new device, gen a new key
        try:
            self.PGPdevice.verify_pin(3, self.PIN3)
            self.PGPdevice.change_pin("123456", self.PIN, 1)
        except OpenPGPpy.ConnectionException:
            raise Exception("OpenPGP device was disconnected.")
        except OpenPGPpy.PGPCardException as exc:
            if exc.sw_code == 0x6982 or exc.sw_code == 0x6A80:
                raise Exception("Error: Wrong admin code")
        # Generate in the device an EC256k1 key pair
        try:
            # Set sign key as ECDSA SECP256K1
            self.PGPdevice.put_data("00C1", ECDSA_K1)
        except OpenPGPpy.ConnectionException:
            raise Exception("OpenPGP device was disconnected.")
        except OpenPGPpy.PGPCardException as exc:
            if exc.sw_code == 0x6A80 or exc.sw_code == 0x6A83:
                raise Exception("This device is not compatible with ECDSA 256k1.") from exc
            raise
        # Generate key for sign
        self.PGPdevice.gen_key("B600")
        try:
            # Set UIF for sign : require a push button and OpenPGP v3
            self.PGPdevice.put_data("00D6", "0120")
        except OpenPGPpy.PGPCardException as exc:
            if exc.sw_code != 0x6A88:
                raise
            # This device just doesn't support physical confirmation button
        self.created = True

    def get_public_key(self):
        try:
            pubkey_bin = self.PGPdevice.get_public_key("B600")
        except OpenPGPpy.ConnectionException:
            raise Exception("OpenPGP device was disconnected.")
        if pubkey_bin[:2] != b"\x7F\x49":
            raise Exception("Bad object key from OpenPGP public key")
        if pubkey_bin[4] != 65:
            raise Exception("Bad public key length read")
        return pubkey_bin[-65:]

    def sign(self, hashed_msg):
        try:
            self.PGPdevice.verify_pin(1, self.PIN)
            raw_sig = self.PGPdevice.sign(hashed_msg)
        except OpenPGPpy.ConnectionException:
            raise Exception("OpenPGP device was disconnected.")
        return fix_s_sig(raw_sig)
