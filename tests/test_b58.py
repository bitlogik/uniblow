import pytest

from cryptolib import base58


# Tests from https://github.com/luke-jr/libbase58/tree/master/tests


def test_base58_encode():
    bint = bytes.fromhex("005a1fc5dd9e6f03819fca94a2d89669469667f9a0")
    assert base58.encode_base58(bint) == "19DXstMaV43WpYg4ceREiiTv2UntmoiA9j"


def test_base58_decode():
    b58_addr_str = "19DXstMaV43WpYg4ceREiiTv2UntmoiA9j"
    bin_addr = "005a1fc5dd9e6f03819fca94a2d89669469667f9a0"
    assert base58.decode_base58(b58_addr_str) == bytes.fromhex(bin_addr)


def test_bad_checksum():
    with pytest.raises(ValueError) as exc_info:
        base58.decode_base58("19DXstMaV43WpYg4ceREiiTv2UntmoiA9a")
    assert str(exc_info.value) == "Base58 checksum is not valid"


def test_small():
    assert base58.base58_to_bin("2") == b"\x01"


def test_zero():
    assert base58.base58_to_bin("111111") == bytes.fromhex("000000000000")


def test_encode_long():
    b58_addr_str = "2mkQLxaN3Y4CwN5E9rdMWNgsXX7VS6UnfeT"
    bin_addr = bytes.fromhex("ff5a1fc5dd9e6f03819fca94a2d89669469667f9a0")
    assert base58.encode_base58(bin_addr) == b58_addr_str


def test_encode_neg():
    bin_addr = bytes.fromhex("00CEF022FA")
    assert base58.bin_to_base58(bin_addr) == "16Ho7Hs"


def test_small_encode():
    assert base58.bin_to_base58(b"1") == "r"


def tests_ietf():
    # Tests from IETF base58
    # https://tools.ietf.org/id/draft-msporny-base58-01.html

    IETF_b58_01 = "2NEpo7TZRRrLZSi2U"
    IETF_bin_01 = b"Hello World!"

    IETF_b58_02 = "USm3fpXnKG5EUBx2ndxBDMPVciP5hGey2Jh4NDv6gmeo1LkMeiKrLJUUBk6Z"
    IETF_bin_02 = b"The quick brown fox jumps over the lazy dog."

    IETF_b58_03 = "11233QC4"
    IETF_bin_03 = bytes.fromhex("0000287fb4cd")

    assert base58.bin_to_base58(IETF_bin_01) == IETF_b58_01
    assert base58.bin_to_base58(IETF_bin_02) == IETF_b58_02
    assert base58.bin_to_base58(IETF_bin_03) == IETF_b58_03

    assert base58.base58_to_bin(IETF_b58_01) == IETF_bin_01
    assert base58.base58_to_bin(IETF_b58_02) == IETF_bin_02
    assert base58.base58_to_bin(IETF_b58_03) == IETF_bin_03
