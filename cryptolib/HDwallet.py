# -*- coding: utf8 -*-

# UNIBLOW  -  HDwallet (BIP39, BIP32)
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


import os
import unicodedata

from cryptolib.cryptography import (
    sha2,
    Hash160,
    HMAC_SHA512,
    EC_key_pair,
    PBKDF2_SHA512,
    CURVES_ORDER,
    random_generator,
)

## BIP39 : mnemonic <-> seed

with open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "wordslist/english.txt"),
    "r",
) as fengmne:
    BIP39_WORDSLIST = [wd.strip() for wd in fengmne.readlines()]


def mnemonic_to_seed(mnemonic_phrase, passphrasestr="", passphrase_prefix=b"mnemonic"):
    passphrase = unicodedata.normalize("NFKD", passphrasestr or "").encode("utf8")
    mnemonic = unicodedata.normalize("NFKD", " ".join(mnemonic_phrase.split())).encode("utf8")
    pbkdf2 = PBKDF2_SHA512(
        passphrase_prefix + passphrase,
    )
    return pbkdf2.derive(mnemonic)


def bip39_is_checksum_valid(mnemonic):
    """Provide tuple (is_checksum_valid, is_wordlist_valid)"""
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
        raise ValueError("Mnemonic has not the right words size")
    entropy = i >> checksum_length
    checksum = i % 2 ** checksum_length
    entb = entropy.to_bytes(entropy_length // 8, "big")
    hashed = int.from_bytes(sha2(entb), "big")
    computed_checksum = hashed >> (256 - checksum_length)
    return checksum == computed_checksum, True


def bip39_mnemonic_to_seed(mnemonic_phrase, passphrase=""):
    if not bip39_is_checksum_valid(mnemonic_phrase)[1]:
        raise ValueError("Mnemonic is not from wordlist")
    if not bip39_is_checksum_valid(mnemonic_phrase)[0]:
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


## BIP32 : key derivation tree


class BIP32node:

    HARDENED_LIMIT = 2 ** 31

    def __init__(self, i, depth, pvkey, chaincode, curve, parent_fingerprint):
        # self.vpub_bytes = bytes.fromhex("0488B21E")  # testnet 0x043587CF
        self.curve = curve.upper()
        self.pv_key = EC_key_pair(pvkey)
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
            data = self.pv_key.get_public_key() + BIP32node.ser32(i)
        key_valid = False
        n_order = CURVES_ORDER.get(self.curve)
        if n_order is None:
            raise Exception("Curve not supported, input R1 ou K1")
        fingerprint = 0  # Hash160(privkey_to_pubkey(self.pv_key, self.curve, True))[:4]
        while not key_valid:  # SLIP10
            deriv = HMAC_SHA512(self.chain_code, data)
            # if private:
            derIL = int.from_bytes(deriv[:32], "big")
            newkey = (derIL + self.pv_key.pv_int()) % n_order
            # else:
            # newkey = add_pubkeys(compress(privkey_to_pubkey(I[:32], opensslbin, curve)), key)
            if derIL >= n_order or newkey == 0:
                data = bytes([1]) + deriv[32:] + BIP32node.ser32(i)
                deriv = HMAC_SHA512(self.chain_code, data)
            else:
                key_valid = True
        return BIP32node(i, self.depth + 1, newkey, deriv[32:], self.curve, fingerprint)

    def serialize_xpub(self):
        dataout = (
            self.vpub_bytes
            + bytes([self.depth])
            + self.parent_fingerprint
            + BIP32node.ser32(self.child_number)
            + self.chain_code
            + privkey_to_pubkey(self.pv_key, self.curve, True)
        )
        return b58.b58encode_check(dataout)

    def __eq__(self, other):
        if not isinstance(other, BIP32node):
            return NotImplemented
        return self.serialize_xpub() == other.serialize_xpub()

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

    def output_pubkey(self, compr):
        return privkey_to_pubkey(self.pv_key, self.curve, compr)

    @classmethod
    def master_node(cls, seed, curve):
        """BIP39"""
        if curve.upper() == "K1":
            curve_string = b"Bitcoin seed"
        elif curve.upper() == "R1":
            curve_string = b"Nist256p1 seed"
        else:
            raise Exception("unsupported curve for BIP32")
        n_order = CURVES_ORDER.get(curve.upper())
        if n_order is None:
            raise Exception("Curve not supported, input R1 ou K1")
        key_invalid = True
        while key_invalid:  # SLIP10
            result = HMAC_SHA512(curve_string, seed)
            derIL = int.from_bytes(result[:32], "big")
            if derIL >= n_order or derIL == 0:
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


## HDWallet : BIP39, BIP32, ...


class HD_Wallet:
    def __init__(self, mk):
        self.master_node = mk

    @classmethod
    def from_seed(cls, seed):
        return cls(BIP32node.master_node(seed, "K1"))

    @classmethod
    def from_mnemonic(cls, mnemonic):
        """Mnemonic to master key (BIP39)"""
        seed = mnemonic_to_seed(mnemonic)
        return HD_Wallet.from_seed(seed)

    def derive_key(self, path):
        """Derive the private key crypto object from the path string"""
        return self.master_node.derive_path_private(path).pv_key
