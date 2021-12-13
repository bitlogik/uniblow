from wallets.ETHwallet import ETHwalletCore


fake_api = None
dummy_pubkey = "0238a4f4226db063fd940eee86d7d130832a2e1175fd6a8c4bd2f031fb6cf8c676"
ERC20_contract = "0x6b175474e89094c44da98b954eedeac495271d0f"


def dummy_balance(self=None, erc20=None):
    return 2000000000000000000


def test_eth_tx():
    # Test building an ETH transaction
    # 1 ETH to 0x3535, gas price = 20 GWei, nonce = 9
    ETHwalletCore.get_decimals = lambda _: 18
    ETHwalletCore.get_symbol = lambda _: "ETH"
    wl = ETHwalletCore(dummy_pubkey, "mainnet", fake_api, 1)
    wl.getbalance = dummy_balance
    wl.getnonce = lambda: 9
    to_addr = "3535353535353535353535353535353535353535"
    amount_value = 1000000000000000000
    gas_price = 20000000000
    gas_limit = 21000
    wl.prepare(to_addr, amount_value, gas_price, gas_limit)
    assert wl.datahash.hex() == "daf5a779ae972f972197303d7b574746c7ef83eadac0f2791ad23db92e4c8e53"


def test_erc20_tx():
    # Test building an ERC20 transaction, on the CSC network id = 52
    # 2 DAI to 0x5322, gas price = 42 GWei, gas limit = 78009
    ETHwalletCore.get_decimals = lambda _: 18
    ETHwalletCore.get_symbol = lambda _: "DAI"
    wl = ETHwalletCore(dummy_pubkey, "other network", fake_api, 52, ERC20_contract)
    wl.getbalance = dummy_balance
    wl.getnonce = lambda: 0
    to_addr = "5322b34c88ed0691971bf52a7047448f0f4efc84"
    amount_value = 2 * 1000000000000000000
    gas_price = 42000000000
    gas_limit = 78009
    wl.prepare(to_addr, amount_value, gas_price, gas_limit)
    assert wl.datahash.hex() == "b3525019dc367d3ecac48905f9a95ff3550c25a24823db765f92cae2dec7ebfd"
