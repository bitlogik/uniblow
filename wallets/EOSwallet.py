#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW EOS wallet
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


import json
import re
import time
import urllib.request

from cryptolib.base58 import bin_to_base58_eos
from cryptolib.uintEncode import uint8, uint16, uint32, encode_varuint
from cryptolib.coins.eos import string_to_binname, expiration_string_epoch_int, near_future_iso_str
from cryptolib.cryptography import public_key_recover, compress_pubkey, sha2
from wallets.wallets_utils import NotEnoughTokens


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
    max_cpu_usage_ms = uint8(tx_obj["max_cpu_usage_ms"])
    delay_sec = encode_varuint(tx_obj["delay_sec"])
    tx_header = exp + ref_blk + ref_block_prefix + net_usage_words + max_cpu_usage_ms + delay_sec
    # Encode actions (1)
    action_account = tx_obj["actions"][0]["account"]
    action_name = tx_obj["actions"][0]["name"]
    tx_actions = uint8(1) + string_to_binname(action_account) + string_to_binname(action_name)
    # Encode authorizations (1)
    auth_actor = tx_obj["actions"][0]["authorization"][0]["actor"]
    auth_perm = tx_obj["actions"][0]["authorization"][0]["permission"]
    tx_auths = uint8(1) + string_to_binname(auth_actor) + string_to_binname(auth_perm)
    # Encode action data
    tx_data_rawhex = tx_obj["actions"][0]["data"]
    tx_data = encode_varuint(len(tx_data_rawhex) // 2) + bytes.fromhex(tx_data_rawhex)
    #        Header | Context actions | Actions : authorizations , Data | Extensions
    return tx_header + uint8(0) + tx_actions + tx_auths + tx_data + uint8(0)


def compute_sig_hash(tx_bin, chain_id):
    """Compute the sig digest, with empty context data"""
    chain_id_bin = bytes.fromhex(chain_id)
    return sha2(chain_id_bin + tx_bin + 32 * b"\0")


class eos_api:
    def __init__(self, network):
        self.network = network
        if self.network == "EOSio":
            self.url = "https://eos.greymass.com"
        elif self.network == "Jungle4":
            self.url = "https://api.jungle4.alohaeos.com"
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
    return eos_account


account_pattern = re.compile(r"^[a-z1-5\.]{11}[a-z1-5]$")

CPU_per_tx = 500
POWER_UP_PAYMENT = "0.0002"


class EOSwalletCore:
    def __init__(self, pubkey, network, api):
        self.pubkey = pubkey
        self.api = api
        self.address = compute_eos_address(compress_pubkey(pubkey))
        self.account = self.getaccount(self.address)
        self.network = network

    def getbalance(self):
        return self.api.get_balance(self.account)

    def getaccount(self, addr):
        try:
            return self.api.get_account(addr)
        except (IOError, OSError):
            return ""

    def getresources(self):
        """Return the CPU available"""
        account_info = self.api.getData("get_account", {"account_name": self.account})
        return account_info["cpu_limit"]["available"]

    def power_up(self, value):
        bal_str = self.getbalance()
        balance = float(bal_str[0][:-4]) if len(bal_str) > 0 else 0.0
        if (float(POWER_UP_PAYMENT) + value) > balance:
            raise NotEnoughTokens("Not enough fund for the tx and the powerup")
        args = {
            "payer": self.account,
            "receiver": self.account,
            "days": 1,
            "cpu_frac": 1000 * CPU_per_tx,
            "net_frac": 10000,
            "max_payment": f"{POWER_UP_PAYMENT} EOS",
        }
        payload = {
            "account": "eosio",
            "name": "powerup",
            "authorization": [
                {
                    "actor": self.account,
                    "permission": "active",
                }
            ],
        }
        data = self.api.abi_json_to_bin(payload["account"], payload["name"], args)
        payload["data"] = data["binargs"]
        ptrx = {"actions": [payload]}
        ptrx["expiration"] = near_future_iso_str(60)
        chain_info, lib_info = self.api.get_chain_lib_info()
        ptrx["ref_block_num"] = chain_info["last_irreversible_block_num"] & 0xFFFF
        ptrx["ref_block_prefix"] = lib_info["ref_block_prefix"]
        ptrx["max_net_usage_words"] = 0
        ptrx["max_cpu_usage_ms"] = 0
        ptrx["delay_sec"] = 0
        ptrx["context_free_actions"] = []
        pdatahash = compute_sig_hash(serialize_tx(ptrx), chain_info["chain_id"])
        return ptrx, pdatahash

    def finalize_powerup(self, tx, datahash, signature_der):
        # Signature decoding
        lenr = int(signature_der[3])
        lens = int(signature_der[5 + lenr])
        r = int.from_bytes(signature_der[4 : lenr + 4], "big")
        s = int.from_bytes(signature_der[lenr + 6 : lenr + 6 + lens], "big")
        # Parity recovery
        i = 31
        h = int.from_bytes(datahash, "big")
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
        final_ptx = {
            "compression": "none",
            "transaction": tx,
            "signatures": [signature_b58],
        }
        self.api.pushtx(final_ptx)

    def prepare(self, to_account, pay_value):
        bal_str = self.getbalance()
        balance = float(bal_str[0][:-4]) if len(bal_str) > 0 else 0.0
        if pay_value > balance or pay_value < 0:
            raise NotEnoughTokens("Not enough fund for the tx")
        if isinstance(pay_value, (int, float)):
            qty = "%.4f %s" % (pay_value, "EOS")
        else:
            raise Exception("pay_value must be int or float")
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
        trx = {"actions": [payload]}
        trx["expiration"] = near_future_iso_str(60)
        chain_info, lib_info = self.api.get_chain_lib_info()
        trx["ref_block_num"] = chain_info["last_irreversible_block_num"] & 0xFFFF
        trx["ref_block_prefix"] = lib_info["ref_block_prefix"]
        trx["max_net_usage_words"] = 0
        trx["max_cpu_usage_ms"] = 0
        trx["delay_sec"] = 0
        trx["context_free_actions"] = []
        datahash = compute_sig_hash(serialize_tx(trx), chain_info["chain_id"])
        return trx, datahash

    def send(self, tx, datahash, signature_der):
        # Signature decoding
        lenr = int(signature_der[3])
        lens = int(signature_der[5 + lenr])
        r = int.from_bytes(signature_der[4 : lenr + 4], "big")
        s = int.from_bytes(signature_der[lenr + 6 : lenr + 6 + lens], "big")
        # Parity recovery
        i = 31
        h = int.from_bytes(datahash, "big")
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
            "transaction": tx,
            "signatures": [signature_b58],
        }
        ret_tx = self.api.pushtx(final_tx)
        return "\nDONE, txID : " + ret_tx["transaction_id"]


