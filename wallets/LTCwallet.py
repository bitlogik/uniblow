#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW LTC wallet with electra API REST
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
import urllib.parse
import urllib.request
import re
from .lib import cryptos

# import hashlib


class sochain_api:
    def __init__(self, network):
        self.url = "https://sochain.com/api/v2/"
        if network == "mainnet":
            self.coin = "LTC"
        elif network == "testnet":
            self.coin = "LTCTEST"
        else:
            raise Exception("Unknown LTC network name")
        self.jsres = []

    def getData(self, command, param, paramsurl={}, data=None):
        parameters = {key: value for key, value in paramsurl.items()}
        params_enc = urllib.parse.urlencode(parameters)
        try:
            req = urllib.request.Request(
                f"{self.url}{command}/{self.coin}/{param}?{params_enc}",
                headers={"User-Agent": "Mozilla/5.0"},
                data=data,
            )
            self.webrsc = urllib.request.urlopen(req)
            brep = self.webrsc.read()
            if len(brep) == 64 and brep[0] != ord("{"):
                brep = b'{"txid":"' + brep + b'"}'
            self.jsres = json.loads(brep)
        except urllib.error.URLError as e:
            raise IOError(e)
        except Exception:
            raise IOError(
                "Error while processing request:\n%s" % (self.url + command + "?" + params_enc)
            )

    def checkapiresp(self):
        if (not "status" in self.jsres) or self.jsres["status"] != "success":
            print(" !! ERROR :")
            raise Exception("Error decoding the API endpoint")

    def getutxos(self, addr, nconf):  # nconf 0 or 1
        # limited to 100 utxos
        self.getData("get_tx_unspent", addr)
        self.checkapiresp()
        addrutxos = self.getKey("data/txs")
        selutxos = []
        # translate inputs from sochain to pylitecoinlib
        for utxo in addrutxos:
            selutxos.append(
                {
                    "value": int(float(utxo["value"]) * LTC_units),
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
            except:
                out = []
        return out

    def get_fee(self, priority):
        return 1
        # self.getData("fee-estimates")


def testaddr(ltc_addr):
    # Safe test of the address format
    if ltc_addr.startswith("L") or ltc_addr.startswith("M"):
        return re.match("^[LM][a-km-zA-HJ-NP-Z1-9]{25,34}$", ltc_addr) is not None
    elif ltc_addr.startswith("m") or ltc_addr.startswith("Q"):
        return re.match("^[mQ][a-km-zA-HJ-NP-Z1-9]{25,34}$", ltc_addr) is not None
    elif ltc_addr.startswith("ltc") or ltc_addr.startswith("ltc"):
        return re.match("^(ltc|ltc)[01][ac-hj-np-z02-9]{8,87}$", ltc_addr) is not None
    else:
        return False
    return False


class LTCwalletCore:
    def __init__(self, pubkey, network_type, segwit_option, api):
        self.testnet = False
        if network_type == "testnet":
            self.testnet = True
        self.segwit = segwit_option
        # pubkey is hex compressed
        self.pubkey = pubkey
        # PKH = CryptnoxPy.bin_hash160(bytes.fromhex(pubkey))
        if self.segwit == 0:
            self.address = cryptos.coins.litecoin.Litecoin(testnet=self.testnet).pubtoaddr(
                self.pubkey
            )
        elif self.segwit == 1:
            self.address = cryptos.coins.litecoin.Litecoin(testnet=self.testnet).pubtop2w(
                self.pubkey
            )
        elif self.segwit == 2:
            self.address = cryptos.coins.litecoin.Litecoin(testnet=self.testnet).pubtosegwit(
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
        if paymentvalue > maxspendable:
            raise Exception("Not enough fund for the tx")
        inputs = self.selectutxos(paymentvalue + fee, utxos)
        invalue = self.balance_fmutxos(inputs)
        changevalue = invalue - paymentvalue - fee
        outs = [{"value": paymentvalue, "address": toaddr}]
        if toaddr.startswith("ltc0") or toaddr.startswith("tltc0"):
            outs[0]["segwit"] = True
        if toaddr.startswith("ltc1") or toaddr.startswith("tltc1"):
            outs[0]["new_segwit"] = True
        if changevalue > 0:
            outs.append({"value": changevalue, "address": self.address})
            if self.segwit == 1:
                outs[-1]["segwit"] = True
            if self.segwit == 2:
                outs[-1]["new_segwit"] = True
        self.tx = cryptos.coins.litecoin.Litecoin(testnet=self.testnet).mktx(inputs, outs)
        if self.segwit == 0:
            script = cryptos.mk_pubkey_script(self.address)
        # elif :
        # script = cryptos.mk_scripthash_script(self.address)
        elif self.segwit == 2 or self.segwit == 1:
            script = cryptos.mk_p2wpkh_scriptcode(self.pubkey)
        else:
            raise Exception("Not valid segwit option")

        # Finish tx
        # Sign each input
        self.leninputs = len(inputs)
        datahashes = []
        for i in range(self.leninputs):
            print("\nSigning INPUT #", i)
            signing_tx = cryptos.signature_form(self.tx, i, script, cryptos.SIGHASH_ALL)
            datahashes.append(cryptos.bin_txhash(signing_tx, cryptos.SIGHASH_ALL))
        return datahashes

    def send(self, signatures):
        for i in range(self.leninputs):
            signature_der_hex = signatures[i].hex() + "01"
            if self.segwit == 0:
                self.tx["ins"][i]["script"] = cryptos.serialize_script(
                    [signature_der_hex, self.pubkey]
                )
            if self.segwit > 0:
                if self.segwit == 1:
                    self.tx["ins"][i]["script"] = cryptos.mk_p2wpkh_redeemscript(self.pubkey)
                elif self.segwit == 2:
                    self.tx["ins"][i]["script"] = ""
                else:
                    raise Exception("Not valid segwit option")
                self.tx["witness"].append(
                    {
                        "number": 2,
                        "scriptCode": cryptos.serialize_script([signature_der_hex, self.pubkey]),
                    }
                )
        txhex = cryptos.serialize(self.tx)
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
            if self.segwit == 1:
                sutxo["segwit"] = True
            if self.segwit == 2:
                sutxo["new_segwit"] = True
            sel_utxos.append(sutxo)
            if 0 >= amount:
                break
        if 0 >= amount:
            return sel_utxos
        else:
            raise Exception("Not enough utxos values for the tx")


LTC_units = 1e8


class LTC_wallet:

    networks = [
        "mainnet",
        "testnet",
    ]

    wtypes = [
        "Legacy standard",
        "Segwit compatible",
        # "Segwit bech32",
    ]

    def __init__(self, network, wtype, device):
        self.current_device = device
        pubkey = self.current_device.get_public_key()
        network_name = self.networks[network]
        self.ltc = LTCwalletCore(pubkey, network_name, wtype, sochain_api(network_name))

    @classmethod
    def get_networks(cls):
        return cls.networks

    @classmethod
    def get_account_types(cls):
        return cls.wtypes

    def get_account(self):
        # Read address to fund the wallet
        return self.ltc.address

    def get_balance(self):
        # Get balance in base integer unit
        return str(self.ltc.getbalance() / LTC_units) + " LTC"

    def check_address(self, addr_str):
        # Check if address is valid
        # Quick check with regex, doesnt compute checksum
        return testaddr(addr_str)

    def history(self):
        # Get history as tx list
        raise "Not yet implemented"

    def raw_tx(self, amount, fee, to_account):
        hashes_to_sign = self.ltc.prepare(to_account, amount, fee)
        tx_signatures = []
        for msg in hashes_to_sign:
            asig = self.current_device.sign(msg)
            tx_signatures.append(asig)
        return self.ltc.send(tx_signatures)

    def assess_fee(self, fee_priority):
        # Get fee assesment for a wallet tx
        fee_unit = self.ltc.api.get_fee(fee_priority)
        # Approx tx "virtual" size for an average transaction :
        #  2 inputs in the wallet format (mean coins used)
        #  plus 1 standard output (max size) and 1 output in the wallet format (change)
        tx_size = 374
        if self.ltc.segwit == 1:  #  P2WPKH in P2SH : -31%
            tx_size = 259
        if self.ltc.segwit == 2:  #  P2WPKH         : -43%
            tx_size = 211
        fee = int(fee_unit * tx_size)
        if fee < 375:  # set minimum for good relay
            fee = 375
        return fee

    def transfer(self, amount, to_account, fee_priority):
        # Transfer x base unit to an account, pay
        fee = self.assess_fee(fee_priority)
        return self.raw_tx(int(amount * LTC_units), fee, to_account)

    def transfer_inclfee(self, amount, to_account, fee_priority):
        # Transfer the amount in base unit minus fee, like the receiver paying the fee
        fee = self.assess_fee(fee_priority)
        return self.raw_tx(amount - fee, fee, to_account)

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.ltc.getbalance()
        return self.transfer_inclfee(all_amount, to_account, fee_priority)