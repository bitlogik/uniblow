from cryptolib.HDwallet import HD_Wallet
from wallets.SOLwallet import SOL_wallet


def mnemonic2soladdr(mnemonic, path=None):
    if not path:
        path = SOL_wallet.get_path(0, 0, False).format(0, 0)
    seed = HD_Wallet.seed_from_mnemonic(mnemonic)
    hdwallet = HD_Wallet.from_seed(seed, "ED")
    device_key = hdwallet.derive_key(path)
    return SOL_wallet(0, 0, device_key).sol.address


def test_sol_derive():
    # https://www.abiraja.com/blog/from-seed-phrase-to-solana-address
    tst_mnemonic = "crush desk brain index action subject tackle idea trim unveil lawn live"
    assert mnemonic2soladdr(tst_mnemonic) == "7EWwMxKQa5Gru7oTcS1Wi3AaEgTfA6MU3z7MaLUT6hnD"

    # https://github.com/trustwallet/wallet-core/blob/master/tests/chains/Solana/TWSolanaAddressTests.cpp
    tst_mnemonic = (
        "shoot island position soft burden budget tooth cruel issue economy destroy above"
    )
    assert (
        mnemonic2soladdr(tst_mnemonic, "m/44'/501'/0'")
        == "2bUBiBNZyD29gP1oV6de7nxowMLoDBtopMMTGgMvjG5m"
    )
