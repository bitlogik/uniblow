import pytest

from cryptolib.slip39 import slip39_mnemonic_to_seed

# Tests from https://github.com/trezor/python-shamir-mnemonic/blob/master/vectors.json


BIP39_TESTS_DATA = [
    [
        "duckling enlarge academic academic agency result length solution fridge kidney coal piece deal husband erode duke ajar critical decision keyboard",
        "bb54aac4b89dc868ba37d9cc21b2cece",
        "xprv9s21ZrQH143K4QViKpwKCpS2zVbz8GrZgpEchMDg6KME9HZtjfL7iThE9w5muQA4YPHKN1u5VM1w8D4pvnjxa2BmpGMfXr7hnRrRHZ93awZ",
    ],
]


@pytest.mark.parametrize("test_data", BIP39_TESTS_DATA)
def test_strict_slip39(test_data):
    mnemonic = test_data[0]
    seed = bytes.fromhex(test_data[1])
    assert slip39_mnemonic_to_seed(mnemonic, "TREZOR") == seed
