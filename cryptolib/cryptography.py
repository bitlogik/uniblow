# -*- coding: utf8 -*-

# UNIBLOW  -  Cryptography library
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


import hashlib
import hmac
from os import urandom
from secrets import randbelow

from .ECP256k1 import ECPoint, inverse_mod
from cryptography.hazmat import backends
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


## Cryptography

CURVES_ORDER = {
    "K1": int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16),
    "R1": int("11579208921035624876269744694940757352999695522413576034242225906" "1068512044369"),
}


def public_key_recover(h, r, s, par=0):
    """Recover public key from hash and signature"""
    n = CURVES_ORDER["K1"]
    # Q = (s.R - h.G) / r
    R = ECPoint.from_x(r, par)
    Q = inverse_mod(r, n) * R.dual_mult(-h % n, s)
    # Uncompressed format 04 X Y
    return Q.encode_output(False)


## EC key pair (private, public)


class EC_key_pair:
    """ECDSA 256 k1 key pair"""

    def __init__(self, pv_key_int):
        """A EllipticCurvePrivateKey object"""
        self.key_obj = ec.derive_private_key(pv_key_int, ec.SECP256K1(), backends.default_backend())

    def pv_int(self):
        """output private key as a integer"""
        return self.key_obj.private_numbers().private_value

    def ser256(self):
        return self.pv_int().to_bytes(32, "big")

    def sign(self, hash_data):
        """Sign pre-hashed data, in DER format"""
        sign_alg = ec.ECDSA(utils.Prehashed(hashes.SHA256()))
        return makeup_sig(self.key_obj.sign(hash_data, sign_alg))

    def get_public_key(self, compressed=True):
        """public key output X962 from the private key object"""
        out_format = (
            serialization.PublicFormat.CompressedPoint
            if compressed
            else serialization.PublicFormat.UncompressedPoint
        )
        return self.key_obj.public_key().public_bytes(serialization.Encoding.X962, out_format)


def sha2(raw_message):
    """SHA-2 256"""
    return hashlib.sha256(raw_message).digest()


def dbl_sha2(raw_message):
    """Double SHA-2 256"""
    return sha2(sha2(raw_message))


def md160(raw_message):
    """RIPE MD160"""
    h = hashlib.new("ripemd160")
    h.update(raw_message)
    return h.digest()


def Hash160(data):
    return md160(sha2(data))


def b58checksum(data):
    return dbl_sha2(data)[:4]


def random_generator():
    """Generate 256 bits highly random"""
    # Read 3072 bytes of TRNG
    random_raw = urandom(384)
    assert len(random_raw) == 384
    rnd_list = []
    # Split 384 bytes into 12 * 32 bytes
    for i in range(12):
        rnd_list.append(random_raw[32 * i : 32 * (i + 1)])
    # Get 8 from 12
    rnd_out = []
    for x in range(12, 4, -1):
        rnd_out.append(rnd_list.pop(randbelow(x)))
    assert len(rnd_out) == 8
    assert len(rnd_list) == 4
    # Reduce to 256 bits from 2048 random-source bits with sha2
    return sha2(b"".join(rnd_out))


def encode_int_der(intarray):
    """Encode a bytes array to a DER integer (bytes list)"""
    if intarray[0] >= 128:
        return [2, len(intarray) + 1, 0, *intarray]
    if intarray[0] == 0:
        return encode_int_der(intarray[1:])
    return [2, len(intarray), *intarray]


def encode_der_s(int_r, int_s):
    """Encode raw signature R|S (2x EC size bytes) into ASN1 DER"""
    array_r = encode_int_der(int_r.to_bytes(32, byteorder="big"))
    # Enforce low S
    n_limit = CURVES_ORDER["K1"]
    if int_s > (n_limit >> 1):
        s_data = (n_limit - int_s).to_bytes(32, byteorder="big")
        array_s = encode_int_der(s_data)
    else:
        array_s = encode_int_der(int_s.to_bytes(32, byteorder="big"))
    return bytes([0x30, len(array_r) + len(array_s), *array_r, *array_s])


def makeup_sig(sig):
    """Blockchain signature : DER to DER with low S"""
    if sig[0] != 0x30:
        raise Exception("Wrong signature header")
    if sig[2] != 0x02:
        raise Exception("Wrong signature format")
    rlen = sig[3]
    r_value = int.from_bytes(sig[4 : 4 + rlen], "big")
    slen = sig[5 + rlen]
    s_value = int.from_bytes(sig[6 + rlen : 6 + rlen + slen], "big")
    if sig[1] != 4 + rlen + slen or len(sig) != 6 + rlen + slen:
        raise Exception("Wrong signature encoding")
    return encode_der_s(r_value, s_value)


# def gen_random_entropy(size_bits):


def HMAC_SHA512(key, data):
    return hmac.new(key, data, hashlib.sha512).digest()


def PBKDF2_SHA512(salt):
    return PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=64,
        salt=salt,
        iterations=2048,
    )
