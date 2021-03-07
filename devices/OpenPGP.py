#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW OpenPGP Wallet manager
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


import OpenPGPpy

CURVE_K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
EC_BYTES_SIZE = 32


class pwdException(Exception):
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


def fix_s_sig(sigRS):
    # Quick MPI decoder
    ec_sz = len(sigRS) // 2
    r_value = int.from_bytes(sigRS[:ec_sz], "big")
    s_value = int.from_bytes(sigRS[ec_sz:], "big")
    # to DER with low S
    return encode_der_s(r_value, s_value)


def compress_pubkey(pgp_pubkey):
    pubkey = pgp_pubkey[-65:]
    pubkey_parity = pubkey[64] % 2
    pubkey_header = (2 + pubkey_parity).to_bytes(1, byteorder="big")
    return pubkey_header + pubkey[1:33]


class OpenPGP:
    # Using an OpenPGP device

    has_password = True
    is_HD = False

    def __init__(self, password, itimes):
        self.created = False
        self.PIN = password
        self.has_hardware_button = True
        self.PGPdevice = OpenPGPpy.OpenPGPcard()
        self.open_account()

    def open_account(self):
        pubkey_card = None
        try:
            pubkey_card = self.PGPdevice.get_public_key("B600")
        except OpenPGPpy.PGPCardException as exc:
            # SW = 0x6581 or 0x6A88 ?
            if exc.sw_code != 0x6581 and exc.sw_code != 0x6A88:
                raise
        # SIGn key is not present, continue to setup this key
        if pubkey_card is None:
            # Setup the new device, gen a new key
            PIN3 = "12345678"
            try:
                self.PGPdevice.verify_pin(3, PIN3)
            except OpenPGPpy.PGPCardException as exc:
                if exc.sw_code == 0x6982 or exc.sw_code == 0x6A80:
                    raise Exception("Error: Wrong PUK")
            # Generate in the device an EC256k1 key pair
            try:
                self.PGPdevice.put_data("00C1", "132B8104000A")
            except OpenPGPpy.PGPCardException as exc:
                if exc.sw_code == 0x6A80:
                    raise Exception("This device is not compatible with ECDSA 256k1.") from exc
                raise
            # Generate key for sign
            pubkey_card = self.PGPdevice.gen_key("B600")
            try:
                # Set UIF for sign : require a push button and OpenGPG v3
                self.PGPdevice.put_data("00D6", "0120")
            except OpenPGPpy.PGPCardException as exc:
                if exc.sw_code != 0x6A88:  # card just doesnt support UIF ?
                    raise
                raise Exception("This device doesn't support physical confirmation button")
            self.created = True
        try:
            self.PGPdevice.verify_pin(1, self.PIN)
        except OpenPGPpy.PGPCardException as exc:
            if exc.sw_code == 0x6982:
                raise pwdException("BadPass")
            if exc.sw_code == 0x6A80:
                raise Exception("Error: Incorrect PIN format")
            if exc.sw_code == 0x6983:
                raise Exception("Error: PIN 1 is blocked")

    def get_public_key(self):
        pubkey_bin = self.PGPdevice.get_public_key("B600")
        return compress_pubkey(pubkey_bin).hex()

    def sign(self, hashed_msg):
        self.PGPdevice.verify_pin(1, self.PIN)
        raw_sig = self.PGPdevice.sign(hashed_msg)
        return fix_s_sig(raw_sig)
