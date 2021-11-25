import pytest

from cryptolib.HDwallet import HD_Wallet, ElectrumOldWallet
from wallets.BTCwallet import BTC_wallet

TEST_MNEMONIC = "content frustrate harsh paint given careful hello peach glance nerve either mask"


def path2addr(wallet, path):
    device_key = wallet.derive_key(path)
    return BTC_wallet(0, 0, device_key).btc.address


def test_old_electrum():
    seed = HD_Wallet.seed_from_mnemonic(TEST_MNEMONIC, passw="", std="ElectrumOLD")
    assert seed.hex() == "cd67e78c8ea0c19793840cff0aa8367c"
    hdwallet = ElectrumOldWallet.from_seed(seed)
    assert (
        hdwallet.master_private_key.get_public_key().hex()
        == "043f50060b88a14d24e493aef0fca5d8ae3205a1e05456035e43d45aa0acfb83474d816bd140f765e8527f7c0b73a39003a36b0204fe9d67dea6ce985335e2d042"
    )

    assert path2addr(hdwallet, "m/0/0") == "1BkdVZWMZjA4gwNvC8DapFsEzHkFMoKXDd"
    assert path2addr(hdwallet, "m/1/0") == "1DGj7HVwaxJNwWGFDrfpr35C6nbShf7pSt"
    assert path2addr(hdwallet, "m/0/1") == "19pS4DeFpa5qqmKR2qD739c55rSyUENwGT"
    assert path2addr(hdwallet, "m/0/2") == "13w1XbUET2Amvx3m8WNzYcriCLuKDBwsFm"
    assert path2addr(hdwallet, "m/0/3") == "113SdLXrf2bD5oCeaYsyipgdvurJXiUs2s"
    assert path2addr(hdwallet, "m/0/4") == "19wip5SFHaV1fmP63RDsGBpwbdbWpfFoJL"
