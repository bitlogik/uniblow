import pytest

from cryptolib.coins.ethereum import rlp_encode, read_int_array


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


def test_practical_encoding():
    # Not EIP155 but good practical RLP test
    tx1 = [
        487,
        0x2E90EDD000,
        0x030D40,
        bytearray.fromhex("bd064928CdD4FD67fb99917c880e6560978D7Ca1"),
        0x0DE0B6B3A7640000,
        bytearray(),
    ]
    assert (
        check_rlp(tx1)
        == "ec8201e7852e90edd00083030d4094bd064928cdd4fd67fb99917c880e6560978d7ca1880de0b6b3a764000080"
    )

    # Now signed
    tx1[6:] = [
        37,
        0x7E833413EAD52B8C538001B12AB5A85BAC88DB0B34B61251BB0FC81573CA093F,
        0x49634F1E439E3760265888434A2F9782928362412030DB1429458DDC9DCEE995,
    ]
    assert (
        check_rlp(tx1)
        == "f86f8201e7852e90edd00083030d4094bd064928cdd4fd67fb99917c880e6560978d7ca1880de0b6b3a76400008025a07e833413ead52b8c538001b12ab5a85bac88db0b34b61251bb0fc81573ca093fa049634f1e439e3760265888434a2f9782928362412030db1429458ddc9dcee995"
    )

    # Consider an EIP155 transaction with
    # nonce = 9, gasprice = 20 * 10**9 = 04a817c800, startgas = 21000 = 5208,
    # to = 0x3535353535353535353535353535353535353535, value = 10**18 = , data='', chain id = 1
    tx2 = [
        9,
        20 * 10**9,
        21000,
        0x3535353535353535353535353535353535353535,
        10**18,
        0,
        1,
        0,
        0,
    ]
    assert (
        check_rlp(tx2)
        == "ec098504a817c800825208943535353535353535353535353535353535353535880de0b6b3a764000080018080"
    )

    # Now signed
    tx2[6] = 37
    tx2[7] = 18515461264373351373200002665853028612451056578545711640558177340181847433846
    tx2[8] = 46948507304638947509940763649030358759909902576025900602547168820602576006531
    assert (
        check_rlp(tx2)
        == "f86c098504a817c800825208943535353535353535353535353535353535353535880de0b6b3a76400008025a028ef61340bd939bc2195fe537567866003e1a15d3c71ff63e1590620aa636276a067cbe9d8997f761aecb703304b3800ccf555c9f3dc64214b297fb1966a3b6d83"
    )


def test_rlp_invalid():
    with pytest.raises(ValueError):
        check_rlp(-1)
    with pytest.raises(ValueError):
        check_rlp([0, -1])
    with pytest.raises(ValueError):
        check_rlp({})
    with pytest.raises(ValueError):
        check_rlp(2.35)


def test_abi_intarray():
    data_in = (
        "0x0000000000000000000000000000000000000000000000000000000000000020"
        "0000000000000000000000000000000000000000000000000000000000000001"
        "00000000000000000000000000000000000000000000000000000000000032e6"
    )
    assert read_int_array(data_in) == [13030]

    data_in = (
        "0x0000000000000000000000000000000000000000000000000000000000000020"
        "0000000000000000000000000000000000000000000000000000000000000003"
        "00000000000000000000000000000000000000000000000000000000000032e6"
        "0000000000000000000000000000000000000000000000000000000000000002"
        "0000000000000000000000000000000000000000000000000000000000000030"
    )
    assert read_int_array(data_in) == [13030, 2, 0x30]
