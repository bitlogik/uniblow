#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Tezos wallet with with SmartPy API REST
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
import urllib.parse
import urllib.request

from cryptolib.base58 import encode_base58, decode_base58
from cryptolib.cryptography import compress_pubkey
from wallets.wallets_utils import shift_10, NotEnoughTokens

try:
    import nacl.signing
    import nacl.encoding
    import nacl.hash
except Exception:
    raise Exception("Requires PyNaCl : pip3 install pynacl")


def int2bytearray(i):
    barr = (i).to_bytes(32, byteorder="big")
    while barr[0] == 0 and len(barr) > 1:
        barr = barr[1:]
    return bytearray(barr)


def blake2b(data, output_sz=32):
    return nacl.hash.blake2b(data, output_sz, encoder=nacl.encoding.RawEncoder)


class RPC_api:

    BASE_BLOCK_URL = "/chains/main/blocks/head"

    def __init__(self, network):
        self.url = f"https://{network}.smartpy.io"
        self.chainID = self.getData("/chains/main/chain_id")
        self.protocol = self.getData(f"{RPC_api.BASE_BLOCK_URL}/protocols")["protocol"]

    def getData(self, method, params=[]):
        full_url = self.url + method
        try:
            if params == []:
                data = None
            else:
                data = json.dumps(params).encode("utf-8")
            req = urllib.request.Request(
                full_url,
                headers={"User-Agent": "Uniblow/1", "Content-Type": "application/json"},
                data=data,
            )
            webrsp = urllib.request.urlopen(req, timeout=6)
            resp = json.load(webrsp)
            return resp
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf8")
            try:
                err = json.loads(err)
            except ValueError:
                pass
            if isinstance(err, str):
                raise IOError(f"Error code {e.code}\n{err}")
            if err and err != [] and len(err) > 1 and err[0].get(key):
                if "msg" in err[0]:
                    key = "msg"
                elif "id" in err[0]:
                    key = "id"
                else:
                    raise IOError(f"Error code {e.code}\n{err}")
                raise IOError(f"Error in the node processing :\n{err[0][key]}")
        except urllib.error.URLError as e:
            raise IOError(e)
        except Exception:
            raise IOError(f"Error while processing request :\n{full_url}:{str(data)}")

    def get_balance(self, addr):
        balraw = self.getData(f"{RPC_api.BASE_BLOCK_URL}/context/contracts/{addr}/balance")
        balance = int(balraw)
        return balance

    def simulate_tx(self, op_tx):
        return self.getData(f"{RPC_api.BASE_BLOCK_URL}/helpers/scripts/run_operation", op_tx)

    def preapply_tx(self, op_tx):
        return self.getData(f"{RPC_api.BASE_BLOCK_URL}/helpers/preapply/operations", op_tx)

    def pushtx(self, txhex):
        return self.getData("/injection/operation?chain=main", txhex)

    def get_counter(self, addr):
        return self.getData(f"{RPC_api.BASE_BLOCK_URL}/context/contracts/{addr}/counter")

    def get_serialtx(self, dataobj):
        # forge operation
        return self.getData(f"{RPC_api.BASE_BLOCK_URL}/helpers/forge/operations", dataobj)

    def get_head_block(self):
        return self.getData(f"{RPC_api.BASE_BLOCK_URL}/hash")

    def get_contract_key(self, contract_addr):
        return self.getData(
            f"{RPC_api.BASE_BLOCK_URL}/context/contracts/{contract_addr}/manager_key"
        )


def testaddr(xtz_addr):
    # Safe readings of the address format
    if not xtz_addr.startswith("tz"):
        return False
    if len(xtz_addr) != 36:
        return False
    if xtz_addr[2] not in ["1", "2", "3"]:
        return False
    try:
        decode_base58(xtz_addr)
    except ValueError:
        return False
    return True


