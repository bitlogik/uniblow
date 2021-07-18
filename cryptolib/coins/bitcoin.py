# -*- coding: utf8 -*-

# UNIBLOW BTC lib wallet
# Copyright (C) 2015-2019 Vitalik Buterin and pycryptools developers
# Copyright (C) 2019-2021 primal100
# Copyright (C) 2021 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from .base import BaseCoin


class Bitcoin(BaseCoin):
    coin_symbol = "BTC"
    display_name = "Bitcoin"
    segwit_supported = True
    magicbyte = 0
    script_magicbyte = 5
    segwit_hrp = "bc"
    client_kwargs = {
        "server_file": "bitcoin.json",
    }

    testnet_overrides = {
        "display_name": "Bitcoin Testnet",
        "coin_symbol": "BTCTEST",
        "magicbyte": 111,
        "script_magicbyte": 196,
        "segwit_hrp": "tb",
        "hd_path": 1,
        "wif_prefix": 0xEF,
        "client_kwargs": {
            "server_file": "bitcoin_testnet.json",
        },
        "xprv_headers": {
            "p2pkh": 0x04358394,
            "p2wpkh-p2sh": 0x044A4E28,
            "p2wsh-p2sh": 0x295B005,
            "p2wpkh": 0x04358394,
            "p2wsh": 0x2AA7A99,
        },
        "xpub_headers": {
            "p2pkh": 0x043587CF,
            "p2wpkh-p2sh": 0x044A5262,
            "p2wsh-p2sh": 0x295B43F,
            "p2wpkh": 0x043587CF,
            "p2wsh": 0x2AA7ED3,
        },
    }
