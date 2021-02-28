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

# from ..explorers import dash_siampm


class Dash(BaseCoin):
    coin_symbol = "DASH"
    display_name = "Dash"
    segwit_supported = False
    magicbyte = 76
    script_magicbyte = 16
    wif_prefix = 0xCC
    hd_path = 5
    # explorer = dash_siampm
    testnet_overrides = {
        "display_name": "Dash Testnet",
        "coin_symbol": "DASHTEST",
        "magicbyte": 140,
        "script_magicbyte": 19,
        "hd_path": 1,
        "xpriv_prefix": 0x04358394,
        "xpub_prefix": 0x043587CF,
    }
