import pytest

from cryptolib.HDwallet import BIP32node
from cryptolib.slip39 import slip39_mnemonic_to_seed

# Tests from https://github.com/trezor/python-shamir-mnemonic/blob/master/vectors.json


BIP39_TESTS_DATA = [
    [
        "duckling enlarge academic academic agency result length solution fridge kidney coal piece deal husband erode duke ajar critical decision keyboard",
        "bb54aac4b89dc868ba37d9cc21b2cece",
        "xprv9s21ZrQH143K4QViKpwKCpS2zVbz8GrZgpEchMDg6KME9HZtjfL7iThE9w5muQA4YPHKN1u5VM1w8D4pvnjxa2BmpGMfXr7hnRrRHZ93awZ",
        # 1MCXenKxN2rtw8qKa3YVh5NDeeYxLZTc8d
        "0356648e3c1890268482b5e58b3448f04de015b53ee161f562cbb888d7c1fef812",
    ],
    [
        "theory painting academic academic armed sweater year military elder discuss acne wildlife boring employer fused large satoshi bundle carbon diagnose anatomy hamster leaves tracks paces beyond phantom capital marvel lips brave detect luck",
        "989baf9dcaad5b10ca33dfd8cc75e42477025dce88ae83e75a230086a0e00e92",
        "xprv9s21ZrQH143K41mrxxMT2FpiheQ9MFNmWVK4tvX2s28KLZAhuXWskJCKVRQprq9TnjzzzEYePpt764csiCxTt22xwGPiRmUjYUUdjaut8RM",
        # 1MuB33X9BdL6ctrmMG5iQS91DDTTY12Y8H
        "020f8b94d8fd249367c57b826923de63cc79b4d939ad7c48b393e2caa3afb71492",
    ],
]


BIP44_BTC_PATH = "m/44'/0'/0'/0/0"


@pytest.mark.parametrize("test_data", BIP39_TESTS_DATA)
def test_strict_slip39(test_data):
    mnemonic = test_data[0]
    seed = bytes.fromhex(test_data[1])
    assert slip39_mnemonic_to_seed(mnemonic, "TREZOR") == seed
    hdw = BIP32node.master_node(seed, "K1")
    pubkey_computed = hdw.derive_path_private(BIP44_BTC_PATH).pv_key.get_public_key(True)
    assert pubkey_computed.hex() == test_data[3]
