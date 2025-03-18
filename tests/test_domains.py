# import pytest

from wallets.name_service import name_hash, resolveENS, resolveUD, resolveZIL, resolve


# Testing domains resolution


def test_namehash():
    assert name_hash("") == "0000000000000000000000000000000000000000000000000000000000000000"
    assert name_hash("eth") == "93cdeb708b7545dc668eb9280176169d1c33cfd8ed6f04690a0bcc88a93fc4ae"
    assert (
        name_hash("foo.eth") == "de9b09fd7c5f901e23a3f19fecc54828e9c848539801e86591bd9801b019f84f"
    )
    assert name_hash("crypto") == "0f4a10a4f46c288cea365fcf45cccf0e9d901b945b9829ccdb54c10dc3cb7a6f"
    assert (
        name_hash("brad.crypto")
        == "756e4e998dbffd803c21d23b06cd855cdc7a4b57706c95964a37e24b47c10fc9"
    )


def test_resolve_ens():
    # Until they change their registered address
    assert resolveENS("beercoin.eth") == "0x0dd544d0da95666d7c3d38460feb4b5f25eaa515"
    assert resolveENS("mayavi.eth") == "0x0dd544d0da95666d7c3d38460feb4b5f25eaa515"
    assert resolveENS("vitalik.eth") == "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
    assert resolveENS("asfga.eth") == "0xcaf5a154e4689442bf2da3a9a90be6abc4c4bca9"
    assert resolveENS("nick.eth") == "0xb8c2c29ee19d8307cb7255e1cd9cbde883a267d5"


def test_resolve_ud():
    assert resolveUD("brad.crypto", "ETH") == "0x8aaD44321A86b170879d7A244c1e8d360c99DdA8"
    assert resolveUD("brad.crypto", "BTC") == "bc1q359khn0phg58xgezyqsuuaha28zkwx047c0c3y"
    assert resolveUD("brad.crypto", "LTC") is None
    assert resolveUD("paul.crypto", "ETH") is None
    assert resolveUD("pomp.crypto", "ETH") is None
    assert resolveUD("homecakes.crypto", "ETH")
    assert resolveUD("homecakes.crypto", "BTC") is None
    assert resolveUD("udtestdev-test.crypto", "BTC")
    assert resolveUD("ryan.crypto", "ETH")
    assert resolveUD("ryan.crypto", "BTC") is None
    assert (
        resolveUD("jim-unstoppable.klever", "ETH") == "0x57A82545be709963F0182B69F6E9B6f00B977592"
    )


def test_resolve_zil():
    assert resolveZIL("brad.zil", "BTC") == "1EVt92qQnaLDcmVFtHivRJaunG2mf2C3mB"
    assert resolveZIL("brad.zil", "DASH") == "XnixreEBqFuSLnDSLNbfqMH1GsZk7cgW4j"
    assert resolveZIL("brad.zil", "ETH") == "0x45b31e01AA6f42F0549aD482BE81635ED3149abb"
    assert resolveZIL("brad.zil", "LTC") == "LetmswTW3b7dgJ46mXuiXMUY17XbK29UmL"
    assert (
        resolveZIL("brad.zil", "XMR")
        == "447d7TVFkoQ57k3jm3wGKoEAkfEym59mK96Xw5yWamDNFGaLKW5wL2qK5RMTDKGS"
        "vYfQYVN7dLSrLdkwtKH3hwbSCQCu26d"
    )
    assert resolveZIL("brad.zil", "ZEC") == "t1h7ttmQvWCSH1wfrcmvT4mZJfGw2DgCSqV"
    assert resolveZIL("brad.zil", "ZIL") == "zil1yu5u4hegy9v3xgluweg4en54zm8f8auwxu0xxj"
    assert resolveZIL("johnnyjumper.zil", "ETH")
    assert resolveZIL("johnnyjumper.zil", "BTC") is None
    assert resolveZIL("unregistered.zil", "ETH") is None
    assert resolveZIL("paulalcock.zil", "ETH") is None
    assert resolve("jim-unstoppable.zil", "ETH") == "0x57A82545be709963F0182B69F6E9B6f00B977592"
    assert resolve("jim-unstoppable.zil", "BTC") == "bc1q4h40jge84c2stj8hya80hf7dqy77wuzqvd79ac"
    assert resolve("jim-unstoppable.zil", "POL") == "0x621bf2A4720DbFF5E0AC4A94f539ef7c4555Cf22"


def test_resolve():
    assert resolve("brad.zil", "BTC") == "1EVt92qQnaLDcmVFtHivRJaunG2mf2C3mB"
    assert resolve("vitalik.eth", "ETH") == "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
    assert resolve("jim-unstoppable.klever", "ETH") == "0x57A82545be709963F0182B69F6E9B6f00B977592"
    assert resolve("jim-unstoppable.crypto", "ETH") == "0x57A82545be709963F0182B69F6E9B6f00B977592"
    assert resolve("jim-unstoppable.crypto", "BTC") == "bc1q4h40jge84c2stj8hya80hf7dqy77wuzqvd79ac"
    assert (
        resolve("jim-unstoppable.crypto", "MATIC") == "0x621bf2A4720DbFF5E0AC4A94f539ef7c4555Cf22"
    )
    # assert (
    #     resolve("jim-unstoppable.zil", "USDC", True, "MATIC")
    #     == "0x89f7D2F14Be6d283d69f6D2879637aF4AA3eEb93"
    # )
    # assert resolve("jim-unstoppable.zil", "USDC") == "0x89f7D2F14Be6d283d69f6D2879637aF4AA3eEb93"
    assert (
        resolve("jim-unstoppable.crypto", "USDT", True, "POL")
        == "0x89f7D2F14Be6d283d69f6D2879637aF4AA3eEb93"
    )
    assert (
        resolve("jim-unstoppable.zil", "USDT", True, "POL")
        == "0x89f7D2F14Be6d283d69f6D2879637aF4AA3eEb93"
    )
    assert resolve("jim-unstoppable.crypto", "FTM") == "0x621bf2A4720DbFF5E0AC4A94f539ef7c4555Cf22"
    assert (
        resolve("jim-unstoppable.crypto", "UNI", True, "FTM")
        == "0x89f7D2F14Be6d283d69f6D2879637aF4AA3eEb93"
    )
    assert (
        resolve("jim-unstoppable.crypto", "UNI", True, "OP")
        == "0x89f7D2F14Be6d283d69f6D2879637aF4AA3eEb93"
    )
