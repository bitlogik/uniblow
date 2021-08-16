from cryptolib.HDwallet import BIP32node

# Tests from BIP32 and SLIP10 vectors


def test_bip32_test_1():
    SEED_1 = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    DATA_1 = [
        ["m", "0339a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c2"],
        ["m/0H", "035a784662a4a20a65bf6aab9ae98a6c068a81c52e4b032c0fb5400c706cfccc56"],
        ["m/0H/1", "03501e454bf00751f24b1b489aa925215d66af2234e3891c3b21a52bedb3cd711c"],
        ["m/0H/1/2H", "0357bfe1e341d01c69fe5654309956cbea516822fba8a601743a012a7896ee8dc2"],
        ["m/0H/1/2H/2", "02e8445082a72f29b75ca48748a914df60622a609cacfce8ed0e35804560741d29"],
        [
            "m/0H/1/2H/2/1000000000",
            "022a471424da5e657499d1ff51cb43c47481a03b1e77f951fe64cec9f5a48f7011",
        ],
    ]
    hdw_1 = BIP32node.master_node(SEED_1, "K1")
    for test_data1 in DATA_1:
        assert (
            hdw_1.derive_path_private(test_data1[0]).pv_key.get_public_key().hex() == test_data1[1]
        )


def test_bip32_test_2():
    SEED_2 = bytes.fromhex(
        "fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a2"
        "9f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542"
    )
    DATA_2 = [
        ["m", "03cbcaa9c98c877a26977d00825c956a238e8dddfbd322cce4f74b0b5bd6ace4a7"],
        ["m/0", "02fc9e5af0ac8d9b3cecfe2a888e2117ba3d089d8585886c9c826b6b22a98d12ea"],
        ["m/0/2147483647H", "03c01e7425647bdefa82b12d9bad5e3e6865bee0502694b94ca58b666abc0a5c3b"],
        ["m/0/2147483647H/1", "03a7d1d856deb74c508e05031f9895dab54626251b3806e16b4bd12e781a7df5b9"],
        [
            "m/0/2147483647H/1/2147483646H",
            "02d2b36900396c9282fa14628566582f206a5dd0bcc8d5e892611806cafb0301f0",
        ],
        [
            "m/0/2147483647H/1/2147483646H/2 ",
            "024d902e1a2fc7a8755ab5b694c575fce742c48d9ff192e63df5193e4c7afe1f9c",
        ],
    ]
    hdw_2 = BIP32node.master_node(SEED_2, "K1")
    for test_data2 in DATA_2:
        assert (
            hdw_2.derive_path_private(test_data2[0]).pv_key.get_public_key().hex() == test_data2[1]
        )
