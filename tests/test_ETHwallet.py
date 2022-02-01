from cryptolib.HDwallet import HD_Wallet
from wallets.ETHwallet import ETH_wallet


def path2addre(wallet, account=0, index=0, path=None, typew=0, network=0):
    if not path:
        path = ETH_wallet.get_path(network, typew, False).format(account, index)
    device_key = wallet.derive_key(path)
    return "0x" + ETH_wallet(network, typew, device_key).eth.address


def test_eth_derive():
    """Standard address"""
    tst_mnemonic = "estate camera orbit figure ready submit pet jungle emotion cruise fade cousin"
    seed = HD_Wallet.seed_from_mnemonic(tst_mnemonic)
    hdwallet = HD_Wallet.from_seed(seed, "K1")
    assert path2addre(hdwallet, 0, 0) == "0x1Dee31D1363DE1bB7a9938EE6a953232e18B11F7"
    tst_mnemonic = "poet hair exist raven affair fragile shine urge violin rough bar legal urban nominee crowd middle seek good upgrade parent very valley jealous hungry"
    seed = HD_Wallet.seed_from_mnemonic(tst_mnemonic)
    hdwallet = HD_Wallet.from_seed(seed, "K1")
    assert path2addre(hdwallet, 0, 0) == "0x2bE9A8a823c70A4EcDcB1441cD5FD0aFd95c9832"
