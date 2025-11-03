from cryptolib.HDwallet import HD_Wallet
from wallets.XTZwallet import XTZ_wallet


def mnemonic2xtzaddr(mnemonic, path=None):
    if not path:
        path = XTZ_wallet.get_path(0, 1, False).format(0, 0)
    seed = HD_Wallet.seed_from_mnemonic(mnemonic)
    hdwallet = HD_Wallet.from_seed(seed, "ED")
    device_key = hdwallet.derive_key(path)
    return XTZ_wallet(0, 1, device_key).xtz.address


def test_xtz_derive():
    tst_mnemonic = "clarify flash mansion forward turtle dinner drill turkey dry draw kidney brain fruit tiny aspect"
    assert mnemonic2xtzaddr(tst_mnemonic) == "tz1XZzisKx1JUCcdojghd7yv7dBLCpzXRpxB"

    #  https://github.com/kukai-wallet/kukai/blob/production/spec/mocks/library.mock.ts
    tst_mnemonic = "icon salute dinner depend radio announce urge hello danger join long toe ridge clever toast opera spot rib outside explain mixture eyebrow brother share"
    assert mnemonic2xtzaddr(tst_mnemonic) == "tz1TogVQurVUhTFY1d62QJGmkMdEadM9MNpu"
    second_account_path = "m/44'/1729'/1'/0'"
    assert (
        mnemonic2xtzaddr(tst_mnemonic, second_account_path)
        == "tz1dXCZTs4pRTVvoXJXNRUmrYqtCde4fdP8N"
    )
