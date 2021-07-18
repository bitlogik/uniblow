import pytest

from cryptolib.bech32 import bech32_decode, decode, bech32_address_btc

# Tests from BIP173 (Base32 address format standard)


def test_bech32_valid():
    bech32_str = "A12UEL5L"
    bech32_decode(bech32_str) != (None, None)
    bech32_str = "a12uel5l"
    bech32_decode(bech32_str) != (None, None)
    bech32_str = (
        "an83characterlonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1tt5tgs"
    )
    bech32_decode(bech32_str) != (None, None)
    bech32_str = "abcdef1qpzry9x8gf2tvdw0s3jn54khce6mua7lmqqqxw"
    bech32_decode(bech32_str) != (None, None)
    bech32_str = (
        "11qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqc8247j"
    )
    bech32_decode(bech32_str) != (None, None)
    bech32_str = "split1checkupstagehandshakeupstreamerranterredcaperred2y9e3w"
    bech32_decode(bech32_str) != (None, None)
    bech32_str = "?1ezyfcl"
    bech32_decode(bech32_str) != (None, None)


def test_bech32_invalid():
    bech32_str_invalid = "\x201nwldj5"
    assert bech32_decode(bech32_str_invalid) == (None, None)
    bech32_str_invalid = "\x7F1axkwrx"
    assert bech32_decode(bech32_str_invalid) == (None, None)
    bech32_str_invalid = "\x801eym55h"
    assert bech32_decode(bech32_str_invalid) == (None, None)
    bech32_str_invalid = "an84characterslonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1569pvx"
    assert bech32_decode(bech32_str_invalid) == (None, None)
    bech32_str_invalid = "pzry9x0s0muk"
    assert bech32_decode(bech32_str_invalid) == (None, None)
    bech32_str_invalid = "1pzry9x0s0muk"
    assert bech32_decode(bech32_str_invalid) == (None, None)
    bech32_str_invalid = "x1b4n0q5v"
    assert bech32_decode(bech32_str_invalid) == (None, None)
    bech32_str_invalid = "li1dgmt3"
    assert bech32_decode(bech32_str_invalid) == (None, None)
    bech32_str_invalid = "de1lg7wt + 0xFF"
    assert bech32_decode(bech32_str_invalid) == (None, None)
    bech32_str_invalid = "A1G7SGD8"
    assert bech32_decode(bech32_str_invalid) == (None, None)
    bech32_str_invalid = "10a06t8"
    assert bech32_decode(bech32_str_invalid) == (None, None)
    bech32_str_invalid = "1qzzfhee"
    assert bech32_decode(bech32_str_invalid) == (None, None)


DATA_CODEC = [
    ["BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4", "0014751e76e8199196d454941c45d1b3a323f1433bd6"],
    [
        "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7",
        "00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262",
    ],
    [
        "bc1pw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7k7grplx",
        "5128751e76e8199196d454941c45d1b3a323f1433bd6751e76e8199196d454941c45d1b3a323f1433bd6",
    ],
    ["BC1SW50QA3JX3S", "6002751e"],
    ["bc1zw508d6qejxtdg4y5r3zarvaryvg6kdaj", "5210751e76e8199196d454941c45d1b3a323"],
    [
        "tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy",
        "0020000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433",
    ],
]


@pytest.mark.parametrize("test_data", DATA_CODEC)
def test_codec_bech32(test_data):
    raw_bin = bytes.fromhex(test_data[1])
    bech32_str = test_data[0]
    hrp = bech32_str[:2].lower()
    assert bytes(decode(hrp, bech32_str)[1]) == raw_bin[2:]
    witness_version = "qpzry9x8gf2tvdw0s3jn54khce6mua7l".find(bech32_str.lower()[3])
    assert bech32_address_btc(raw_bin[2:], hrp, witness_version) == bech32_str.lower()


def test_invalid_address():
    bech32_addr_invalid = "tc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "BC13W508D6QEJXTDG4Y5R3ZARVARY0C5XW7KN40WF2"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "bc1rw5uspcuh"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = (
        "bc10w508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5rljs90"
    )
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sL5k7"
    assert decode("tb", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "bc1zw508d6qejxtdg4y5r3zarvaryvqyzf3du"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3pjxtptv"
    assert decode("tb", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "bc1gmk9yu"
    assert decode("bc", bech32_addr_invalid) == (None, None)
