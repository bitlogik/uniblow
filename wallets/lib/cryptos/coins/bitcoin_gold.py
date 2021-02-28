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

# from ..explorers import btg_explorer
from ..main import b58check_to_bin
from ..py3specials import bin_to_b58check

FORKID_BTG = 79


class BitcoinGold(BaseCoin):
    coin_symbol = "btg"
    display_name = "Bitcoin Gold"
    segwit_supported = True
    magicbyte = 38
    script_magicbyte = 23
    wif_prefix = 0x80
    hd_path = 0
    # explorer = btg_explorer
    hashcode = SIGHASH_ALL | SIGHASH_FORKID | FORKID_BTG << 8
    segwit_hrp = "bc"
    testnet_overrides = {
        "display_name": "Bitcoin Gold Testnet",
        "coin_symbol": "tbcc",
        "magicbyte": 111,
        "script_magicbyte": 196,
        "wif_prefix": 0xEF,
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
        "hd_path": 1,
    }

    def __init__(self, testnet=False, legacy=False, **kwargs):
        super(BitcoinGold, self).__init__(testnet=testnet, **kwargs)
        if legacy and not testnet:
            self.magicbyte = 0
            self.script_magicbyte = 5

    def address_from_btc(self, addr):
        pubkey_hash = b58check_to_bin(addr)
        return bin_to_b58check(pubkey_hash, self.magicbyte)

    def sh_address_from_btc(self, addr):
        pubkey_hash = b58check_to_bin(addr)
        return bin_to_b58check(pubkey_hash, self.script_magicbyte)
