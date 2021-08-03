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


import json
import re
import urllib.request

from cryptolib.base58 import bin_to_base58_eos
from cryptolib.coins.eos import (
    uint2bin,
    uint16,
    uint32,
    string_to_binname,
    encode_varuint,
    expiration_string_epoch_int,
    near_future_iso_str,
)
from cryptolib.cryptography import public_key_recover, decompress_pubkey, sha2


def compute_eos_address(pubkey, key_type="K1"):
    return f"PUB_{key_type}_{bin_to_base58_eos(pubkey, key_type)}"


def serialize_tx(tx_obj):
    """Serialize a transaction to binary"""
    # Transaction is restricted :
    #    A single action / authorization
    #    Empty context actions
    #    Empty extensions
    # Encode transaction header
    exp_ts = expiration_string_epoch_int(tx_obj["expiration"])
    exp = uint32(exp_ts)
    ref_blk = uint16(tx_obj["ref_block_num"] & 0xFFFF)
    ref_block_prefix = uint32(tx_obj["ref_block_prefix"])
    net_usage_words = encode_varuint(tx_obj["max_net_usage_words"])
    max_cpu_usage_ms = uint2bin(tx_obj["max_cpu_usage_ms"], 1)
    delay_sec = encode_varuint(tx_obj["delay_sec"])
    tx_header = exp + ref_blk + ref_block_prefix + net_usage_words + max_cpu_usage_ms + delay_sec
    # Encode actions (1)
    action_account = tx_obj["actions"][0]["account"]
    action_name = tx_obj["actions"][0]["name"]
    tx_actions = uint2bin(1, 1) + string_to_binname(action_account) + string_to_binname(action_name)
    # Encode authorizations (1)
    auth_actor = tx_obj["actions"][0]["authorization"][0]["actor"]
    auth_perm = tx_obj["actions"][0]["authorization"][0]["permission"]
    tx_auths = uint2bin(1, 1) + string_to_binname(auth_actor) + string_to_binname(auth_perm)
    # Encode action data
    tx_data_rawhex = tx_obj["actions"][0]["data"]
    tx_data = encode_varuint(len(tx_data_rawhex) // 2) + bytes.fromhex(tx_data_rawhex)
    #        Header | Context actions | Actions : authorizations , Data | Extensions
    return tx_header + uint2bin(0, 1) + tx_actions + tx_auths + tx_data + uint2bin(0, 1)


def compute_sig_hash(tx_bin, chain_id):
    """Compute the sig digest, with empty context data"""
    chain_id_bin = bytes.fromhex(chain_id)
    return sha2(chain_id_bin + tx_bin + 32 * b"\0")


class eos_api:
    def __init__(self, network):
        self.network = network
        if self.network == "EOSio":
            self.url = "https://eos.greymass.com"
        elif self.network == "Jungle3":
            self.url = "https://api.jungle3.alohaeos.com"
        else:
            raise Exception("Not valid EOS network")

    def getData(self, endpoint, data=None):
        """POST data to the EOS RPC API endpoint"""
        if data is not None and isinstance(data, dict):
            data = json.dumps(data).encode("utf8")
        try:
            req = urllib.request.Request(
                f"{self.url}/v1/chain/{endpoint}",
                headers={"User-Agent": "Mozilla/5.0"},
                data=data,
            )
            webrsc = urllib.request.urlopen(req)
            return json.load(webrsc)
        except urllib.error.HTTPError as exc:
            strerr = exc.read()
            raise IOError(f"{exc.code}  :  {strerr.decode('utf8')}")
        except urllib.error.URLError as exc:
            raise IOError(exc)
        except Exception:
            raise IOError(f"Error while processing request:\n{self.url}/v1/chain/{endpoint}")

    def get_balance(self, account):
        data_bal = {"account": account, "code": "eosio.token", "symbol": "EOS"}
        return self.getData("get_currency_balance", data_bal)

    def get_account(self, address):
        accounts_info = self.getData("get_accounts_by_authorizers", {"keys": [address]})
        if len(accounts_info["accounts"]) > 0:
            return accounts_info["accounts"][0]["account_name"]
        return ""

    def abi_json_to_bin(self, code, action, args):
        abi_query = {"code": code, "action": action, "args": args}
        return self.getData("abi_json_to_bin", abi_query)

    def get_chain_lib_info(self):
        chain_info = self.getData("get_info")
        lib_info = self.get_block(chain_info["last_irreversible_block_num"])
        return chain_info, lib_info

    def get_block(self, block_num):
        return self.getData("get_block", {"block_num_or_id": block_num})

    def pushtx(self, txdata):
        return self.getData("push_transaction", txdata)


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
        self.datahash = b""
        self.trx = {}

    def getbalance(self):
        return self.api.get_balance(self.account)

    def getaccount(self, addr):
        return self.api.get_account(addr)

    def prepare(self, to_account, pay_value):
        bal_str = self.getbalance()
        balance = float(bal_str[0][:-4]) if len(bal_str) > 0 else 0.0
        if float(pay_value) > balance:
            raise Exception("Not enough fund for the tx")
        if isinstance(pay_value, (int, float)):
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
        data = self.api.abi_json_to_bin(payload["account"], payload["name"], args)
        payload["data"] = data["binargs"]
        self.trx = {"actions": [payload]}
        self.trx["expiration"] = near_future_iso_str(60)
        chain_info, lib_info = self.api.get_chain_lib_info()
        self.trx["ref_block_num"] = chain_info["last_irreversible_block_num"] & 0xFFFF
        self.trx["ref_block_prefix"] = lib_info["ref_block_prefix"]
        self.trx["max_net_usage_words"] = 0
        self.trx["max_cpu_usage_ms"] = 0
        self.trx["delay_sec"] = 0
        self.trx["context_free_actions"] = []
        self.datahash = compute_sig_hash(serialize_tx(self.trx), chain_info["chain_id"])
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
            "transaction": self.trx,
            "signatures": [signature_b58],
        }
        ret_tx = self.api.pushtx(final_tx)
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
        return None

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
