#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW EOS wallet
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
#


import pytz
import datetime as dt
import json
import re

from cryptolib.base58 import bin_to_base58_eos
from cryptolib.cryptography import public_key_recover, decompress_pubkey

from eospy.cleos import Cleos
from eospy.utils import sig_digest
from eospy.types import EOSEncoder, Transaction


def compute_eos_address(pubkey, key_type="K1"):
    return f"PUB_{key_type}_{bin_to_base58_eos(pubkey, key_type)}"


class eos_api:
    def __init__(self, network):
        self.network = network
        if self.network == "EOSio":
            self.url = "https://eos.greymass.com"
        elif self.network == "Jungle3":
            self.url = "https://api.jungle3.alohaeos.com"
        else:
            raise Exception("Not valid EOS network")
        self.libeos = Cleos(url=self.url)

    def get_balance(self, account):
        return self.libeos.get_currency_balance(account)

    def get_account(self, address):
        accounts_info = self.libeos.get_accounts(address)
        if len(accounts_info["account_names"]) > 0:
            return accounts_info["account_names"][0]
        else:
            return ""

    def pushtx(self, txdata):
        return self.libeos.post("chain.push_transaction", params=None, data=txdata, timeout=30)

    def get_tx_num(self, addr, blocks):
        self.getData("eth_getTransactionCount", ["0x" + addr, blocks])
        self.checkapiresp()
        return int(self.getKey("result")[2:], 16)

    def getKey(self, keychar):
        out = self.jsres
        path = keychar.split("/")
        for key in path:
            if key.isdigit():
                key = int(key)
            try:
                out = out[key]
            except Exception:
                out = []
        return out


def testaddr(eos_account):
    # Safe reading of the account format
    if len(eos_account) != 12:
        return False
    if account_pattern.match(eos_account) is None:
        return False
    return True


account_pattern = re.compile(r"^[a-z1-5]{12}$")


class EOSwalletCore:
    def __init__(self, pubkey, network, api):
        self.pubkey = decompress_pubkey(pubkey)
        self.api = api
        self.address = compute_eos_address(bytes.fromhex(pubkey))
        self.account = self.getaccount(self.address)
        self.network = network

    def getbalance(self):
        return self.api.get_balance(self.account)

    def getaccount(self, addr):
        return self.api.get_account(addr)

    def prepare(self, to_account, pay_value):
        bal_str = self.getbalance()
        balance = float(bal_str[0][:-4]) if len(bal_str) > 0 else 0.0
        if float(pay_value) > balance:
            raise Exception("Not enough fund for the tx")
        if isinstance(pay_value, int) or isinstance(pay_value, float):
            qty = "%.4f %s" % (pay_value, "EOS")
        elif isinstance(pay_value, str):
            qty = "%.4f %s" % (float(pay_value), "EOS")
        else:
            raise Exception("to_account variable must be int float or string")
        args = {
            "from": self.account,
            "to": to_account,
            "quantity": qty,
            "memo": "",
        }
        payload = {
            "account": "eosio.token",
            "name": "transfer",
            "authorization": [
                {
                    "actor": self.account,
                    "permission": "active",
                }
            ],
        }
        data = self.api.libeos.abi_json_to_bin(payload["account"], payload["name"], args)
        payload["data"] = data["binargs"]
        trx = {"actions": [payload]}
        trx["expiration"] = str(
            (dt.datetime.utcnow() + dt.timedelta(seconds=60)).replace(tzinfo=pytz.UTC)
        )
        chain_info, lib_info = self.api.libeos.get_chain_lib_info()
        self.tx_info = Transaction(trx, chain_info, lib_info)
        self.datahash = bytes.fromhex(sig_digest(self.tx_info.encode(), chain_info["chain_id"]))
        return self.datahash

    def send(self, signature_der):
        # Signature decoding
        lenr = int(signature_der[3])
        lens = int(signature_der[5 + lenr])
        r = int.from_bytes(signature_der[4 : lenr + 4], "big")
        s = int.from_bytes(signature_der[lenr + 6 : lenr + 6 + lens], "big")
        # Parity recovery
        i = 31
        h = int.from_bytes(self.datahash, "big")
        if public_key_recover(h, r, s, i) != self.pubkey:
            i += 1
        # Signature encoding
        # pack
        ib = i.to_bytes(1, byteorder="big")
        rb = r.to_bytes(32, byteorder="big")
        sb = s.to_bytes(32, byteorder="big")
        sig_bin = ib + rb + sb
        # encode
        sigtype = "K1"
        signature_b58 = f"SIG_{sigtype}_{bin_to_base58_eos(sig_bin, sigtype)}"
        final_tx = {
            "compression": "none",
            "transaction": self.tx_info.__dict__,
            "signatures": [signature_b58],
        }
        data_tx = json.dumps(final_tx, cls=EOSEncoder)
        ret_tx = self.api.pushtx(data_tx)
        return "\nDONE, txID : " + ret_tx["transaction_id"]


# Only local key for now
class EOS_wallet:

    coin = "EOS"

    networks = [
        "EOSio",
        "Jungle3",
    ]

    wtypes = [
        "K1",
    ]

    derive_paths = [
        # mainnet
        [
            "m/44'/194'/0'/0/",
        ],
        # testnet
        [
            "m/44'/1'/0'/0/",
        ],
    ]

    def __init__(self, network, wtype, device):
        self.network = EOS_wallet.networks[network]
        self.key_type = EOS_wallet.wtypes[wtype]
        self.current_device = device
        pubkey_hex = self.current_device.get_public_key()
        self.eos = EOSwalletCore(pubkey_hex, self.network, eos_api(self.network))

    @classmethod
    def get_networks(cls):
        return cls.networks

    @classmethod
    def get_account_types(cls):
        return cls.wtypes

    @classmethod
    def get_path(cls, network_name, wtype):
        return cls.derive_paths[network_name][wtype]

    def get_account(self):
        # Read account to fund the wallet
        return self.eos.account if self.eos.account else self.eos.address

    def get_balance(self):
        # Get balance in base integer unit
        if not self.eos.account:
            return "Register this publickey\nin an account, and refresh."
        bal_list = self.eos.getbalance()
        return bal_list[0] if len(bal_list) > 0 else f"0 {self.coin}"

    def check_address(self, addr_str):
        # Check if address is valid
        return testaddr(addr_str)

    def history(self):
        # Get history page
        if self.eos.account:
            if self.network == "EOSio":
                EOS_EXPLORER_URL = f"https://bloks.io/account/{self.eos.account}"
            else:
                EOS_EXPLORER_URL = (
                    f"https://{self.network.lower()}.bloks.io/account/{self.eos.account}"
                )
            return EOS_EXPLORER_URL

    def transfer(self, amount, to_account, priority_fee):
        # Transfer x unit to an account, pay
        hash_to_sign = self.eos.prepare(to_account, amount)
        # sign until R|S = 2x32
        len_r = 0
        len_s = 0
        while len_r != 32 or len_s != 32:
            tx_signature = self.current_device.sign(hash_to_sign)
            len_r = int(tx_signature[3])
            len_s = int(tx_signature[5 + len_r])
        return self.eos.send(tx_signature)

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.get_balance()
        return self.transfer(all_amount, to_account, fee_priority)