class XTZwalletCore:

    key_types = [
        "K1",
        "ED",
    ]

    SIGED_HEADER = bytes([9, 245, 205, 134, 18])  # edsig
    ADDRESS_ED_HEADER = bytes([6, 161, 159])  # tz1
    PUBKEY_ED_HEADER = bytes([13, 15, 37, 217])  # edpk
    SIGK1_HEADER = bytes([13, 115, 101, 19, 63])  # spsig
    ADDRESS_K1_HEADER = bytes([6, 161, 161])  # tz2
    PUBKEY_K1_HEADER = bytes([3, 254, 226, 86])  # sppk
    # SIGR1_HEADER = bytes([54, 240, 44, 52])  # p2sig
    # ADDRESS_R1_HEADER = bytes([6, 161, 164])  # tz3
    # PUBKEY_R1_HEADER = bytes([3, 178, 139, 127])  # p2pk

    def __init__(self, pubkey, network, wtype, api):
        if wtype == 1:
            # tz1 Ed
            self.SIG_HEADER = XTZwalletCore.SIGED_HEADER
            PUBKEY_HEADER = XTZwalletCore.PUBKEY_ED_HEADER
            ADDRESS_HEADER = XTZwalletCore.ADDRESS_ED_HEADER
            self.pubkey = pubkey
        else:
            # tz2 k1
            self.SIG_HEADER = XTZwalletCore.SIGK1_HEADER
            PUBKEY_HEADER = XTZwalletCore.PUBKEY_K1_HEADER
            ADDRESS_HEADER = XTZwalletCore.ADDRESS_K1_HEADER
            self.pubkey = compress_pubkey(pubkey)
        self.key_type = XTZwalletCore.key_types[wtype]
        self.pubkey_b58 = encode_base58(PUBKEY_HEADER + self.pubkey)
        pubkey_hashed = blake2b(self.pubkey, 20)
        self.address = encode_base58(ADDRESS_HEADER + pubkey_hashed)
        self.api = api
        self.network = network

    def getbalance(self):
        return self.api.get_balance(self.address)

    def getnonce(self):
        return self.api.get_counter(self.address)

    def getpublickey(self):
        # is revealed ?
        pkr = self.api.get_contract_key(self.address)
        if isinstance(pkr, str) and self.key_type == "K1" and pkr.startswith("sppk"):
            return pkr
        if isinstance(pkr, str) and self.key_type == "ED" and pkr.startswith("edpk"):
            return pkr
        if pkr and "key" in pkr:
            return pkr["key"]
        return ""

    def check_operation(self, run_result):
        if type(run_result) is list:
            run_result = run_result[0]
        for op in run_result["contents"]:
            if op["metadata"]["operation_result"]["status"] != "applied":
                return op["metadata"]["operation_result"]
        return {}

    def prepare(self, toaddr, paymentvalue, fee, glimit):
        balance = self.getbalance()
        key_revealed = self.getpublickey()
        self.fee = str(fee)
        if not key_revealed:
            fee = 2 * fee
        maxspendable = balance - fee
        if paymentvalue > maxspendable or paymentvalue < 0:
            raise NotEnoughTokens("Not enough fund for the tx")
        self.nonce = int(self.getnonce())
        self.glimit = glimit
        self.value = str(int(paymentvalue))
        curr_branch = self.api.get_head_block()
        self.operation = {
            "operation": {
                "branch": curr_branch,
                "contents": [],
            },
            "chain_id": self.api.chainID,
        }
        if not key_revealed:  # need reveal
            self.nonce += 1
            self.operation["operation"]["contents"].append(
                {
                    "kind": "reveal",
                    "source": self.address,
                    "fee": self.fee,
                    "counter": str(self.nonce),
                    "gas_limit": "1000",
                    "storage_limit": "0",
                    "public_key": self.pubkey_b58,
                }
            )
        self.operation["operation"]["contents"].append(
            {
                "kind": "transaction",
                "source": self.address,
                "fee": self.fee,
                "counter": str(self.nonce + 1),
                "gas_limit": self.glimit,
                "storage_limit": "500",
                "amount": self.value,
                "destination": toaddr,
            }
        )
        self.signing_tx_hex = self.api.get_serialtx(self.operation["operation"])
        self.datahash = blake2b(bytes.fromhex("03" + self.signing_tx_hex))
        return self.datahash

    def send(self, signature_der):
        # Signature decoding
        if self.key_type == "K1":
            lenr = int(signature_der[3])
            lens = int(signature_der[5 + lenr])
            r = int.from_bytes(signature_der[4 : lenr + 4], "big")
            s = int.from_bytes(signature_der[lenr + 6 : lenr + 6 + lens], "big")
            rs_bin = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        else:
            r = int.from_bytes(signature_der[:32], "big")
            s = int.from_bytes(signature_der[32:], "big")
        rs_bin = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        sig_b58 = encode_base58(self.SIG_HEADER + rs_bin)
        self.operation["operation"]["signature"] = sig_b58

        # Simulate tx
        simu_result = self.api.simulate_tx(self.operation)
        checked_simu = self.check_operation(simu_result)
        if checked_simu:
            raise Exception(str(checked_simu))
        self.operation["operation"]["protocol"] = self.api.protocol
        # Full test (preapply) tx
        apply_result = self.api.preapply_tx([self.operation["operation"]])
        checked_apply = self.check_operation(apply_result)
        if checked_apply:
            raise Exception(str(checked_apply))

        txhex = self.signing_tx_hex + "%064x" % r + "%064x" % s
        return "\nDONE, txID : " + self.api.pushtx(txhex)


