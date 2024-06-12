#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW BSC wallet with with with RPC API REST
# Copyright (C) 2021-2022 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


from copy import deepcopy
from wallets.ETHwallet import ETH_wallet
from wallets.BSCtokens import tokens_values, ledger_tokens, nfts_values


class BSC_wallet(ETH_wallet):
    coin = "BSC"

    networks = [
        "Mainnet",
        "Testnet",
    ]

    derive_paths = [
        # mainnet
        [
            "m/44'/60'/{}'/0/{}",
        ],
        # testnet
        [
            "m/44'/1'/{}'/0/{}",
        ],
    ]

    options_data = deepcopy(ETH_wallet.options_data)
    options_data[0]["preset"] = tokens_values
    options_data[2]["preset"] = nfts_values

    def __init__(
        self, network, wtype, device, contract_addr=None, wc_uri=None, confirm_callback=None
    ):
        self.network = BSC_wallet.networks[network].lower()
        if self.network == "mainnet":
            self.chainID = 56
            rpc_endpoint = "bsc"
            self.explorer = "https://www.bscscan.com/address/0x"
        if self.network == "testnet":
            self.chainID = 97
            rpc_endpoint = "https://data-seed-prebsc-2-s2.binance.org:8545/"
            self.explorer = "bsc-testnet"
        self.load_base(rpc_endpoint, device, contract_addr, wc_uri, confirm_callback, wtype != 3)
        self.ledger_tokens = ledger_tokens
