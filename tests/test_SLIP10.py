from cryptolib.HDwallet import BIP32node

# Tests from BIP32 and SLIP10 vectors


def test_slip10_P1_vect1():
    SEED_1 = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    DATA_1 = [
        ["m", "0266874dc6ade47b3ecd096745ca09bcd29638dd52c2c12117b11ed3e458cfa9e8"],
        ["m/0H", "0384610f5ecffe8fda089363a41f56a5c7ffc1d81b59a612d0d649b2d22355590c"],
        ["m/0H/1", "03526c63f8d0b4bbbf9c80df553fe66742df4676b241dabefdef67733e070f6844"],
        ["m/0H/1/2H", "0359cf160040778a4b14c5f4d7b76e327ccc8c4a6086dd9451b7482b5a4972dda0"],
        ["m/0H/1/2H/2", "029f871f4cb9e1c97f9f4de9ccd0d4a2f2a171110c61178f84430062230833ff20"],
        [
            "m/0H/1/2H/2/1000000000",
            "02216cd26d31147f72427a453c443ed2cde8a1e53c9cc44e5ddf739725413fe3f4",
        ],
    ]
    hdw_1 = BIP32node.master_node(SEED_1, "R1")
    for test_data1 in DATA_1:
        assert (
            hdw_1.derive_path_private(test_data1[0]).pv_key.get_public_key().hex() == test_data1[1]
        )


def test_slip10_Ed_vect1():
    SEED_1 = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    DATA_1 = [
        ["m", "a4b2856bfec510abab89753fac1ac0e1112364e7d250545963f135f2a33188ed"],
        ["m/0H", "8c8a13df77a28f3445213a0f432fde644acaa215fc72dcdf300d5efaa85d350c"],
        ["m/0H/1H", "1932a5270f335bed617d5b935c80aedb1a35bd9fc1e31acafd5372c30f5c1187"],
        ["m/0H/1H/2H", "ae98736566d30ed0e9d2f4486a64bc95740d89c7db33f52121f8ea8f76ff0fc1"],
        ["m/0H/1H/2H/2H", "8abae2d66361c879b900d204ad2cc4984fa2aa344dd7ddc46007329ac76c429c"],
        [
            "m/0H/1H/2H/2H/1000000000H",
            "3c24da049451555d51a7014a37337aa4e12d41e485abccfa46b47dfb2af54b7a",
        ],
    ]
    hdw_1 = BIP32node.master_node(SEED_1, "ED")
    for test_data1 in DATA_1:
        assert (
            hdw_1.derive_path_private(test_data1[0]).pv_key.get_public_key().hex() == test_data1[1]
        )


def test_slip10_P1_vect2():
    SEED_2 = bytes.fromhex(
        "fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a2"
        "9f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542"
    )
    DATA_2 = [
        ["m", "02c9e16154474b3ed5b38218bb0463e008f89ee03e62d22fdcc8014beab25b48fa"],
        ["m/0", "039b6df4bece7b6c81e2adfeea4bcf5c8c8a6e40ea7ffa3cf6e8494c61a1fc82cc"],
        ["m/0/2147483647H", "02f89c5deb1cae4fedc9905f98ae6cbf6cbab120d8cb85d5bd9a91a72f4c068c76"],
        ["m/0/2147483647H/1", "03abe0ad54c97c1d654c1852dfdc32d6d3e487e75fa16f0fd6304b9ceae4220c64"],
        [
            "m/0/2147483647H/1/2147483646H",
            "03cb8cb067d248691808cd6b5a5a06b48e34ebac4d965cba33e6dc46fe13d9b933",
        ],
        [
            "m/0/2147483647H/1/2147483646H/2",
            "020ee02e18967237cf62672983b253ee62fa4dd431f8243bfeccdf39dbe181387f",
        ],
    ]
    hdw_2 = BIP32node.master_node(SEED_2, "R1")
    for test_data2 in DATA_2:
        assert (
            hdw_2.derive_path_private(test_data2[0]).pv_key.get_public_key().hex() == test_data2[1]
        )


def test_slip10_Ed_vect2():
    SEED_2 = bytes.fromhex(
        "fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a2"
        "9f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542"
    )
    DATA_2 = [
        ["m", "8fe9693f8fa62a4305a140b9764c5ee01e455963744fe18204b4fb948249308a"],
        ["m/0H", "86fab68dcb57aa196c77c5f264f215a112c22a912c10d123b0d03c3c28ef1037"],
        ["m/0H/2147483647H", "5ba3b9ac6e90e83effcd25ac4e58a1365a9e35a3d3ae5eb07b9e4d90bcf7506d"],
        ["m/0H/2147483647H/1H", "2e66aa57069c86cc18249aecf5cb5a9cebbfd6fadeab056254763874a9352b45"],
        [
            "m/0H/2147483647H/1H/2147483646H",
            "e33c0f7d81d843c572275f287498e8d408654fdf0d1e065b84e2e6f157aab09b",
        ],
        [
            "m/0H/2147483647H/1H/2147483646H/2H",
            "47150c75db263559a70d5778bf36abbab30fb061ad69f69ece61a72b0cfa4fc0",
        ],
    ]
    hdw_2 = BIP32node.master_node(SEED_2, "ED")
    for test_data2 in DATA_2:
        assert (
            hdw_2.derive_path_private(test_data2[0]).pv_key.get_public_key().hex() == test_data2[1]
        )
