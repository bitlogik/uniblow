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

from .bitcoin import BaseCoin

# from ..explorers import sochain


class Doge(BaseCoin):
    coin_symbol = "DOGE"
    display_name = "Dogecoin"
    segwit_supported = False
    magicbyte = 30
    script_magicbyte = 22
    to_wif = 0x9E
    hd_path = 3
    # explorer = sochain
    xpriv_prefix = 0x02FACAFD
    xpub_prefix = 0x02FAC398
    testnet_overrides = {
        "display_name": "Dogecoin Testnet",
        "coin_symbol": "Dogecoin",
        "magicbyte": 113,
        "script_magicbyte": 196,
        "hd_path": 1,
        "xpriv_prefix": 0x04358394,
        "xpub_prefix": 0x043587CF,
    }
