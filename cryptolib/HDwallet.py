# -*- coding: utf8 -*-

# UNIBLOW  -  HDwallet (BIP39, BIP32)
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


import os
import unicodedata

from cryptolib.cryptography import (
    sha2,
    dbl_sha2,
    HMAC_SHA512,
    PBKDF2_SHA512,
    SecuBoost_KDF,
    CURVES_ORDER,
    random_generator,
)
from cryptolib.ECKeyPair import EC_key_pair, EC_key_pair_uncpr
from cryptolib.ElectrumLegacy import decode_old_mnemonic

# BIP39 : mnemonic <-> seed

with open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "wordslist/english.txt"),
    "r",
    encoding="utf8",
) as fengmne:
    BIP39_WORDSLIST = [wd.strip() for wd in fengmne.readlines()]


def mnemonic_to_seed(
    mnemonic_phrase,
    passphrasestr="",
    passphrase_prefix=b"mnemonic",
    method="PBKDF2-2048-HMAC-SHA512",
):
    passphrase = unicodedata.normalize("NFKD", passphrasestr).encode("utf8")
    mnemonic = unicodedata.normalize("NFKD", " ".join(mnemonic_phrase.split())).encode("utf8")
    if method == "PBKDF2-2048-HMAC-SHA512":
        pbkdf2 = PBKDF2_SHA512(
            passphrase_prefix + passphrase,
        )
        return pbkdf2.derive(mnemonic)
    if method == "SCRYPT":
        return SecuBoost_KDF(
            mnemonic,
            passphrase_prefix + passphrase,
        )
    else:
        raise Exception("Mnemonic derivation method not valid")


def bip39_is_checksum_valid(mnemonic):
    """Provide tuple (is_checksum_valid, is_wordlist_valid)"""
    if mnemonic == "":
        return False, False
    words = [unicodedata.normalize("NFKD", word) for word in mnemonic.split()]
    words_len = len(words)
    n = len(BIP39_WORDSLIST)
    checksum_length = 11 * words_len // 33
    entropy_length = 32 * checksum_length
    i = 0
    words.reverse()
    while words:
        w = words.pop()
        try:
            k = BIP39_WORDSLIST.index(w)
        except ValueError:
            return False, False
        i = i * n + k
    if words_len not in [12, 15, 18, 21, 24]:
        return False, True
    entropy = i >> checksum_length
    checksum = i % 2 ** checksum_length
    entb = entropy.to_bytes(entropy_length >> 3, "big")
    hashed = int.from_bytes(sha2(entb), "big")
    computed_checksum = hashed >> (256 - checksum_length)
    return checksum == computed_checksum, True


def bip39_mnemonic_to_seed(mnemonic_phrase, passphrase=""):
    words_len = len([unicodedata.normalize("NFKD", word) for word in mnemonic_phrase.split()])
    if words_len not in [12, 15, 18, 21, 24]:
        raise ValueError("Mnemonic has not the right words size")
    bip39_mnemonic_info = bip39_is_checksum_valid(mnemonic_phrase)
    if not bip39_mnemonic_info[1]:
        raise ValueError("Mnemonic is not from wordlist")
    if not bip39_mnemonic_info[0]:
        raise ValueError("BIP39 Checksum is invalid for this mnemonic")
    return mnemonic_to_seed(
        mnemonic_phrase, passphrasestr=passphrase, passphrase_prefix=b"mnemonic"
    )


def mnemonic_int_to_words(mint, mint_num_words):
    words = [BIP39_WORDSLIST[(mint >> (11 * x)) & 0x7FF].strip() for x in range(mint_num_words)]
    return " ".join((words[::-1]))


def entropy_int(entbytes):
    checksum_size = len(entbytes) // 4
    hent = int.from_bytes(sha2(entbytes), "big")
    csint = hent >> (256 - checksum_size)
    return csint, checksum_size


def entropy_to_mnemonic(entropy):
    if len(entropy) < 16:
        raise ValueError("The size of the entropy must be at least 128 bits (16 bytes)")
    if len(entropy) % 4 != 0:
        raise ValueError("The size of the entropy must be a multiple of 4 bytes.")
    if len(entropy) > 32:
        raise ValueError("The size of the entropy must at most 256 bits (32 bytes)")
    entbytes = len(entropy)
    csint, checksum_size = entropy_int(entropy)
    entint = int.from_bytes(entropy, "big")
    mint = (entint << checksum_size) | csint
    mint_num_words = (8 * entbytes + checksum_size) // 11
    return mnemonic_int_to_words(mint, mint_num_words)


def generate_mnemonic(nwords):
    if nwords not in [12, 15, 18, 21, 24]:
        raise ValueError("The number of words should be 12-24.")
    ent_sz = (nwords * 4) // 3
    new_ent = random_generator()[:ent_sz]
    return entropy_to_mnemonic(new_ent)


# BIP32 : key derivation tree


