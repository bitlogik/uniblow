import pytest

from cryptolib.coins.ethereum import rlp_encode


# Testing RLP encoding


def check_rlp(toencode):
    if isinstance(toencode, str):
        toencode = bytearray(toencode.encode("utf8"))
    return rlp_encode(toencode).hex().lower()


def test_rlp_strings():
    assert check_rlp("") == "80"
    assert check_rlp("dog") == "83646f67"


def test_rlp_int():
    assert check_rlp(0) == "80"
    assert check_rlp(127) == "7f"
    assert check_rlp(128) == "8180"
    assert check_rlp(256) == "820100"
    assert check_rlp(1024) == "820400"
    assert check_rlp(0xFFFFFF) == "83ffffff"
    assert check_rlp(0xFFFFFFFF) == "84ffffffff"
    assert check_rlp(0xFFFFFFFFFFFFFF) == "87ffffffffffffff"


def test_rlp_unit256():
    assert check_rlp(0x102030405060708090A0B0C0D0E0F2) == "8f102030405060708090a0b0c0d0e0f2"
    assert (
        check_rlp(0x0100020003000400050006000700080009000A000B000C000D000E01)
        == "9c0100020003000400050006000700080009000a000b000c000d000e01"
    )
    assert (
        check_rlp(0x0100000000000000000000000000000000000000000000000000000000000000)
        == "a00100000000000000000000000000000000000000000000000000000000000000"
    )


def test_rlp_list():
    assert check_rlp([]) == "c0"
    assert check_rlp([1, 2, 3]) == "c3010203"
    assert check_rlp([bytearray(b"cat"), bytearray(b"dog")]) == "c88363617483646f67"
    assert check_rlp([0] * 1024) == "f90400" + 1024 * "80"


def test_rlp_invalid():
    with pytest.raises(ValueError):
        check_rlp(-1)
    with pytest.raises(ValueError):
        check_rlp([0, -1])
    with pytest.raises(ValueError):
        check_rlp({})
    with pytest.raises(ValueError):
        check_rlp(2.35)
