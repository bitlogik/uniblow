# -*- coding: utf8 -*-

# UNIBLOW - SLIP-0039
# Copyright (C) 2024 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


"""SLIP39"""

import os

from cryptolib.cryptography import PBKDF2_SHA256, XOR
from .rs1024 import verify_checksum

with open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "wordslist/slip_wordlist.txt"),
    "r",
    encoding="utf8",
) as fslip:
    SLIP39_WORDSLIST = [wd.strip() for wd in fslip.readlines()]


WORDS_DICT = {w: idx for idx, w in enumerate(SLIP39_WORDSLIST)}


def round_secret(id_bin, i, data_input, key, iterations):
    """Derive a secret key to xor"""
    # F(i, R) = PBKDF2(
    #    PRF = HMAC-SHA256,
    #    Password = (i || passphrase),
    #    Salt = (salt_prefix || R),
    #    iterations = 2500 << e,
    #    dkLen = n/2 bytes, len(R)
    # )
    # No id_bin: ext = 1, salt_prefix is an empty string.
    # id_bin:    ext = 0, salt_prefix = "shamir" || id
    salt = data_input
    if id_bin:
        # Not extendable
        salt = b"shamir" + id_bin + data_input
    pbkdf = PBKDF2_SHA256(salt, iterations)
    return pbkdf.derive(bytes([i]) + key)


def decrypt_lrwb(enc_seed, identifier, iter_exp, key):
    """Decrypt the encrypted share value.
    Wide-blocksize pseudorandom permutation based on the Luby-Rackoff construction
    """
    id_bin = b""
    if identifier is not None:
        # Not extendable
        id_bin = identifier.to_bytes(2, "big")
    left = enc_seed[: len(enc_seed) // 2]
    right = enc_seed[len(enc_seed) // 2 :]
    rounds = 4
    iterations = (10000 // rounds) * (1 << iter_exp)
    for round_number in [3, 2, 1, 0]:
        left, right = right, XOR(left, round_secret(id_bin, round_number, right, key, iterations))
    return right + left


def mnemonic_to_seed(
    mnemonic_phrase,
    passphrasestr="",
):
    """Compute seed from a SLIP39 mnemonic"""
    passphrase = passphrasestr.encode("ascii")
    words = [word for word in mnemonic_phrase.split()]

    n = len(SLIP39_WORDSLIST)
    i = 0
    for w in words:
        i = i * n + WORDS_DICT[w]

    # Decode bits from right to left

    # checksum = i & ((1 << 30) - 1)
    # Skipped : already checked
    i >>= 30

    padded_share_len_bits = len(words) * 10 - 70
    if padded_share_len_bits % 10:
        raise ValueError("Share value is not correctly padded")
    if padded_share_len_bits % 16 > 8:
        raise ValueError("Too large share value padding")
    share_value = i & ((1 << padded_share_len_bits) - 1)
    # Check all padding bits are zero : value less than w/o padding
    if share_value >= 2 ** (padded_share_len_bits - (padded_share_len_bits % 16)):
        raise ValueError("Invalid share padding bits")
    i >>= padded_share_len_bits

    member_threshold = i & ((1 << 4) - 1)
    if member_threshold != 0:
        raise ValueError(
            "Only compatible with single share (no split/sharing). "
            "Member threshold is expected to be zero"
        )
    i >>= 4

    # member_index = i & ((1 << 4) - 1)
    i >>= 4

    group_count = i & ((1 << 4) - 1)
    if group_count != 0:
        raise ValueError(
            "Only compatible with single share (no split/sharing). "
            "Group count is expected to be zero"
        )
    i >>= 4

    group_threshold = i & ((1 << 4) - 1)
    if group_threshold != 0:
        raise ValueError(
            "Only compatible with single share (no split/sharing). "
            "Group threshold is expected to be zero"
        )
    i >>= 4

    # group_index = i & ((1 << 4) - 1)
    i >>= 4

    iterations_exp = i & ((1 << 4) - 1)
    i >>= 4

    extendable = i & ((1 << 1) - 1) == 1
    i >>= 1

    identifier = i  # remaining bits

    # Decrypt the master secret
    enc_seed = share_value.to_bytes(padded_share_len_bits // 8, "big")
    idext = None if extendable else identifier
    return decrypt_lrwb(enc_seed, idext, iterations_exp, passphrase)


def slip39_is_checksum_valid(mnemonic):
    """Provide tuple (is_checksum_valid, is_wordlist_valid)"""

    if mnemonic == "":
        return False, False

    words = mnemonic.split()
    words_idxs = []
    for w in words:
        if w not in WORDS_DICT:
            return False, False
        words_idxs.append(WORDS_DICT[w])

    if len(words) not in [20, 33]:
        return False, True
    if words_idxs[1] & 0b10000:
        # extendable
        cs = b"shamir_extendable"
    else:
        cs = b"shamir"
    return verify_checksum(cs, words_idxs), True


def slip39_mnemonic_to_seed(mnemonic_phrase, passphrase=""):
    """Check SLIP39 mnemonic and compute seed from it."""
    words_len = len(mnemonic_phrase.split())
    if words_len not in [20, 33]:
        raise ValueError("Mnemonic has not the right words number (should be 20 or 33)")

    bip39_mnemonic_info = slip39_is_checksum_valid(mnemonic_phrase)
    if not bip39_mnemonic_info[1]:
        raise ValueError("Mnemonic is not from wordlist")
    if not bip39_mnemonic_info[0]:
        raise ValueError("Checksum is invalid for this SLIP39 mnemonic")

    return mnemonic_to_seed(mnemonic_phrase, passphrase)
