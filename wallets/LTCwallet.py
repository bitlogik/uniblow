#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW LTC wallet with electra API REST
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
import logging

import cryptolib.coins
from cryptolib.base58 import decode_base58
from cryptolib.bech32 import test_bech32
from cryptolib.cryptography import compress_pubkey, sha2
from wallets.name_service import resolve
from wallets.wallets_utils import balance_string, shift_10, NotEnoughTokens


logger = logging.getLogger(__name__)


class blockcypher_api:
    def __init__(self, network):
        self.url = "https://api.blockcypher.com/v1/ltc/main/"
        if network == "mainnet":
            self.coin = "LTC"
        else:
            raise Exception("Unknown LTC network name")
        self.jsres = []

    def getData(self, command, param, paramsurl={}, data=None):
        parameters = {key: value for key, value in paramsurl.items()}
        params_enc = urllib.parse.urlencode(parameters)
        url = f"{self.url}{command}/{param}"
        if params_enc:
            url += f"?{params_enc}"
        try:
            req = urllib.request.Request(
                url,
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
            raise IOError("Error while processing request:\n" f"{url}")

    def checkapiresp(self):
        if "errors" in self.jsres:
            logger.error(" !! ERROR : %s", self.jsres["errors"])
            raise Exception("Error decoding the API endpoint")

    def getutxos(self, addr, nconf):  # nconf 0 or 1
        self.getData("addrs", addr, {"unspentOnly": "true", "confirmations": nconf, "limit": 2000})
        self.checkapiresp()
        addrutxos = self.getKey("txrefs")
        selutxos = []
        # translate inputs from blockcypher to pybitcoinlib
        for utxo in addrutxos:
            selutxos.append(
                {
                    "value": utxo["value"],
                    "output": f'{utxo["tx_hash"]}:{utxo["tx_output_n"]}',
                }
            )
        return selutxos

    def pushtx(self, txhex):
        self.getData("txs", "push", data=f'{{"tx": "{txhex}"}}'.encode("ascii"))
        self.checkapiresp()
        return self.getKey("tx/hash")

    def getKey(self, keychar):
        out = self.jsres
        path = keychar.split("/")
        for key in path:
            if key.isdigit():
                key = int(key)
            try:
                out = out[key]
            except KeyError:
                out = []
        return out

    def get_fee(self, priority):
        return priority + 1


def testaddr(ltc_addr, is_testnet):
    # Safe tests of the address format
    checked = False
    addr_head = "L"
    addr_head_alt = "L"
    mult_head = "M"
    mult_head_alt = "3"
    segwit_head = "ltc"
    if is_testnet:
        addr_head = "n"
        addr_head_alt = "m"
        mult_head = "Q"
        mult_head_alt = "2"
        segwit_head = "tltc"
    if ltc_addr.startswith(addr_head) or ltc_addr.startswith(addr_head_alt):
        checked = re.match("^[Lnm][a-km-zA-HJ-NP-Z1-9]{25,34}$", ltc_addr) is not None
    elif ltc_addr.startswith(mult_head) or ltc_addr.startswith(mult_head_alt):
        checked = re.match("^[23MQ][a-km-zA-HJ-NP-Z1-9]{25,34}$", ltc_addr) is not None
    elif ltc_addr.startswith(segwit_head):
        checked = re.match("^(ltc|tltc)[01][ac-hj-np-z02-9]{8,87}$", ltc_addr) is not None
        if checked and test_bech32(ltc_addr):
            return ltc_addr
    else:
        return False
    try:
        if checked:
            decode_base58(ltc_addr)
    except ValueError:
        return False
    if checked:
        return ltc_addr
    return False


class LTCwalletCore:
    def __init__(self, pubkey, network_type, segwit_option, api):
        self.testnet = False
        if network_type == "testnet":
            self.testnet = True
        self.segwit = segwit_option
        self.pubkey = compress_pubkey(pubkey).hex()
        if self.segwit == 0:
            self.address = cryptolib.coins.litecoin.Litecoin(testnet=self.testnet).pubtoaddr(
                self.pubkey
            )
        elif self.segwit == 1:
            self.address = cryptolib.coins.litecoin.Litecoin(testnet=self.testnet).pubtop2w(
                self.pubkey
            )
        elif self.segwit == 2:
            self.address = cryptolib.coins.litecoin.Litecoin(testnet=self.testnet).pubtosegwit(
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
        self.tx = cryptolib.coins.litecoin.Litecoin(testnet=self.testnet).mktx(inputs, outs)
        if self.segwit == 0:
            script = cryptolib.coins.mk_pubkey_script(self.address)
        elif self.segwit == 2 or self.segwit == 1:
            script = cryptolib.coins.mk_p2wpkh_scriptcode(self.pubkey)
        else:
            raise Exception("Not valid segwit option")

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
            if self.segwit == 0:
                self.tx["ins"][i]["script"] = cryptolib.coins.serialize_script(
                    [signature_der_hex, self.pubkey]
                )
            if self.segwit > 0:
                if self.segwit == 1:
                    self.tx["ins"][i]["script"] = cryptolib.coins.mk_p2wpkh_redeemscript(
                        self.pubkey
                    )
                elif self.segwit == 2:
                    self.tx["ins"][i]["script"] = ""
                else:
                    raise Exception("Not valid segwit option")
                self.tx["witness"].append(
                    {
                        "number": 2,
                        "scriptCode": cryptolib.coins.serialize_script(
                            [signature_der_hex, self.pubkey]
                        ),
                    }
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
            raise NotEnoughTokens("Not enough utxos values for the tx")


LTC_units = 8


class LTC_wallet:
    coin = "LTC"

    networks = [
        "mainnet",
    ]

    wtypes = [
        "Legacy standard",
        "Segwit compatible",
        # "Segwit bech32",
    ]

    derive_paths = [
        # mainnet
        [
            "m/44'/2'/{}'/0/{}",
            "m/49'/2'/{}'/0/{}",
        ],
        # testnet
        [
            "m/44'/1'/{}'/0/{}",
            "m/49'/1'/{}'/0/{}",
        ],
    ]

    def __init__(self, network, wtype, device):
        self.current_device = device
        pubkey = self.current_device.get_public_key()
        network_name = self.networks[network]
        self.ltc = LTCwalletCore(pubkey, network_name, wtype, blockcypher_api(network_name))

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
        return self.ltc.address

    def get_balance(self):
        # Get balance in base integer unit
        return f"{balance_string(self.ltc.getbalance(), LTC_units)} {self.coin}"

    def check_address(self, addr_str):
        # Check if address or domain is valid
        resolved = resolve(addr_str, LTC_wallet.coin)
        if resolved:
            addr_str = resolved
        return testaddr(addr_str, self.ltc.testnet)

    def history(self):
        # Get history page
        return f"https://blockchair.com/litecoin/address/{self.ltc.address}"

    def raw_tx(self, amount, fee, to_account):
        msgs_to_sign = self.ltc.prepare(to_account, amount, fee)
        tx_signatures = []
        for msg in msgs_to_sign:
            if not self.current_device.has_screen:
                msg = sha2(msg)
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
        if self.ltc.segwit == 1:  # P2WPKH in P2SH : -31%
            tx_size = 259
        if self.ltc.segwit == 2:  # P2WPKH         : -43%
            tx_size = 211
        fee = int(fee_unit * tx_size)
        if fee < 375:  # set minimum for good relay
            fee = 375
        return fee

    def transfer(self, amount, to_account, fee_priority):
        # Transfer x base unit to an account, pay
        fee = self.assess_fee(fee_priority)
        return self.raw_tx(shift_10(amount, LTC_units), fee, to_account)

    def transfer_inclfee(self, amount, to_account, fee_priority):
        # Transfer the amount in base unit minus fee, like the receiver paying the fee
        fee = self.assess_fee(fee_priority)
        return self.raw_tx(amount - fee, fee, to_account)

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.ltc.getbalance()
        return self.transfer_inclfee(all_amount, to_account, fee_priority)
