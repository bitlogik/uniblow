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
from ..transaction import SIGHASH_ALL, SIGHASH_FORKID

# from ..explorers import blockdozer


class BitcoinCash(BaseCoin):
    coin_symbol = "bcc"
    display_name = "Bitcoin Cash"
    segwit_supported = False
    magicbyte = 0
    script_magicbyte = 5
    wif_prefix = 0x80
    hd_path = 145
    # explorer = blockdozer
    hashcode = SIGHASH_ALL | SIGHASH_FORKID
    testnet_overrides = {
        "display_name": "Bitcoin Cash Testnet",
        "coin_symbol": "tbcc",
        "magicbyte": 111,
        "script_magicbyte": 196,
        "wif_prefix": 0xEF,
        "xprv_headers": {
            "p2pkh": 0x04358394,
        },
        "xpub_headers": {
            "p2pkh": 0x043587CF,
        },
        "hd_path": 1,
    }

    def __init__(self, legacy=False, testnet=False, **kwargs):
        super(BitcoinCash, self).__init__(testnet=testnet, **kwargs)
        self.hd_path = 0 if legacy and testnet else self.hd_path
