# -*- coding: utf8 -*-

# UNIBLOW  -  Elliptic Key Pair
# Copyright (C) 2021-2023 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


# EC key (private, public)
# For ECDSA 256k1 or 256r1
# or Ed25519

from cryptography.hazmat import backends
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from nacl.encoding import RawEncoder
from nacl.signing import SigningKey

from cryptolib.cryptography import random_generator, makeup_sig


K1_CURVE = ec.SECP256K1()
R1_CURVE = ec.SECP256R1()
R384_CURVE = ec.SECP384R1()


class EC_key_pair:
    """EC 256k1, 256r1 or Ed 25519 key pair"""

    def __init__(self, pv_key_int, curve):
        """An EllipticCurvePrivateKey object"""
        self.curve = curve
        if self.curve == "K1":
            curveobj = K1_CURVE
        elif self.curve == "R1":
            curveobj = R1_CURVE
        if self.curve == "K1" or self.curve == "R1":
            # K1 or R1
            if pv_key_int < 0:
                # No private key provided, generating
                self.key_obj = ec.generate_private_key(curveobj, backends.default_backend())
            else:
                # Create a key pair from the provided key integer
                self.key_obj = ec.derive_private_key(
                    pv_key_int, curveobj, backends.default_backend()
                )
        elif self.curve == "ED":
            if pv_key_int < 0:
                # No private key provided, generating
                seed_bytes = random_generator()
            else:
                # Create a key pair from the provided key integer
                seed_bytes = pv_key_int.to_bytes(32, "big")
            self.key_obj = SigningKey(seed_bytes, RawEncoder)
        else:
            raise ValueError("ECkeypair must be K1, R1 or ED")

    def pv_int(self):
        """output private key as a integer, only for 256k1/r1"""
        if self.curve == "ED":
            raise ValueError("ECkeypair pv_int can only be used for R1 or K1 key.")
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

    def get_public_key(self, compressed=False):
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

    def ecdh(self, peer_pub_key):
        """Compute a ECDH key exchange."""
        if self.curve == "ED":
            raise ValueError("ECkeypair pv_int can only be used for R1 or K1 key.")
        if self.curve == "K1":
            curveobj = K1_CURVE
        elif self.curve == "R1":
            curveobj = R1_CURVE
        public_key = ec.EllipticCurvePublicKey.from_encoded_point(curveobj, peer_pub_key)
        shared_key = self.key_obj.exchange(ec.ECDH(), public_key)
        return shared_key


class ECpubkey:
    """EC 256k1, 256r1 public key"""

    def __init__(self, pubkey_data, curve):
        """An EllipticCurvePrivateKey object generated"""
        if curve == "K1":
            curveobj = K1_CURVE
        elif curve == "R1":
            curveobj = R1_CURVE
        elif curve == "R384":
            curveobj = R384_CURVE
        else:
            raise ValueError("ECpubkey must be K1, R1 or R384")
        self.pubkey_obj = ec.EllipticCurvePublicKey.from_encoded_point(curveobj, pubkey_data)

    def check_signature(self, msg, signature):
        """Check an ECDSA signature.
        Throws except InvalidSignature if not OK.
        """
        if self.pubkey_obj.key_size == 256:
            h = hashes.SHA256()
        elif self.pubkey_obj.key_size == 384:
            h = hashes.SHA384()
        else:
            raise Exception("Invalid public key length.")
        self.pubkey_obj.verify(signature, msg, ec.ECDSA(h))
