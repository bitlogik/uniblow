import secrets

from cryptolib import ECP256k1

from cryptography.hazmat.primitives.asymmetric import ec

# Tests from https://github.com/paritytech/libsecp256k1/blob/master/tests/verify.rs


def gen_key():
    random_int = secrets.randbelow(ECP256k1._r)
    return ec.derive_private_key(random_int, ec.SECP256K1())


def key_to_pvint(pvkey):
    """Give private key integer from EllipticCurvePrivateKey object"""
    return pvkey.private_numbers().private_value


def key_to_coords(pvkey):
    """Set public key (x,y) from EllipticCurvePrivateKey object"""
    pubkey_numbers = pvkey.public_key().public_numbers()
    return (pubkey_numbers.x, pubkey_numbers.y)


def test_pubkeys():
    from cryptolib.cryptography import compress_pubkey, decompress_pubkey

    compr = bytes.fromhex("0339a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c2")
    uncompr = bytes.fromhex(
        "04"
        "39a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c2"
        "3cbe7ded0e7ce6a594896b8f62888fdbc5c8821305e2ea42bf01e37300116281"
    )
    assert compress_pubkey(uncompr) == compr
    assert decompress_pubkey(compr) == uncompr


def test_ECDH():
    """Test scalar point multiplication"""
    for x in range(10):
        pv_key_1 = gen_key()
        pv_key_2 = gen_key()
        Pub_1 = ECP256k1.ECPoint(*key_to_coords(pv_key_1))
        Pub_2 = ECP256k1.ECPoint(*key_to_coords(pv_key_2))
        # a.B = b.A
        assert key_to_pvint(pv_key_1) * Pub_2 == key_to_pvint(pv_key_2) * Pub_1


def test_pubkeys_add():
    Pub_1 = ECP256k1.ECPoint.from_bytes(
        bytes(
            [
                4,
                126,
                60,
                36,
                91,
                73,
                177,
                194,
                111,
                11,
                3,
                99,
                246,
                204,
                86,
                122,
                109,
                85,
                28,
                43,
                169,
                243,
                35,
                76,
                152,
                90,
                76,
                241,
                17,
                108,
                232,
                215,
                115,
                15,
                19,
                23,
                164,
                151,
                43,
                28,
                44,
                59,
                141,
                167,
                134,
                112,
                105,
                251,
                15,
                193,
                183,
                224,
                238,
                154,
                204,
                230,
                163,
                216,
                235,
                112,
                77,
                239,
                98,
                135,
                132,
            ]
        )
    )
    Pub_2 = ECP256k1.ECPoint.from_bytes(
        bytes(
            [
                4,
                40,
                127,
                167,
                223,
                38,
                53,
                6,
                223,
                67,
                83,
                204,
                60,
                226,
                227,
                107,
                231,
                172,
                34,
                3,
                187,
                79,
                112,
                167,
                0,
                217,
                118,
                69,
                218,
                189,
                208,
                150,
                190,
                54,
                186,
                220,
                95,
                80,
                220,
                183,
                202,
                117,
                160,
                18,
                84,
                245,
                181,
                23,
                32,
                51,
                73,
                178,
                173,
                92,
                118,
                92,
                122,
                83,
                49,
                54,
                195,
                194,
                16,
                229,
                39,
            ]
        )
    )
    Pub3_bin_expected = bytes(
        [
            4,
            101,
            166,
            20,
            152,
            34,
            76,
            121,
            113,
            139,
            80,
            13,
            92,
            122,
            96,
            38,
            194,
            205,
            149,
            93,
            19,
            147,
            132,
            195,
            173,
            42,
            86,
            26,
            221,
            170,
            127,
            180,
            168,
            145,
            21,
            75,
            45,
            248,
            90,
            114,
            118,
            62,
            196,
            194,
            143,
            245,
            204,
            184,
            16,
            175,
            202,
            175,
            228,
            207,
            112,
            219,
            94,
            237,
            75,
            105,
            186,
            56,
            102,
            46,
            147,
        ]
    )
    assert (Pub_1 + Pub_2).encode_output(False) == Pub3_bin_expected


def test_ycompute():
    Pub3_bin = bytes(
        [
            4,
            101,
            166,
            20,
            152,
            34,
            76,
            121,
            113,
            139,
            80,
            13,
            92,
            122,
            96,
            38,
            194,
            205,
            149,
            93,
            19,
            147,
            132,
            195,
            173,
            42,
            86,
            26,
            221,
            170,
            127,
            180,
            168,
            145,
            21,
            75,
            45,
            248,
            90,
            114,
            118,
            62,
            196,
            194,
            143,
            245,
            204,
            184,
            16,
            175,
            202,
            175,
            228,
            207,
            112,
            219,
            94,
            237,
            75,
            105,
            186,
            56,
            102,
            46,
            147,
        ]
    )
    x_coord = int.from_bytes(Pub3_bin[1:33], "big")
    assert ECP256k1.ECPoint.from_x(x_coord, 0).encode_output(False) == Pub3_bin
