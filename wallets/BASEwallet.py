#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Base wallet with RPC API REST
# Copyright (C) 2021-2024 BitLogiK

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
from wallets.BASEtokens import tokens_values, ledger_tokens


class BASE_wallet(ETH_wallet):
    coin = "BASE/ETH"

    sendall_notallowed = True

    networks = [
        "Mainnet",
        "BaseSepolia",
    ]

    derive_paths = [
        # Mainnet
        [
            "m/44'/60'/{}'/0/{}",
        ],
        # Testnet Sepolia
        [
            "m/44'/1'/{}'/0/{}",
        ],
    ]

    options_data = deepcopy(ETH_wallet.options_data)
    options_data[0]["preset"] = tokens_values

    def __init__(
        self, network, wtype, device, contract_addr=None, wc_uri=None, confirm_callback=None
    ):
        self.network = BASE_wallet.networks[network].lower()
        if self.network == "mainnet":
            self.chainID = 8453
            rpc_endpoint = "base"
            self.explorer = "https://basescan.org/address/0x"
        elif self.network == "basesepolia":
            self.chainID = 84532
            rpc_endpoint = "base-sepolia"
            self.explorer = "https://sepolia.basescan.org/address/0x"
        else:
            raise ValueError("Wrong BASE network.")
        self.load_base(rpc_endpoint, device, contract_addr, wc_uri, confirm_callback, wtype != 3)
        self.ledger_tokens = ledger_tokens
