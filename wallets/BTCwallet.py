#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW BTC wallet with electra API REST
# Copyright (C) 2021-2025 BitLogiK

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
from cryptolib.bech32 import test_bech32
from cryptolib.base58 import decode_base58
from cryptolib.cryptography import compress_pubkey, sha2, encode_der_s
from wallets.name_service import resolve
from wallets.wallets_utils import balance_string, shift_10, NotEnoughTokens


class blkhub_api:
    # Electra API
    def __init__(self, network):
        if network == "mainnet":
            self.url = "https://blockstream.info/api/"
        elif network == "testnet":
            self.url = "https://blockstream.info/testnet/api/"
        else:
            raise Exception("Unknown BTC network name")

    def getData(self, endpoint, params={}, data=None):
        parameters = {key: value for key, value in params.items()}
        params_enc = urllib.parse.urlencode(parameters)
        req = urllib.request.Request(
            f"{self.url}{endpoint}?{params_enc}",
            headers={"User-Agent": "Mozilla/5.0"},
            data=data,
        )
        try:
            webrsc = urllib.request.urlopen(req, timeout=12.0)
            brep = webrsc.read()
            if len(brep) == 64 and brep[0] != ord("{"):
                brep = b'{"txid":"' + brep + b'"}'
            res = json.loads(brep)
            if "error" in res:
                raise Exception(res["error"])
            if "errors" in res:
                raise Exception(res["errors"])
            return res
        except urllib.error.HTTPError as e:
            strerr = e.read()
            raise IOError(f"{e.code}  :  {strerr.decode('utf8')}")
        except urllib.error.URLError as e:
            raise IOError(e)
        except Exception:
            raise IOError(f"Error while processing request:\n{req.full_url}")

    def getutxos(self, addr, nconf):  # nconf 0 or 1
        addrutxos = self.getData("address/" + addr + "/utxo")
        selutxos = []
        # translate inputs from blkhub to pybitcoinlib
        for utxo in addrutxos:
            selutxos.append(
                {
                    "value": utxo["value"],
                    "output": utxo["txid"] + ":" + str(utxo["vout"]),
                }
            )
        return selutxos

    def pushtx(self, txhex):
        return self.getData("tx", data=txhex.encode("ascii")).get("txid")

    def get_fee(self, priority):
        fees_table = self.getData("fee-estimates")
        if priority == 0:
            return fees_table["504"]
        if priority == 1:
            return fees_table["10"]
        if priority == 2:
            return fees_table["2"]
        raise Exception("bad priority argument for get_fee, must be 0, 1 or 2")


def testaddr(btc_addr, is_testnet):
    # Safe tests of the address format
    checked = False
    addr_head = "1"
    addr_head_alt = "1"
    mult_head = "3"
    segwit_head = "bc"
    if is_testnet:
        addr_head = "n"
        addr_head_alt = "m"
        mult_head = "2"
        segwit_head = "tb"
    if btc_addr.startswith(addr_head) or btc_addr.startswith(addr_head_alt):
        checked = re.match("^[1nm][a-km-zA-HJ-NP-Z1-9]{25,34}$", btc_addr) is not None
    elif btc_addr.startswith(mult_head):
        checked = re.match("^[23][a-km-zA-HJ-NP-Z1-9]{25,34}$", btc_addr) is not None
    elif btc_addr.lower().startswith(segwit_head):
        checked = re.match("^(bc|tb)[01][ac-hj-np-z02-9]{8,87}$", btc_addr.lower()) is not None
        if checked and test_bech32(btc_addr):
            return btc_addr
    else:
        return False
    try:
        if checked:
            decode_base58(btc_addr)
    except ValueError:
        return False
    if checked:
        return btc_addr
    return False


