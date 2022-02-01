from cryptolib.HDwallet import HD_Wallet
from wallets.BTCwallet import BTC_wallet


def path2addr(wallet, account=0, index=0, path=None, typew=0, network=0):
    if not path:
        path = BTC_wallet.get_path(network, typew, False).format(account, index)
    device_key = wallet.derive_key(path)
    return BTC_wallet(network, typew, device_key).btc.address


def test_btc_derive_std1():
    """Standard Legacy addresses"""
    tst_mnemonic = "estate camera orbit figure ready submit pet jungle emotion cruise fade cousin"
    seed = HD_Wallet.seed_from_mnemonic(tst_mnemonic)
    assert (
        seed.hex()
        == "4d8ad83f78568605716cbb72c6cc63a609fca07c572813b50369be56259d35d7d8abf87aa264d656e012ffcc206036264abf04c95476818d24927f8ba105e40a"
    )
    hdwallet = HD_Wallet.from_seed(seed, "K1")
    assert (
        hdwallet.master_node.pv_key.get_public_key(True).hex()
        == "0289bec3f35f0b25ba64ce27e70ba98f5f46485c051832659ec90f86242426d725"
    )
    assert path2addr(hdwallet, 0, 0) == "1FoNgoKR4E7uWDLJvn86MTWH2qCDX77WCY"
    assert path2addr(hdwallet, path="m/44'/0'/0'/1/0") == "1mTsSwv5TDRyZN47RbexrXPwZCacxZX5u"
    assert path2addr(hdwallet, 0, 1) == "1MeBTBdsZzDWPjSh7Lh2yPjP3SqYLpuohw"
    assert path2addr(hdwallet, 0, 2) == "1JnofrZeNaSdydaewQL8xXYh62F79QnZTy"
    assert path2addr(hdwallet, 0, 3) == "1FE7MvXgJ5wRMAzicqejRzSfmfxSLtjkHC"
    assert path2addr(hdwallet, 0, 4) == "1CYFR4NMw1nSJEn7i2R8sgQuU5MzgjL3UA"


def test_btc_derive_std2():
    """Standard Legacy addresses, different mnemonic"""
    tst_mnemonic = "poet hair exist raven affair fragile shine urge violin rough bar legal urban nominee crowd middle seek good upgrade parent very valley jealous hungry"
    seed = HD_Wallet.seed_from_mnemonic(tst_mnemonic)
    assert (
        seed.hex()
        == "b8ac4c18f027d1c0b271f02ef57832d22ef62d26d781a3953e25a6c786a455e3a1ec3f16b443717b6527df6249f0affc2ab53a1bccb5e808fb4dbe36b940dd7d"
    )
    hdwallet = HD_Wallet.from_seed(seed, "K1")
    assert (
        hdwallet.master_node.pv_key.get_public_key(True).hex()
        == "02b59fc316bc45ff0f983643397a9ff656c3a37f5042d0f28140ca0262bc78a9b0"
    )
    assert path2addr(hdwallet) == "1JPuTvXABaGpgd42T1T9VqUnRKuTQTrTYM"
    assert path2addr(hdwallet, path="m/44'/0'/0'/1/0") == "1HkLkzPXbh1kyN4tcm8fuw9kTFFpwqxUyv"
    assert path2addr(hdwallet, 0, 1) == "17hNXERrnQHM6LbQskk7FEgfvr5mSzwXXC"
    assert path2addr(hdwallet, 0, 2) == "1N1KSr6vqR24HuUkbt1qnz4QwqCVXhRyWH"
    assert path2addr(hdwallet, 0, 3) == "1JSMHZRQhsBBW4J8QuEAbf1jc6gSbJwzmr"
    assert path2addr(hdwallet, 0, 4) == "16V9RVhBcfqdPVTFhtawwHyvd6RpHUZ4MA"


def test_btc_derive_p2sh():
    """Compatible Segwit P2SH addresses"""
    tst_mnemonic = "poet hair exist raven affair fragile shine urge violin rough bar legal urban nominee crowd middle seek good upgrade parent very valley jealous hungry"
    seed = HD_Wallet.seed_from_mnemonic(tst_mnemonic)
    hdwallet = HD_Wallet.from_seed(seed, "K1")
    assert path2addr(hdwallet, typew=1) == "3DjaFPuY3TT9KezrbeZUhWYrvKkAE39E3f"
    assert (
        path2addr(hdwallet, path="m/49'/0'/0'/1/0", typew=1) == "3KtHTKyHTJHQP6zC98uYSqgTPFWcMGHWCi"
    )
    assert path2addr(hdwallet, 0, 1, typew=1) == "3LAsCTZMEKortGM7gxmbRSLokeJNBE9faD"
    assert path2addr(hdwallet, 0, 2, typew=1) == "3CQat7Gb6i3KLoc864gNj8MPhNTFochTnE"
    assert path2addr(hdwallet, 0, 3, typew=1) == "3BeiccyBVs6yRDbEJaipoZoDwQih7PsggK"
    assert path2addr(hdwallet, 0, 4, typew=1) == "31wYem8JggAWZRtf6HRohkwCQSJgLWNFUe"


def test_btc_derive_p2wpkh():
    """Full Segwit bech 32 addresses"""
    tst_mnemonic = "poet hair exist raven affair fragile shine urge violin rough bar legal urban nominee crowd middle seek good upgrade parent very valley jealous hungry"
    seed = HD_Wallet.seed_from_mnemonic(tst_mnemonic)
    hdwallet = HD_Wallet.from_seed(seed, "K1")
    assert path2addr(hdwallet, typew=2) == "bc1q5zkxfxmqg9y8fxe9nztscdqs74k6482y4gg8r6"
    assert (
        path2addr(hdwallet, path="m/84'/0'/0'/1/0", typew=2)
        == "bc1qjyw49r7nj0k9netqpkzvsl436c3hswh2jfd2kq"
    )
    assert path2addr(hdwallet, 0, 1, typew=2) == "bc1qns5u4rpjr04ephgvvdk067j2shslf55fvfp9f8"
    assert path2addr(hdwallet, 0, 2, typew=2) == "bc1q7v4sj7lqectqg4v88lpqzx7cz9x6j8r9pt6uwt"
    assert path2addr(hdwallet, 0, 3, typew=2) == "bc1qhph75l44agexppl9z9vjtczdfe0zfc2kumljd4"
    assert path2addr(hdwallet, 0, 4, typew=2) == "bc1qmfuk82g99lvqzz9el2xflertxgq8qrxszk70uz"