# Only local key for now
class EOS_wallet:
    coin = "EOS"

    networks = [
        "EOSio",
        "Jungle4",
    ]

    wtypes = [
        "K1",
    ]

    derive_paths = [
        # mainnet
        [
            "m/44'/194'/{}'/0/{}",
        ],
        # testnet
        [
            "m/44'/1'/{}'/0/{}",
        ],
    ]

    def __init__(self, network, wtype, device):
        self.network = EOS_wallet.networks[network]
        self.key_type = EOS_wallet.wtypes[wtype]
        self.current_device = device
        pubkey = self.current_device.get_public_key()
        self.eos = EOSwalletCore(pubkey, self.network, eos_api(self.network))

    @classmethod
    def get_networks(cls):
        return cls.networks

    @classmethod
    def get_account_types(cls):
        return cls.wtypes

    @classmethod
    def get_path(cls, network_name, wtype, legacy):
        return cls.derive_paths[network_name][wtype]

    @classmethod
    def get_key_type(cls, wtype):
        # No list, it's all k1, r1 not still supported
        return "K1"

    def get_account(self):
        # Read account to fund the wallet
        return self.eos.account if self.eos.account else self.eos.address

    def get_balance(self):
        # Get balance in base integer unit
        if not self.eos.account:
            return "No pubkey found\n(not registered or offline)"
        bal_list = self.eos.getbalance()
        return bal_list[0] if len(bal_list) > 0 else f"0 {self.coin}"

    def check_address(self, addr_str):
        # Check if address is valid
        return testaddr(addr_str)

    def history(self):
        # Get history page
        if self.eos.account:
            if self.network == "EOSio":
                net = "eos"
            else:
                net = self.network.lower()
            return f"https://{net}.eosq.eosnation.io/account/{self.eos.account}"
        return None

    def transfer(self, amount, to_account, priority_fee, is_all=False):
        # Transfer x unit to an account
        if isinstance(amount, str) and amount[-4:] == " EOS":
            amount = amount[:-4]
        value = float(amount)

        # Check CPU available
        cpu_avail = self.eos.getresources()
        if cpu_avail < CPU_per_tx:
            # Need to power up
            pu_tx, ptxhash = self.eos.power_up(value)
            # sign until R|S = 2x32
            len_r = 0
            len_s = 0
            while len_r != 32 or len_s != 32:
                if self.current_device.on_device_check:
                    tx_signature = self.current_device.sign(pu_tx)
                else:
                    tx_signature = self.current_device.sign(ptxhash)
                if self.current_device.provide_parity:
                    raise NotImplementedError(
                        "Device with provide_parity attribute was not implemented in this Tezos wallet."
                    )
                len_r = int(tx_signature[3])
                len_s = int(tx_signature[5 + len_r])
            # Finalize powerup tx and send it
            self.eos.finalize_powerup(pu_tx, ptxhash, tx_signature)
            if is_all:
                value -= float(POWER_UP_PAYMENT)
            time.sleep(3)

        # Perform the transfer transaction
        atx, hash_to_sign = self.eos.prepare(to_account, value)
        # sign until R|S = 2x32
        len_r = 0
        len_s = 0
        while len_r != 32 or len_s != 32:
            if self.current_device.on_device_check:
                tx_signature = self.current_device.sign(atx)
            else:
                tx_signature = self.current_device.sign(hash_to_sign)
            if self.current_device.provide_parity:
                raise NotImplementedError(
                    "Device with provide_parity attribute was not implemented in this Tezos wallet."
                )
            len_r = int(tx_signature[3])
            len_s = int(tx_signature[5 + len_r])
        return self.eos.send(atx, hash_to_sign, tx_signature)

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.get_balance()
        return self.transfer(all_amount, to_account, fee_priority, is_all=True)
