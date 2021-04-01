#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Tezos wallet with with Giganode API REST
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


import json
import ecdsa
import time
import urllib.parse
import urllib.request
from .lib import cryptos

try:
    import nacl.signing
    import nacl.encoding
    import nacl.hash
except:
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
        # https://mainnet-tezos.giganode.io/chains/main/blocks/head
        #         mainnet
        self.network = network
        self.url = f"https://{network}-tezos.giganode.io"
        self.chainID = self.getData("/chains/main/chain_id")
        self.protocol = self.getData(f"{RPC_api.BASE_BLOCK_URL}/header/protocol_data")["protocol"]

    def getData(self, method, params=[]):
        full_url = self.url + method
        try:
            if params == []:
                data = None
            else:
                data = json.dumps(params).encode("utf-8")
            print("-> Request :")
            print(method)
            if data:
                print("with data :", data)
            req = urllib.request.Request(
                full_url,
                headers={"User-Agent": "Uniblow/1", "Content-Type": "application/json"},
                data=data,
            )
            webrsp = urllib.request.urlopen(req, timeout=6)
            # return json.load(webrsp)
            resp = json.load(webrsp)
            print("<- Response :")
            print(resp)
            return resp
        except Exception as exc:
            print(exc.read())
            raise IOError("Error while processing request:\n%s" % (full_url + " : " + str(data)))

    def checkapiresp(self):
        if "error" in self.jsres:
            print(" !! ERROR :")
            raise Exception(self.jsres["error"])
        if "errors" in self.jsres:
            print(" !! ERRORS :")
            raise Exception(self.jsres["errors"])

    def get_balance(self, addr):
        balraw = self.getData(f"{RPC_api.BASE_BLOCK_URL}/context/contracts/{addr}/balance")
        balance = int(balraw)
        return balance

    def simulate_tx(self, op_tx):
        return self.getData(f"{RPC_api.BASE_BLOCK_URL}/helpers/scripts/run_operation", op_tx)

    def preapply_tx(self, op_tx):
        return self.getData(f"{RPC_api.BASE_BLOCK_URL}/helpers/preapply/operations", op_tx)

    def pushtx(self, txhex):
        return self.getData(f"/injection/operation?chain=main", txhex) # tx hex
        # return self.getData(f"{RPC_api.BASE_BLOCK_URL}/helpers/preapply/operations", txhex) # ?

    def get_tx_num(self, addr):
        return self.getData(f"{RPC_api.BASE_BLOCK_URL}/context/contracts/{addr}/counter")

    def get_serialtx(self, dataobj):
        # forge operation
        return self.getData(f"{RPC_api.BASE_BLOCK_URL}/helpers/forge/operations", dataobj)

    def get_head_block(self):
        return self.getData(f"{RPC_api.BASE_BLOCK_URL}/hash")


def testaddr(xtz_addr):
    # Safe reading of the address format
    # very basic check, ToDo decode base58 checksum
    if not xtz_addr.startswith("tz"):
        return False
    if len(xtz_addr) != 36:
        return False
    return True


