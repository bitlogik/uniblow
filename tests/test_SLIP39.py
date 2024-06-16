import pytest

from cryptolib.HDwallet import BIP32node
from cryptolib.slip39 import slip39_mnemonic_to_seed

# Tests from https://github.com/trezor/python-shamir-mnemonic/blob/master/vectors.json


SLIP39_TESTS_DATA = [
    # Non extendable
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
    # Extendable
    [
        "testify swimming academic academic column loyalty smear include exotic bedroom exotic wrist lobe cover grief golden smart junior estimate learn",
        "1679b4516e0ee5954351d288a838f45e",
        "xprv9s21ZrQH143K2w6eTpQnB73CU8Qrhg6gN3D66Jr16n5uorwoV7CwxQ5DofRPyok5DyRg4Q3BfHfCgJFk3boNRPPt1vEW1ENj2QckzVLQFXu",
        # 12YBQQspmVfWTrBCAk2kQu1D8i3cg7G6ob
        "0380946783b7f20012b326693b7df5a178eb0fe31c7113ba7fcf6adb59075c51c5",
    ],
    [
        "impulse calcium academic academic alcohol sugar lyrics pajamas column facility finance tension extend space birthday rainbow swimming purple syndrome facility trial warn duration snapshot shadow hormone rhyme public spine counter easy hawk album",
        "8340611602fe91af634a5f4608377b5235fa2d757c51d720c0c7656249a3035f",
        "xprv9s21ZrQH143K2yJ7S8bXMiGqp1fySH8RLeFQKQmqfmmLTRwWmAYkpUcWz6M42oGoFMJRENmvsGQmunWTdizsi8v8fku8gpbVvYSiCYJTF1Y",
        # 175ibUer1wAxtf2s3Ae933XEsXgDdgqjNr
        "0240ce1a5889078c2eccc0bf0a3bbdc4f434dfdbc5ddf8227bc493613b72f32609",
    ],
]

SLIP39_TESTS_DATA_ERRORS = [
    [
        "duckling enlarge academic academic agency result length solution fridge kidney coal piece deal husband erode duke ajar critical decision kidney",
        "Checksum is invalid for this SLIP39 mnemonic",
    ],
    [
        "duckling enlarge academic academic email result length solution fridge kidney coal piece deal husband erode duke ajar music cargo fitness",
        "Invalid share padding bits",
    ],
    [
        "shadow pistol academic always adequate wildlife fancy gross oasis cylinder mustang wrist rescue view short owner flip making coding armed",
        "Only compatible with single share (no split/sharing)",
    ],
    [
        "theory painting academic academic armed sweater year military elder discuss acne wildlife boring employer fused large satoshi bundle carbon diagnose anatomy hamster leaves tracks paces beyond phantom capital marvel lips brave detect lunar",
        "Checksum is invalid for this SLIP39 mnemonic",
    ],
    [
        "theory painting academic academic campus sweater year military elder discuss acne wildlife boring employer fused large satoshi bundle carbon diagnose anatomy hamster leaves tracks paces beyond phantom capital marvel lips facility obtain sister",
        "Invalid share padding bits",
    ],
    [
        "enemy favorite academic acid cowboy phrase havoc level response walnut budget painting inside trash adjust froth kitchen learn tidy punish",
        "Only compatible with single share (no split/sharing)",
    ],
]


BIP44_BTC_PATH = "m/44'/0'/0'/0/0"


@pytest.mark.parametrize("test_data", SLIP39_TESTS_DATA)
def test_process_slip39(test_data):
    mnemonic = test_data[0]
    seed = bytes.fromhex(test_data[1])
    assert slip39_mnemonic_to_seed(mnemonic, "TREZOR") == seed
    hdw = BIP32node.master_node(seed, "K1")
    pubkey_computed = hdw.derive_path_private(BIP44_BTC_PATH).pv_key.get_public_key(True)
    assert pubkey_computed.hex() == test_data[3]


@pytest.mark.parametrize("test_data_err", SLIP39_TESTS_DATA_ERRORS)
def test_error_slip39(test_data_err):
    mnemonic = test_data_err[0]
    with pytest.raises(Exception) as exc_info:
        slip39_mnemonic_to_seed(mnemonic, "TREZOR")
    assert exc_info.value.args[0].startswith(test_data_err[1])
