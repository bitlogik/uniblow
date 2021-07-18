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


class Litecoin(BaseCoin):
    coin_symbol = "LTC"
    display_name = "Litecoin"
    segwit_supported = True
    magicbyte = 48
    script_magicbyte = 50  # Supposed to be new magicbyte
    # script_magicbyte = 5  # Old magicbyte still recognised by explorers
    wif_prefix = 0xB0
    segwit_hrp = "ltc1"
    hd_path = 2
    testnet_overrides = {
        "display_name": "Litecoin Testnet",
        "coin_symbol": "LTCTEST",
        "magicbyte": 111,
        "script_magicbyte": 58,  # Supposed to be new magicbyte
        # "script_magicbyte": 196,  # Old magicbyte still recognised by explorers,
        "segwit_hrp": "tltc1",
        "hd_path": 1,
        "xpriv_prefix": 0x04358394,
        "xpub_prefix": 0x043587CF,
    }
