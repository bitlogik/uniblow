#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW DOGE wallet with electra API REST
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
import re

import cryptolib.coins
from cryptolib.base58 import decode_base58
from wallets.wallets_utils import shift_10, NotEnoughTokens


class sochain_api:
    def __init__(self, network):
        self.url = "https://sochain.com/api/v2/"
        if network == "mainnet":
            self.coin = "DOGE"
        elif network == "testnet":
            self.coin = "DOGETEST"
        else:
            raise Exception("Unknown DOGE network name")
        self.jsres = []

    def getData(self, command, param, data=None):
        try:
            url_req = f"{self.url}{command}/{self.coin}"
            if param:
                url_req += f"/{param}"
            req = urllib.request.Request(
                url_req,
                headers={"User-Agent": "Mozilla/5.0"},
                data=data,
            )
            self.webrsc = urllib.request.urlopen(req)
            brep = self.webrsc.read()
            if len(brep) == 64 and brep[0] != ord("{"):
                brep = b'{"txid":"' + brep + b'"}'
            self.jsres = json.loads(brep)
        except urllib.error.HTTPError as e:
            strerr = e.read()
            raise IOError(f"{e.code}  :  {strerr.decode('utf8')}")
        except urllib.error.URLError as e:
            raise IOError(e)
        except Exception:
            raise IOError(f"Error while processing request:\n{self.url}{command}/{param}")

    def checkapiresp(self):
        if ("status" not in self.jsres) or self.jsres["status"] != "success":
            print(" !! ERROR :")
            raise Exception("Error decoding the API endpoint")

    def getutxos(self, addr, nconf):  # nconf 0 or 1
        # limited to 100 utxos
        self.getData("get_tx_unspent", addr)
        self.checkapiresp()
        addrutxos = self.getKey("data/txs")
        selutxos = []
        # translate inputs from sochain to pydogecoinlib
        for utxo in addrutxos:
            selutxos.append(
                {
                    "value": shift_10(utxo["value"], DOGE_units),
                    "output": utxo["txid"] + ":" + str(utxo["output_no"]),
                }
            )
        return selutxos

    def pushtx(self, txhex):
        self.getData("send_tx", "", data=b"tx_hex=" + txhex.encode("ascii"))
        self.checkapiresp()
        return self.getKey("data/txid")

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

    def get_fee(self, priority):
        return int(10 ** DOGE_units)


def testaddr(doge_addr, is_testnet):
    # Safe tests of the address format
    checked = False
    addr_head = "D"
    addr_head_alt = "D"
    mult_head = "9"
    mult_head_alt = "A"
    if is_testnet:
        addr_head = "n"
        addr_head_alt = "m"
        mult_head = "2"
        mult_head_alt = "2"
    if doge_addr.startswith(addr_head) or doge_addr.startswith(addr_head_alt):
        checked = re.match("^[Dnm][a-km-zA-HJ-NP-Z1-9]{25,34}$", doge_addr) is not None
    elif doge_addr.startswith(mult_head) or doge_addr.startswith(mult_head_alt):
        checked = re.match("^[9A2][a-km-zA-HJ-NP-Z1-9]{25,34}$", doge_addr) is not None
    else:
        return False
    try:
        if checked:
            decode_base58(doge_addr)
    except ValueError:
        return False
    return checked