class XTZwalletCore:
    
    SIG256K1_PREFIX = bytes([13, 115, 101, 19, 63])
    ADDRESS_HEADER = b"\x06\xa1\xa1"  # tz2
    PUBKEY_HEADER = bytes([3, 254, 226, 86])

    def __init__(self, pubkey, network, api):
        self.pubkey = pubkey
        self.Qpub = cryptos.decode_pubkey(pubkey)
        self.pubkey_b58 = cryptos.headbin_to_b58check(bytes.fromhex(self.pubkey), XTZwalletCore.PUBKEY_HEADER)
        pubkey_hash = blake2b(bytes.fromhex(pubkey), 20)
        self.address = cryptos.headbin_to_b58check(pubkey_hash, XTZwalletCore.ADDRESS_HEADER)
        self.api = api
        self.network = network

    def getbalance(self):
        return self.api.get_balance(self.address)

    def getnonce(self):
        return self.api.get_tx_num(self.address)

    def getheadblock(self):
        return self.api.get_head_block()

    def getserialtx(self, dataobj):
        return self.api.get_serialtx(dataobj)

    def getchainid(self):
        return self.api.chainID

    def getprotocol(self):
        return self.api.protocol

    def prepare(self, toaddr, paymentvalue, fee, glimit):
        balance = self.getbalance()
        maxspendable = balance - int(fee)
        if paymentvalue > maxspendable or paymentvalue < 0:
            raise Exception("Not enough fund for the tx")
        self.nonce = int(self.getnonce())
        self.fee = fee
        self.glimit = glimit
        self.value = str(int(paymentvalue))
        curr_branch = self.getheadblock()
        print(curr_branch)
        # reveal needed ? -> /context/contracts/{address}/manager_key key:
        tx_data = {
            "branch": curr_branch,
            "contents": [
                {
                    "kind": "reveal",
                    "source": self.address,
                    "fee": self.fee,
                    "counter": str(self.nonce+1),
                    "gas_limit": "100000",
                    "storage_limit": "60000",
                    "public_key": self.pubkey_b58,
                },
                {
                    "kind": "transaction",
                    "source": self.address,
                    "fee": self.fee,
                    "counter": str(self.nonce+2),
                    "gas_limit": self.glimit,
                    "storage_limit": "60000",
                    "amount": self.value,
                    "destination": toaddr,
                },
            ],
        }
        self.tx = tx_data
        self.signing_tx_hex = "03" + self.getserialtx(tx_data)
        print(self.signing_tx_hex)
        self.datahash = blake2b(bytes.fromhex(self.signing_tx_hex))
        return self.datahash

    def send(self, signature_der):
        # Signature decoding
        lenr = int(signature_der[3])
        lens = int(signature_der[5 + lenr])
        r = int.from_bytes(signature_der[4 : lenr + 4], "big")
        s = int.from_bytes(signature_der[lenr + 6 : lenr + 6 + lens], "big")
        # # Parity recovery
        # Q = ecdsa.keys.VerifyingKey.from_public_key_recovery_with_digest(
        # signature_der, self.datahash, ecdsa.curves.SECP256k1, sigdecode=ecdsa.util.sigdecode_der
        # )[1]
        # if Q.to_string("uncompressed") == cryptos.encode_pubkey(self.Qpub, "bin"):
        # i = 36
        # else:
        # i = 35
        # Signature encoding
        # v = int2bytearray(2 * self.chainID + i)
        # r = int2bytearray(r)
        # s = int2bytearray(s)
        # signature_header = bytes([13, 115, 101, 19, 63])
        # sig_b58 = cryptos.headbin_to_b58check(r+s, signature_header)
        # print(sig_b58)
        # 256k1 sig prefix : [13, 115, 101, 19, 63]
        rs_bin = signature_der[4 : lenr + 4][-32:] + signature_der[lenr + 6 : lenr + 6 + lens][-32:]
        sig_b58 = cryptos.headbin_to_b58check(rs_bin, XTZwalletCore.SIG256K1_PREFIX)
        
        self.tx["signature"] = sig_b58
        op = {"operation":self.tx}
        op["chain_id"] = self.getchainid()
        
        print(self.tx)
        print(self.api.simulate_tx(op))
        print("-- now pre apply --")
        self.tx["protocol"] = self.getprotocol()
        print(self.api.preapply_tx([self.tx]))
        
        txhex = self.signing_tx_hex + "%064x" % r + "%064x" % s
        print(txhex)
        return "\nDONE, txID : " + self.api.pushtx(txhex)
        # server return "Unknown branch (BKjdF8tM7TEv), cannot inject the operation."

# https://www.ocamlpro.com/2018/11/21/an-introduction-to-tezos-rpcs-signing-operations/
# https://github.com/goat-systems/go-tezos/blob/800cc714fad7313e92a5068407c23e0e397f5323/keys/secp256k1.go#L71
# https://gitlab.com/tezos/tezos/-/blob/master/docs/api/edo-openapi.json
# https://gitlab.com/tezos/tezos/-/blob/v8-release/docs/api/rpc-openapi.json
# https://tezos.gitlab.io/shell/rpc.html

XTZ_units = 10 ** 6

# Only local key for now
class XTZ_wallet:

    networks = [
        "mainnet",
        "testnet",
    ]

    wtypes = [
        "tz2",
    ]

    GAZ_LIMIT_SIMPLE_TX = "2000"

    def __init__(self, network, wtype, device):
        self.network = XTZ_wallet.networks[network].lower()
        self.current_device = device
        pubkey = self.current_device.get_public_key()
        self.xtz = XTZwalletCore(pubkey, self.network, RPC_api(self.network))

    @classmethod
    def get_networks(cls):
        return cls.networks

    @classmethod
    def get_account_types(cls):
        return cls.wtypes

    def get_account(self):
        # Read address to fund the wallet
        return self.xtz.address

    def get_balance(self):
        # Get balance in base integer unit
        return str(self.xtz.getbalance() / XTZ_units) + " XTZ"

    def check_address(self, addr_str):
        # Check if address is valid
        # Quick check with regex, doesnt compute checksum
        return testaddr(addr_str)

    def history(self):
        # Get history as tx list
        raise "Not yet implemented"

    def raw_tx(self, amount, fee, ethgazlimit, account):
        hash_to_sign = self.xtz.prepare(account, amount, fee, ethgazlimit)
        tx_signature = self.current_device.sign(hash_to_sign)
        return self.xtz.send(tx_signature)

    def transfer(self, amount, to_account, priority_fee):
        # Transfer x unit to an account, pay
        ethgazlimit = XTZ_wallet.GAZ_LIMIT_SIMPLE_TX
        ethgazprice = "50000"
        return self.raw_tx(int(amount * XTZ_units), ethgazprice, ethgazlimit, to_account)

    def transfer_inclfee(self, amount, to_account, fee_priority):
        # Transfer the amount in base unit minus fee, like the receiver paying the fee
        gazlimit = XTZ_wallet.GAZ_LIMIT_SIMPLE_TX
        if to_account.startswith("0x"):
            to_account = to_account[2:]
        gazprice = self.xtz.api.get_fee(fee_priority)
        fee = gazlimit * gazprice
        return self.raw_tx(amount - int(fee * 10 ** 9), gazprice, gazlimit, to_account)

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.xtz.getbalance()
        return self.transfer_inclfee(all_amount, to_account, fee_priority)
