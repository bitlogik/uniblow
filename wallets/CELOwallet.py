#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW CELO wallet with with with RPC API REST
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
from wallets.CELOtokens import tokens_values, ledger_tokens


class CELO_wallet(ETH_wallet):
    coin = "CELO"

    networks = [
        "Mainnet",
        "Alfajores",
        "Baklava",
    ]

    derive_paths = [
        # mainnet
        [
            "m/44'/60'/{}'/0/{}",
        ],
        # testnets
        [
            "m/44'/1'/{}'/0/{}",
        ],
        [
            "m/44'/1'/{}'/0/{}",
        ],
    ]

    options_data = deepcopy(ETH_wallet.options_data)
    options_data[0]["preset"] = tokens_values

    def __init__(
        self, network, wtype, device, contract_addr=None, wc_uri=None, confirm_callback=None
    ):
        self.network = CELO_wallet.networks[network].lower()
        if self.network == "mainnet":
            self.chainID = 42220
            rpc_endpoint = "celo"
            self.explorer = "https://explorer.celo.org/address/0x"
        if self.network == "alfajores":
            self.chainID = 44787
            rpc_endpoint = "https://alfajores-forno.celo-testnet.org/"
            self.explorer = "https://alfajores-blockscout.celo-testnet.org/address/0x"
        if self.network == "baklava":
            self.chainID = 62320
            rpc_endpoint = "https://baklava-forno.celo-testnet.org/"
            self.explorer = "https://baklava-blockscout.celo-testnet.org/address/0x"
        self.load_base(rpc_endpoint, device, contract_addr, wc_uri, confirm_callback, wtype != 3)
        self.ledger_tokens = ledger_tokens
