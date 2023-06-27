from cryptolib.ECKeyPair import EC_key_pair
from wallets.TRXwallet import TRX_wallet


def test_tron_address():
    skey = 0xDEFEDCD7B8D82434549550AD9611834FE62E62E4527A05C792F36804CE604BAB
    kpair = EC_key_pair(skey, "K1")
    assert TRX_wallet(0, 0, kpair).address == "THjtwRbkJfXQQVRUSfjU2yBtiTwi1bZsDh"
    skey = 0x3481E79956D4BD95F358AC96D151C976392FC4E3FC132F78A847906DE588C145
    kpair = EC_key_pair(skey, "K1")
    assert TRX_wallet(0, 0, kpair).address == "TNPeeaaFB7K9cmo4uQpcU32zGK8G1NYqeL"
