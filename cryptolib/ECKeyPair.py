# -*- coding: utf8 -*-

# UNIBLOW  -  Elliptic Key Pair
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


# EC key pair (private, public)
# For ECDSA 256k1 or 256r1
# or Ed25519


from cryptography.hazmat import backends
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from nacl.encoding import RawEncoder
from nacl.signing import SigningKey

from cryptolib.cryptography import makeup_sig


class EC_key_pair:
    """EC 256k1, 256r1 or Ed 25519 key pair"""

    def __init__(self, pv_key_int, curve):
        """A EllipticCurvePrivateKey object"""
        self.curve = curve
        if self.curve == "K1":
            self.key_obj = ec.derive_private_key(
                pv_key_int, ec.SECP256K1(), backends.default_backend()
            )
        elif self.curve == "R1":
            self.key_obj = ec.derive_private_key(
                pv_key_int, ec.SECP256R1(), backends.default_backend()
            )
        elif self.curve == "ED":
            seed_bytes = pv_key_int.to_bytes(32, "big")
            self.key_obj = SigningKey(seed_bytes, RawEncoder)
        else:
            raise ValueError("ECkeypair must be K1, R1 or ED")

    def pv_int(self):
        """output private key as a integer, only for 256k1/r1"""
        return self.key_obj.private_numbers().private_value

    def ser256(self):
        """output private key as bytes"""
        if self.curve == "K1" or self.curve == "R1":
            return self.pv_int().to_bytes(32, "big")
        return self.key_obj._seed

    def sign(self, data):
        """Sign data, in DER format.
        For r1 and k1 : sign pre-hashed data (256 bits).
        For Ed25519 : sign full message data.
        """
        if self.curve == "K1" or self.curve == "R1":
            sign_alg = ec.ECDSA(utils.Prehashed(hashes.SHA256()))
            return makeup_sig(self.key_obj.sign(data, sign_alg), self.curve)
        # Ed25519
        return self.key_obj.sign(data, RawEncoder).signature

    def get_public_key(self, compressed=True):
        """public key output X962 from the private key object"""
        if self.curve == "K1" or self.curve == "R1":
            # X962 PublicKey
            out_format = (
                serialization.PublicFormat.CompressedPoint
                if compressed
                else serialization.PublicFormat.UncompressedPoint
            )
            return self.key_obj.public_key().public_bytes(serialization.Encoding.X962, out_format)
        # Ed25519 : 32 bytes public key
        return self.key_obj.verify_key.encode(RawEncoder)