XTZ_units = 6


class XTZ_wallet:

    coin = "XTZ"

    networks = [
        "Mainnet",
        "HangzhouNet",
        "IthacaNet",
    ]

    wtypes = [
        "tz2",
        "tz1",
    ]

    derive_paths = [
        # mainnet
        [
            "m/44'/1729'/{}'/0/{}",
            "m/44'/1729'/{}'/{}",
        ],
        # testnet
        [
            "m/44'/1'/{}'/0/{}",
            "m/44'/1'/{}'/{}",
        ],
        [
            "m/44'/1'/{}'/0/{}",
            "m/44'/1'/{}'/{}",
        ],
    ]

    OPERATION_FEE = 1290
    GAZ_LIMIT_SIMPLE_TX = "10200"

    def __init__(self, network, wtype, device):
        self.network = XTZ_wallet.networks[network].lower()
        self.current_device = device
        pubkey = self.current_device.get_public_key()
        self.xtz = XTZwalletCore(pubkey, self.network, wtype, RPC_api(self.network))

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
        return XTZwalletCore.key_types[wtype]

    def get_account(self):
        # Read address to fund the wallet
        return self.xtz.address

    def get_balance(self):
        # Get balance in base integer unit
        return f"{self.xtz.getbalance() / (10 ** XTZ_units)} {self.coin}"

    def check_address(self, addr_str):
        # Check if address is valid
        return testaddr(addr_str)

    def history(self):
        # Get history page
        if self.network == "mainnet":
            XTZ_EXPLORER_URL = f"https://tzstats.com/{self.xtz.address}#transfers"
        else:  # Granada[Net] and Hangzhou[Net]
            XTZ_EXPLORER_URL = (
                f"https://{self.network[:-3]}.tzstats.com/{self.xtz.address}#transfers"
            )
        return XTZ_EXPLORER_URL

    def raw_tx(self, amount, fee, gazlimit, account):
        hash_to_sign = self.xtz.prepare(account, amount, fee, gazlimit)
        # For Ed, the signed message is the hash also
        tx_signature = self.current_device.sign(hash_to_sign)
        return self.xtz.send(tx_signature)

    def transfer(self, amount, to_account, priority_fee):
        # Transfer x unit to an account, pay
        return self.raw_tx(
            shift_10(amount, XTZ_units),
            XTZ_wallet.OPERATION_FEE,
            XTZ_wallet.GAZ_LIMIT_SIMPLE_TX,
            to_account,
        )

    def transfer_inclfee(self, amount, to_account, fee_priority):
        # Transfer the amount in base unit minus fee, like the receiver paying the fee
        fee = XTZ_wallet.OPERATION_FEE
        if not self.xtz.getpublickey():
            # if not revealed
            fee += XTZ_wallet.OPERATION_FEE
        return self.raw_tx(
            amount - fee,
            XTZ_wallet.OPERATION_FEE,
            XTZ_wallet.GAZ_LIMIT_SIMPLE_TX,
            to_account,
        )

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.xtz.getbalance()
        return self.transfer_inclfee(all_amount, to_account, fee_priority)