class DOGEwalletCore:
    def __init__(self, pubkey, network_type, segwit_option, api):
        self.testnet = False
        if network_type == "testnet":
            self.testnet = True
        self.segwit = segwit_option
        # pubkey is hex compressed
        self.pubkey = pubkey
        if self.segwit == 0:
            self.address = cryptolib.coins.dogecoin.Doge(testnet=self.testnet).pubtoaddr(
                self.pubkey
            )
        else:
            raise Exception("Not valid segwit option")
        self.api = api

    def getutxos(self, nconf=0):
        return self.api.getutxos(self.address, nconf)

    def getbalance(self):
        utxos = self.getutxos()
        return self.balance_fmutxos(utxos)

    def prepare(self, toaddr, paymentvalue, fee):
        utxos = self.getutxos()
        balance = self.balance_fmutxos(utxos)
        maxspendable = balance - fee
        if paymentvalue > maxspendable or paymentvalue < 0:
            raise NotEnoughTokens("Not enough fund for the tx")
        inputs = self.selectutxos(paymentvalue + fee, utxos)
        invalue = self.balance_fmutxos(inputs)
        changevalue = invalue - paymentvalue - fee
        outs = [{"value": paymentvalue, "address": toaddr}]
        if changevalue > 0:
            outs.append({"value": changevalue, "address": self.address})
        self.tx = cryptolib.coins.dogecoin.Doge(testnet=self.testnet).mktx(inputs, outs)
        script = cryptolib.coins.mk_pubkey_script(self.address)

        # Finish tx
        # Sign each input
        self.leninputs = len(inputs)
        datahashes = []
        for i in range(self.leninputs):
            signing_tx = cryptolib.coins.signature_form(
                self.tx, i, script, cryptolib.coins.SIGHASH_ALL
            )
            datahashes.append(cryptolib.coins.bin_txhash(signing_tx, cryptolib.coins.SIGHASH_ALL))
        return datahashes

    def send(self, signatures):
        for i in range(self.leninputs):
            signature_der_hex = signatures[i].hex() + "01"
            self.tx["ins"][i]["script"] = cryptolib.coins.serialize_script(
                [signature_der_hex, self.pubkey]
            )
        txhex = cryptolib.coins.serialize(self.tx)
        return "\nDONE, txID : " + self.api.pushtx(txhex)

    def balance_fmutxos(self, utxos):
        bal = 0
        for utxo in utxos:
            bal += utxo["value"]
        return bal

    def selectutxos(self, amount, utxos):
        sorted_utxos = sorted(utxos, key=lambda x: x["value"], reverse=True)
        sel_utxos = []
        for sutxo in sorted_utxos:
            amount -= sutxo["value"]
            sel_utxos.append(sutxo)
            if 0 >= amount:
                break
        if 0 >= amount:
            return sel_utxos
        else:
            raise NotEnoughTokens("Not enough utxos values for the tx")


DOGE_units = 8


class DOGE_wallet:

    coin = "DOGE"

    networks = [
        "mainnet",
        "testnet",
    ]

    wtypes = [
        "Standard",
    ]

    derive_paths = [
        # mainnet
        [
            "m/44'/3'/{}'/0/{}",
        ],
        # testnet
        [
            "m/44'/1'/{}'/0/{}",
        ],
    ]

    def __init__(self, network, wtype, device):
        self.current_device = device
        pubkey = self.current_device.get_public_key()
        network_name = self.networks[network]
        self.doge = DOGEwalletCore(pubkey, network_name, wtype, sochain_api(network_name))

    @classmethod
    def get_networks(cls):
        return cls.networks

    @classmethod
    def get_account_types(cls):
        return cls.wtypes

    @classmethod
    def get_path(cls, network_name, wtype, legacy):
        # First path
        # To be changed to the first one available, needs scanning
        return cls.derive_paths[network_name][wtype]

    @classmethod
    def get_key_type(cls, wtype):
        # No list, it's all k1
        return "K1"

    def get_account(self):
        # Read address to fund the wallet
        return self.doge.address

    def get_balance(self):
        # Get balance in base integer unit
        return f"{self.doge.getbalance() / (10 ** DOGE_units)} {self.coin}"

    def check_address(self, addr_str):
        # Check if address is valid
        return testaddr(addr_str, self.doge.testnet)

    def history(self):
        # Get history page
        if self.doge.testnet:
            DOGE_EXPLORER_URL = f"https://sochain.com/address/DOGETEST/{self.doge.address}"
        else:
            DOGE_EXPLORER_URL = f"https://sochain.com/address/DOGE/{self.doge.address}"
        return DOGE_EXPLORER_URL

    def raw_tx(self, amount, fee, to_account):
        hashes_to_sign = self.doge.prepare(to_account, amount, fee)
        tx_signatures = []
        for msg in hashes_to_sign:
            asig = self.current_device.sign(msg)
            tx_signatures.append(asig)
        return self.doge.send(tx_signatures)

    def assess_fee(self, fee_priority):
        # Get fee assesment for a wallet tx
        fee = self.doge.api.get_fee(fee_priority)
        return fee

    def transfer(self, amount, to_account, fee_priority):
        # Transfer x base unit to an account, pay
        fee = self.assess_fee(fee_priority)
        return self.raw_tx(shift_10(amount, DOGE_units), fee, to_account)

    def transfer_inclfee(self, amount, to_account, fee_priority):
        # Transfer the amount in base unit minus fee, like the receiver paying the fee
        fee = self.assess_fee(fee_priority)
        return self.raw_tx(amount - fee, fee, to_account)

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.doge.getbalance()
        return self.transfer_inclfee(all_amount, to_account, fee_priority)