class BIP32node:

    HARDENED_LIMIT = 2 ** 31

    def __init__(self, i, depth, pvkey, chaincode, curve, parent_fingerprint):
        # self.vpub_bytes = bytes.fromhex("0488B21E")  # testnet 0x043587CF
        self.curve = curve.upper()
        self.pv_key = EC_key_pair(pvkey, self.curve)
        self.chain_code = chaincode
        self.child_number = i
        self.parent_fingerprint = parent_fingerprint
        self.depth = depth

    def derive_private(self, i):
        """private parent key to private child key"""
        if i >= BIP32node.HARDENED_LIMIT:
            # hardened
            data = bytes([0]) + self.pv_key.ser256() + BIP32node.ser32(i)
        else:
            # standard (non-hardened)
            if self.curve == "ED":
                raise Exception("Ed25519 derivation can't be done with a non-hardened normal child")
            data = self.pv_key.get_public_key() + BIP32node.ser32(i)
        key_valid = False
        if self.curve != "ED":
            n_order = CURVES_ORDER.get(self.curve)
            if n_order is None:
                raise Exception("Curve not supported, input R1, K1 or ED")
        fingerprint = 0  # Hash160(privkey_to_pubkey(self.pv_key, self.curve, True))[:4]
        while not key_valid:  # SLIP10
            deriv = HMAC_SHA512(self.chain_code, data)
            derIL = int.from_bytes(deriv[:32], "big")
            if self.curve == "ED":
                newkey = derIL
                key_valid = True
            else:
                newkey = (derIL + self.pv_key.pv_int()) % n_order
                if derIL >= n_order or newkey == 0:
                    data = bytes([1]) + deriv[32:] + BIP32node.ser32(i)
                    deriv = HMAC_SHA512(self.chain_code, data)
                else:
                    key_valid = True
        return BIP32node(i, self.depth + 1, newkey, deriv[32:], self.curve, fingerprint)

    def derive_path_private(self, path_str):
        if self.depth > 0:
            raise Exception("Must be called only on a master node")
        if path_str == "" or path_str == "m":
            return self
        if path_str[:2] != "m/":
            raise Exception("Unvalid path string, must start with m/")
        path_list = path_str.lstrip("m/").split("/")
        node = self
        for pt in path_list:
            node = node.derive_private(BIP32node.index_int(pt.rstrip()))
        return node

    @classmethod
    def master_node(cls, seed, curve):
        """BIP39"""
        if curve.upper() == "K1":
            curve_string = b"Bitcoin seed"
        elif curve.upper() == "R1":
            curve_string = b"Nist256p1 seed"
        elif curve.upper() == "ED":
            curve_string = b"ed25519 seed"
        else:
            raise Exception("unsupported curve for SLIP10/BIP32")
        if curve_string != b"ed25519 seed":
            n_order = CURVES_ORDER.get(curve.upper())
            if n_order is None:
                raise Exception("Curve not supported, input R1, K1 or ED")
        key_invalid = True
        while key_invalid:  # SLIP10
            result = HMAC_SHA512(curve_string, seed)
            derIL = int.from_bytes(result[:32], "big")
            if curve_string != b"ed25519 seed" and derIL >= n_order or derIL == 0:
                seed = result
            else:
                key_invalid = False
        return cls(
            0,
            0,
            int.from_bytes(result[:32], "big"),
            result[32:],
            curve.upper(),
            BIP32node.ser32(0),
        )

    @staticmethod
    def ser32(num):
        return num.to_bytes(4, "big")

    @staticmethod
    def index_int(path_num):
        """index string to int"""
        if path_num[-1] == "'" or path_num[-1] == "H":
            numout = int(path_num[:-1], 10) + BIP32node.HARDENED_LIMIT
        else:
            numout = int(path_num, 10)
        return numout

    @staticmethod
    def ser256(num):
        return num.to_bytes(32, "big")


# HDWallet : BIP39, BIP32, ...


class HD_Wallet:
    def __init__(self, mk):
        self.master_node = mk

    @classmethod
    def from_seed(cls, seed, ptype):
        return cls(BIP32node.master_node(seed, ptype))

    @staticmethod
    def seed_from_mnemonic(mnemonic, passw="", std="BIP39"):
        """Mnemonic to master key (BIP39 or BOOST)"""
        pprefix = b"mnemonic"
        if std == "BIP39":
            mnemonic = mnemonic.lower()
            method = "PBKDF2-2048-HMAC-SHA512"
        elif std == "BOOST":
            method = "SCRYPT"
        elif std == "Electrum":
            mnemonic = mnemonic.lower()
            method = "PBKDF2-2048-HMAC-SHA512"
            pprefix = b"electrum"
        elif std == "ElectrumOLD":
            return decode_old_mnemonic(mnemonic)
        else:
            raise Exception("Mnemonic standard not valid")
        seed = mnemonic_to_seed(
            mnemonic, passphrasestr=passw, passphrase_prefix=pprefix, method=method
        )
        return seed

    def derive_key(self, path):
        """Derive the private key crypto object from the path string"""
        return self.master_node.derive_path_private(path).pv_key


class ElectrumOldWallet:
    def __init__(self, pv_key):
        self.master_private_key = pv_key

    @classmethod
    def from_seed(cls, seed):
        seedh = seed.hex().encode("ascii")
        orig_seedh = seedh
        for _ in range(100000):
            seedh = sha2(seedh + orig_seedh)
        master_key = int.from_bytes(seedh, "big")
        return cls(EC_key_pair_uncpr(master_key, "K1"))

    def derive_key(self, path_str):
        child_priv_int = self.master_private_key.pv_int()
        if path_str[:2] != "m/":
            raise Exception("Unvalid path string, must start with m/")
        if len(path_str.split("/")) != 3:
            raise Exception("Unvalid path string, must have exactly 2 levels for Old Electrum")
        change, index = path_str.lstrip("m/").split("/")
        data_hashed = (
            f"{index}:{change}:".encode("ascii") + self.master_private_key.get_public_key()[1:]
        )
        child_priv_int += int.from_bytes(dbl_sha2(data_hashed), "big")
        curve = "K1"
        return EC_key_pair_uncpr(child_priv_int % CURVES_ORDER[curve], curve)
