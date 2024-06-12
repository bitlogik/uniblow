#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW GLMR wallet with with with RPC API REST
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
from wallets.GLMRtokens import tokens_values, ledger_tokens


class GLMR_wallet(ETH_wallet):
    coin = "GLMR"

    networks = [
        "Moonbeam",
        "Moonriver",
        "Moonbase Alpha",
    ]

    derive_paths = [
        # mainnets
        [
            "m/44'/60'/{}'/0/{}",
        ],
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

    def __init__(
        self, network, wtype, device, contract_addr=None, wc_uri=None, confirm_callback=None
    ):
        self.network = GLMR_wallet.networks[network]
        if self.network == "Moonriver":
            self.coin = "MOVR"
            self.chainID = 1285
            rpc_endpoint = "moonriver"
            self.explorer = "https://moonriver.moonscan.io/address/0x"
        if self.network == "Moonbeam":
            self.chainID = 1284
            rpc_endpoint = "moonbeam"
            self.explorer = "https://moonbeam.moonscan.io/address/0x"
        if self.network == "Moonbase Alpha":
            self.coin = "MDEV"
            self.chainID = 1287
            rpc_endpoint = "https://rpc.api.moonbase.moonbeam.network/"
            self.explorer = "https://moonbase.moonscan.io/address/0x"
        self.load_base(rpc_endpoint, device, contract_addr, wc_uri, confirm_callback, wtype != 3)
        self.ledger_tokens = ledger_tokens