class BTCwalletCore:
    def __init__(self, pubkey, network_type, segwit_option, api, pubk_cpr):
        self.testnet = False
        if network_type == "testnet":
            self.testnet = True
        self.segwit = segwit_option
        self.pubkey = compress_pubkey(pubkey).hex() if pubk_cpr else pubkey.hex()
        if self.segwit == 0:
            self.address = cryptolib.coins.bitcoin.Bitcoin(testnet=self.testnet).pubtoaddr(
                self.pubkey
            )
        elif self.segwit == 1:
            self.address = cryptolib.coins.bitcoin.Bitcoin(testnet=self.testnet).pubtop2w(
                self.pubkey
            )
        elif self.segwit == 2:
            self.address = cryptolib.coins.bitcoin.Bitcoin(testnet=self.testnet).pubtosegwit(
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
        if toaddr.startswith("bc0") or toaddr.startswith("tb0"):
            outs[0]["segwit"] = True
        if toaddr.startswith("bc1") or toaddr.startswith("tb1"):
            outs[0]["new_segwit"] = True
        if changevalue > 0:
            outs.append({"value": changevalue, "address": self.address})
            if self.segwit == 1:
                outs[-1]["segwit"] = True
            if self.segwit == 2:
                outs[-1]["new_segwit"] = True
        self.tx = cryptolib.coins.bitcoin.Bitcoin(testnet=self.testnet).mktx(inputs, outs)
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


BTC_units = 8


class BTC_wallet:
    coin = "BTC"

    networks = [
        "mainnet",
        "testnet",
    ]

    wtypes = [
        "Legacy standard",
        "Segwit compatible",
        "Segwit bech32",
    ]

    derive_paths = [
        # mainnet
        [
            "m/44'/0'/{}'/0/{}",
            "m/49'/0'/{}'/0/{}",
            "m/84'/0'/{}'/0/{}",
        ],
        # testnet
        [
            "m/44'/1'/{}'/0/{}",
            "m/49'/1'/{}'/0/{}",
            "m/84'/1'/{}'/0/{}",
        ],
    ]

    def __init__(self, network, wtype, device, pk_compress=True):
        self.current_device = device
        pubkey = self.current_device.get_public_key()
        network_name = self.networks[network]
        self.btc = BTCwalletCore(pubkey, network_name, wtype, blkhub_api(network_name), pk_compress)

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
        return self.btc.address

    def get_balance(self):
        # Get balance in base integer unit
        return f"{balance_string(self.btc.getbalance(), BTC_units)} {self.coin}"

    def check_address(self, addr_str):
        # Check if address or domain is valid
        resolved = resolve(addr_str, BTC_wallet.coin)
        if resolved:
            addr_str = resolved
        return testaddr(addr_str, self.btc.testnet)

    def history(self):
        # Get history page
        if self.btc.testnet:
            BTC_EXPLORER_URL = f"https://blockstream.info/testnet/address/{self.btc.address}"
        else:
            BTC_EXPLORER_URL = f"https://blockstream.info/address/{self.btc.address}"
        return BTC_EXPLORER_URL

    def raw_tx(self, amount, fee, to_account):
        msgs_to_sign = self.btc.prepare(to_account, amount, fee)
        tx_signatures = []
        for msg in msgs_to_sign:
            if not self.current_device.on_device_check:
                msg = sha2(msg)
                # Even msg before hash is a hash, to be modified
            asig = self.current_device.sign(msg)
            if self.current_device.provide_parity:
                # asig : v,r,s turn into DER
                asig = encode_der_s(asig[1], asig[2], "K1")
            tx_signatures.append(asig)
        return self.btc.send(tx_signatures)

    def assess_fee(self, fee_priority):
        # Get fee assesment for a wallet tx
        fee_unit = self.btc.api.get_fee(fee_priority)
        # Approx tx "virtual" size for an average transaction :
        #  2 inputs in the wallet format (mean coins used)
        #  plus 1 standard output (max size) and 1 output in the wallet format (change)
        tx_size = 374
        if self.btc.segwit == 1:  # P2WPKH in P2SH : -31%
            tx_size = 259
        if self.btc.segwit == 2:  # P2WPKH         : -43%
            tx_size = 211
        fee = int(fee_unit * tx_size)
        if fee < 490:  # set minimum for good relay
            fee = 490
        return fee

    def transfer(self, amount, to_account, fee_priority):
        # Transfer x base unit to an account, pay
        amnt_int = shift_10(amount, BTC_units)
        if amnt_int == 0:
            raise Exception("Amount is zero.")
        fee = self.assess_fee(fee_priority)
        return self.raw_tx(amnt_int, fee, to_account)

    def transfer_inclfee(self, amount, to_account, fee_priority):
        # Transfer the amount in base unit minus fee, like the receiver paying the fee
        fee = self.assess_fee(fee_priority)
        net_amount = amount - fee
        if net_amount <= 0:
            raise Exception("Not enough fund to cover fees.")
        return self.raw_tx(net_amount, fee, to_account)

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.btc.getbalance()
        return self.transfer_inclfee(all_amount, to_account, fee_priority)
