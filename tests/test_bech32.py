import pytest

from cryptolib.bech32 import bech32_decode, decode, bech32_address_btc

# Tests from BIP173 (Base32 address format standard)


def test_bech32_valid():
    bech32_str = "A12UEL5L"
    assert bech32_decode(bech32_str) != (None, None)
    bech32_str = "a12uel5l"
    assert bech32_decode(bech32_str) != (None, None)
    bech32_str = (
        "an83characterlonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1tt5tgs"
    )
    assert bech32_decode(bech32_str) != (None, None)
    bech32_str = "abcdef1qpzry9x8gf2tvdw0s3jn54khce6mua7lmqqqxw"
    assert bech32_decode(bech32_str) != (None, None)
    bech32_str = (
        "11qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqc8247j"
    )
    assert bech32_decode(bech32_str) != (None, None)
    bech32_str = "split1checkupstagehandshakeupstreamerranterredcaperred2y9e3w"
    assert bech32_decode(bech32_str) != (None, None)
    bech32_str = "?1ezyfcl"
    assert bech32_decode(bech32_str) != (None, None)
    # BIP350
    bech32_str = "A1LQFN3A"
    assert bech32_decode(bech32_str, 0x2BC830A3) != (None, None)
    bech32_str = "a1lqfn3a"
    assert bech32_decode(bech32_str, 0x2BC830A3) != (None, None)
    bech32_str = (
        "an83characterlonghumanreadablepartthatcontainsthetheexcludedcharactersbioandnumber11sg7hg6"
    )
    assert bech32_decode(bech32_str, 0x2BC830A3) != (None, None)
    bech32_str = "abcdef1l7aum6echk45nj3s0wdvt2fg8x9yrzpqzd3ryx"
    assert bech32_decode(bech32_str, 0x2BC830A3) != (None, None)
    bech32_str = (
        "11llllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllludsr8"
    )
    assert bech32_decode(bech32_str, 0x2BC830A3) != (None, None)
    bech32_str = "split1checkupstagehandshakeupstreamerranterredcaperredlc445v"
    assert bech32_decode(bech32_str, 0x2BC830A3) != (None, None)
    bech32_str = "?1v759aa"
    assert bech32_decode(bech32_str, 0x2BC830A3) != (None, None)


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
        "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7",
        "00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262",
    ],
    [
        "bc1p2wsldez5mud2yam29q22wgfh9439spgduvct83k3pm50fcxa5dps59h4z5",
        "512053a1f6e454df1aa2776a2814a721372d6258050de330b3c6d10ee8f4e0dda343",
    ],
    [
        "bc1pz37fc4cn9ah8anwm4xqqhvxygjf9rjf2resrw8h8w4tmvcs0863sa2e586",
        "5120147c9c57132f6e7ecddba9800bb0c4449251c92a1e60371ee77557b6620f3ea3",
    ],
    ["BC1SW50QGDZ25J", "6002751e"],
    ["bc1zw508d6qejxtdg4y5r3zarvaryvaxxpcs", "5210751e76e8199196d454941c45d1b3a323"],
    [
        "tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy",
        "0020000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433",
    ],
    [
        "bc1punvppl2stp38f7kwv2u2spltjuvuaayuqsthe34hd2dyy5w4g58qqfuag5",
        "5120e4d810fd50586274face62b8a807eb9719cef49c04177cc6b76a9a4251d5450e",
    ],
    [
        "bc1pwyjywgrd0ffr3tx8laflh6228dj98xkjj8rum0zfpd6h0e930h6saqxrrm",
        "5120712447206d7a5238acc7ff53fbe94a3b64539ad291c7cdbc490b7577e4b17df5",
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
    bech32_addr_invalid = "tc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq5zuyut"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqh2y7hd"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "tb1z0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqglt7rf"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "BC1S0XLXVLHEMJA6C4DQV22UAPCTQUPFHLXM9H8Z3K2E72Q4K9HCZ7VQ54WELL"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kemeawh"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "tb1q0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq24jc47"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "bc1p38j9r5y49hruaue7wxjce0updqjuyyx0kh56v8s25huc6995vvpql3jow4"
    bech32_addr_invalid = "BC130XLXVLHEMJA6C4DQV22UAPCTQUPFHLXM9H8Z3K2E72Q4K9HCZ7VQ7ZWS8R"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "bc1pw5dgrnzv"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = (
        "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7v8n0nx0muaewav253zgeav"
    )
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "tb1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq47Zagq"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7v07qwwzcrf"
    assert decode("bc", bech32_addr_invalid) == (None, None)
    bech32_addr_invalid = "tb1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vpggkg4j"
    assert decode("bc", bech32_addr_invalid) == (None, None)
