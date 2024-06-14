# SLIP39

import os

from cryptolib.cryptography import sha2, HMAC_SHA512, PBKDF2_SHA256, PBKDF2_SHA512, XOR
from .rs1024 import verify_checksum

with open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "wordslist/slip_wordlist.txt"),
    "r",
    encoding="utf8",
) as fslip:
    SLIP39_WORDSLIST = [wd.strip() for wd in fslip.readlines()]


def round_secret(id_bin, i, data_input, passphrase):
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
    itrs = 2500
    pbkdf = PBKDF2_SHA256(salt, itrs)
    return pbkdf.derive(bytes([i]) + passphrase)


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

    cs = i % (1 << 31)
    i >>= 30

    share = i & ((1 << 130) - 1)
    i >>= 130

    member_threshold = i & ((1 << 4) - 1)
    i >>= 4

    member_index = i & ((1 << 4) - 1)
    i >>= 4

    group_threshold = i & ((1 << 4) - 1)
    i >>= 4

    i >>= 13

    identifier = i

    print(f"{cs=}")
    print(f"{share=}")
    print(f"{member_threshold=}")
    print(f"{member_index=}")
    print(f"{group_threshold=}")
    print(f"{identifier=}")

    id_bin = identifier.to_bytes(2, "big")

    enc_seed = share.to_bytes(16, "big")
    print(len(enc_seed) // 2)
    L = enc_seed[: len(enc_seed) // 2]
    R = enc_seed[len(enc_seed) // 2 :]
    for roundn in [3, 2, 1, 0]:
        L, R = R, XOR(L, round_secret(id_bin, roundn, R, passphrase))
    return R + L


def slip39_is_checksum_valid(mnemonic):
    """Provide tuple (is_checksum_valid, is_wordlist_valid)"""

    if mnemonic == "":
        return False, False

    words = [word for word in mnemonic.split()]
    words_len = len(words)

    words_idxs = []
    for w in words:
        try:
            k = SLIP39_WORDSLIST.index(w)
        except ValueError:
            return False, False
        words_idxs.append(k)

    if words_len not in [20, 33]:
        return False, True
    # b"shamir" or b"shamir_extendable"
    return verify_checksum(b"shamir", words_idxs), True


def slip39_mnemonic_to_seed(mnemonic_phrase, passphrase=""):
    words_len = len([word for word in mnemonic_phrase.split()])
    if words_len not in [20, 33]:
        raise ValueError("Mnemonic has not the right words size")

    bip39_mnemonic_info = slip39_is_checksum_valid(mnemonic_phrase)
    if not bip39_mnemonic_info[1]:
        raise ValueError("Mnemonic is not from wordlist")
    if not bip39_mnemonic_info[0]:
        raise ValueError("BIP39 Checksum is invalid for this mnemonic")

    return mnemonic_to_seed(mnemonic_phrase, passphrase)
