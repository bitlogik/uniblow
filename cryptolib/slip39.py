# SLIP39

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
    # If ext = 1, then salt_prefix is an empty string.
    # If ext = 0, then salt_prefix = "shamir" || id
    salt = b"shamir" + id_bin + data_input
    pbkdf = PBKDF2_SHA256(salt, iterations)
    return pbkdf.derive(bytes([i]) + key)


def decrypt_lrwb(enc_seed, identifier, iter_exp, key):
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
    passphrase = passphrasestr.encode("ascii")
    words = [word for word in mnemonic_phrase.split()]

    n = len(SLIP39_WORDSLIST)
    i = 0
    for w in words:
        try:
            k = SLIP39_WORDSLIST.index(w)
        except ValueError:
            return False, False
        i = i * n + k

    # Decode bits from right to left

    # checksum = i & ((1 << 30) - 1)
    # Skipped : already checked
    i >>= 30

    padded_share_len_bits = len(words) * 10 - 70
    share_value = i & ((1 << padded_share_len_bits) - 1)
    i >>= padded_share_len_bits

    member_threshold = i & ((1 << 4) - 1)
    i >>= 4

    member_index = i & ((1 << 4) - 1)
    i >>= 4

    group_count = i & ((1 << 4) - 1)
    i >>= 4

    group_threshold = i & ((1 << 4) - 1)
    i >>= 4

    group_index = i & ((1 << 4) - 1)
    i >>= 4

    iterations_exp = i & ((1 << 4) - 1)
    i >>= 4

    extendable = i & ((1 << 1) - 1)
    i >>= 1

    identifier = i  # remaining bits

    # Decrypt the master secret
    enc_seed = share_value.to_bytes(padded_share_len_bits // 8, "big")
    return decrypt_lrwb(enc_seed, identifier, iterations_exp, passphrase)


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
    # b"shamir" or b"shamir_extendable"
    return verify_checksum(b"shamir", words_idxs), True


def slip39_mnemonic_to_seed(mnemonic_phrase, passphrase=""):
    words_len = len(mnemonic_phrase.split())
    if words_len not in [20, 33]:
        raise ValueError("Mnemonic has not the right words size")

    bip39_mnemonic_info = slip39_is_checksum_valid(mnemonic_phrase)
    if not bip39_mnemonic_info[1]:
        raise ValueError("Mnemonic is not from wordlist")
    if not bip39_mnemonic_info[0]:
        raise ValueError("BIP39 Checksum is invalid for this mnemonic")

    return mnemonic_to_seed(mnemonic_phrase, passphrase)
