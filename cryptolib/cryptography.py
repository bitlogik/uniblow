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

try:
    import sha3 as keccak
except Exception:
    raise Exception("Requires PySHA3 : pip3 install pysha3")

from .ECP256k1 import ECPoint, inverse_mod
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from nacl.hashlib import scrypt


# Cryptography

CURVES_ORDER = {
    "K1": int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16),
    "R1": int("115792089210356248762697446949407573529996955224135760342422259061068512044369"),
}


def decompress_pubkey(pubkey_hex_compr):
    """From a public key X962 hex compressed to X962 bin uncompressed"""
    ECPub = ECPoint.from_hex(pubkey_hex_compr)
    return ECPub.encode_output(False)


def public_key_recover(h, r, s, par=0):
    """Recover public key from hash and signature"""
    n = CURVES_ORDER["K1"]
    # Q = (s.R - h.G) / r
    R = ECPoint.from_x(r, par)
    Q = inverse_mod(r, n) * R.dual_mult(-h % n, s)
    # Uncompressed format 04 X Y
    return Q.encode_output(False)


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


def sha3(raw_message):
    """Keccak-256 for Ethereumn, not SHA3"""
    return keccak.keccak_256(raw_message).digest()


def Hash160(data):
    return md160(sha2(data))


def HMAC_SHA512(key, data):
    hmac512 = hmac.new(key, digestmod=hashlib.sha512)
    hmac512.update(data)
    return hmac512.digest()


def PBKDF2_SHA512(salt):
    # Then .derive(data)
    return PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=64,
        salt=salt,
        iterations=2048,
    )


def SecuBoost_KDF(data, salt):
    return scrypt(
        data.replace(b" ", b""), salt, n=pow(2, 20), r=8, p=8, dklen=64, maxmem=1.5 * pow(2, 30)
    )


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


def encode_der_s(int_r, int_s, curve_param):
    """Encode raw signature R|S (2x EC size bytes) into ASN1 DER"""
    array_r = encode_int_der(int_r.to_bytes(32, byteorder="big"))
    # Enforce low S
    n_limit = CURVES_ORDER.get(curve_param)
    if n_limit is None:
        Exception("Encode DER signature to low S is only supported for K1 or R1.")
    if int_s > (n_limit >> 1):
        s_data = (n_limit - int_s).to_bytes(32, byteorder="big")
        array_s = encode_int_der(s_data)
    else:
        array_s = encode_int_der(int_s.to_bytes(32, byteorder="big"))
    return bytes([0x30, len(array_r) + len(array_s), *array_r, *array_s])


def makeup_sig(sig, curve_param):
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
    return encode_der_s(r_value, s_value, curve_param)
