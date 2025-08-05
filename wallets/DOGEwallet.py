#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW DOGE wallet with Blockcypher API REST
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
import logging
import urllib.parse
import urllib.request
import re

import cryptolib.coins
from cryptolib.base58 import decode_base58
from cryptolib.cryptography import compress_pubkey, sha2, encode_der_s
from wallets.name_service import resolve
from wallets.wallets_utils import balance_string, shift_10, NotEnoughTokens


logger = logging.getLogger(__name__)


class blockcypher_api:
    def __init__(self, network):
        self.url = "https://api.blockcypher.com/v1/doge/main/"
        if network == "mainnet":
            self.coin = "DOGE"
        else:
            raise Exception("Unknown DOGE network name")

    def getData(self, command, param, paramsurl={}, data=None):
        parameters = {key: value for key, value in paramsurl.items()}
        params_enc = urllib.parse.urlencode(parameters)
        url = f"{self.url}{command}/{param}"
        if params_enc:
            url += f"?{params_enc}"
        req = urllib.request.Request(
            url,
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
            raise IOError("Error while processing request:\n" f"{url}")

    def getutxos(self, addr, nconf):  # nconf 0 or 1
        addrutxos = self.getData(
            "addrs", addr, {"unspentOnly": "true", "confirmations": nconf, "limit": 2000}
        ).get("txrefs")
        selutxos = []
        if addrutxos is None:
            return selutxos
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
        return (
            self.getData("txs", "push", data=f'{{"tx": "{txhex}"}}'.encode("ascii"))
            .get("tx")
            .get("hash")
        )

    def get_fee(self, priority):
        return int(10**DOGE_units)


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
    if checked:
        return doge_addr
    return False


class DOGEwalletCore:
    def __init__(self, pubkey, network_type, segwit_option, api):
        self.testnet = False
        if network_type == "testnet":
            self.testnet = True
        self.segwit = segwit_option
        self.pubkey = compress_pubkey(pubkey).hex()
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
        self.doge = DOGEwalletCore(pubkey, network_name, wtype, blockcypher_api(network_name))

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
        return f"{balance_string(self.doge.getbalance(), DOGE_units)} {self.coin}"

    def check_address(self, addr_str):
        # Check if address or domain is valid
        resolved = resolve(addr_str, DOGE_wallet.coin)
        if resolved:
            addr_str = resolved
        return testaddr(addr_str, self.doge.testnet)

    def history(self):
        # Get history page
        return f"https://blockchair.com/dogecoin/address/{self.doge.address}"

    def raw_tx(self, amount, fee, to_account):
        msgs_to_sign = self.doge.prepare(to_account, amount, fee)
        tx_signatures = []
        for msg in msgs_to_sign:
            # DOGE is a non-EVM chain enabled for Satochip.
            # This requires a special case handling.
            if (
                self.current_device.__class__.__name__ == "Satochip"
                or not self.current_device.on_device_check
            ):
                msg = sha2(msg)
            asig = self.current_device.sign(msg)
            if self.current_device.provide_parity:
                # asig : v,r,s turn into DER
                asig = encode_der_s(asig[1], asig[2], "K1")
                # Even msg before hash is a hash, to be modified
            tx_signatures.append(asig)
        return self.doge.send(tx_signatures)

    def assess_fee(self, fee_priority):
        # Get fee assesment for a wallet tx
        fee = self.doge.api.get_fee(fee_priority)
        return fee

    def transfer(self, amount, to_account, fee_priority):
        # Transfer x base unit to an account, pay
        amnt_int = shift_10(amount, DOGE_units)
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
        all_amount = self.doge.getbalance()
        return self.transfer_inclfee(all_amount, to_account, fee_priority)
