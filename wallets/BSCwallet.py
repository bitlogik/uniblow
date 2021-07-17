#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW BSC wallet with with Binance web3 API REST
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
    import sha3
except Exception:
    raise Exception("Requires PySHA3 : pip3 install pysha3")


def rlp_encode(input):
    if isinstance(input, bytearray):
        if len(input) == 1 and input[0] == 0:
            return bytearray(b"\x80")
        if len(input) == 1 and input[0] < 0x80:
            return input
        else:
            return encode_length(len(input), 0x80) + input
    elif isinstance(input, list):
        output = bytearray([])
        for item in input:
            output += rlp_encode(item)
        return encode_length(len(output), 0xC0) + output
    raise Exception("Bad input type, list or bytearray needed")


def encode_length(L, offset):
    if L < 56:
        return bytearray([L + offset])
    BL = to_binary(L)
    return bytearray([len(BL) + offset + 55]) + BL


def to_binary(x):
    if x == 0:
        return bytearray([])
    else:
        return to_binary(int(x // 256)) + bytearray([x % 256])


def int2bytearray(i):
    barr = (i).to_bytes(32, byteorder="big")
    while barr[0] == 0 and len(barr) > 1:
        barr = barr[1:]
    return bytearray(barr)


class web3_api:
    def __init__(self, api_key, network):
        self.network = network
        self.url = "https://bsc-dataseed.binance.org/"
        if network.lower() == "testnet":
            self.url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
        self.jsres = []

    def getData(self, method, params=[]):
        # parameters = {key: value for key, value in params.items()}
        # parameters.update( self.params )
        if isinstance(params, str):
            params = [params]
        data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        try:
            req = urllib.request.Request(
                self.url,
                headers={"User-Agent": "Uniblow/1", "Content-Type": "application/json"},
                data=json.dumps(data).encode("utf-8"),
            )
            self.webrsc = urllib.request.urlopen(req)
            self.jsres = json.load(self.webrsc)
        except Exception:
            raise IOError(
                "Error while processing request:\n%s"
                % (self.url + "->" + method + " : " + str(params))
            )

    def checkapiresp(self):
        if "error" in self.jsres:
            print(" !! ERROR :")
            raise Exception(self.jsres["error"])
        if "errors" in self.jsres:
            print(" !! ERRORS :")
            raise Exception(self.jsres["errors"])

    def get_balance(self, addr, nconf):  # nconf 0 or 1
        if nconf == 0:
            datap = "pending"
        if nconf == 1:
            datap = "latest"
        self.getData("eth_getBalance", ["0x" + addr, datap])
        balraw = self.getKey("result")[2:]
        if balraw == []:
            return 0
        balance = int(balraw, 16)
        return balance

    def pushtx(self, txhex):
        self.getData("eth_sendRawTransaction", ["0x" + txhex])
        self.checkapiresp()
        return self.getKey("result")

    def get_tx_num(self, addr, blocks):
        self.getData("eth_getTransactionCount", ["0x" + addr, blocks])
        self.checkapiresp()
        return int(self.getKey("result")[2:], 16)

    def get_fee(self, priority):
        self.getData("eth_gasPrice")
        self.checkapiresp()
        gaz_price = int(self.getKey("result")[2:], 16) / 10 ** 9
        if priority == 0:
            return int(gaz_price * 0.9)
        if priority == 1:
            return int(gaz_price * 1.1)
        if priority == 2:
            return int(gaz_price * 1.6)
        raise Exception("bad priority argument for get_fee, must be 0, 1 or 2")

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


def has_checksum(addr):
    # addr without 0x
    return not addr.islower() and not addr.isupper() and not addr.isnumeric()


def format_checksum_address(addr):
    # Format an ETH address with checksum (without 0x)
    addr = addr.lower()
    addr_sha3hash = sha3.keccak_256(addr.encode("ascii")).hexdigest()
    cs_address = ""
    for idx, ci in enumerate(addr):
        if ci in "abcdef":
            cs_address += ci.upper() if int(addr_sha3hash[idx], 16) >= 8 else ci
            continue
        cs_address += ci
    return cs_address


def checksum_address(addr):
    # Check address sum (without 0x)
    return format_checksum_address(addr) == addr


def testaddr(eth_addr):
    # Safe reading of the address format
    if eth_addr.startswith("0x"):
        eth_addr = eth_addr[2:]
    if len(eth_addr) != 40:
        return False
    try:
        int(eth_addr, 16)
    except Exception:
        return False
    if has_checksum(eth_addr):
        return checksum_address(eth_addr)
    return True


class BSCwalletCore:
    def __init__(self, pubkey, network, api):
        self.pubkey = pubkey
        PKH = bytes.fromhex(cryptos.decompress(pubkey))
        self.Qpub = cryptos.decode_pubkey(pubkey)
        self.address = format_checksum_address(sha3.keccak_256(PKH[1:]).hexdigest()[-40:])
        self.api = api
        self.network = network

    def getbalance(self):
        return self.api.get_balance(self.address, 0)

    def getnonce(self):
        numtx = self.api.get_tx_num(self.address, "pending")
        return numtx

    def prepare(self, toaddr, paymentvalue, gprice, glimit):
        balance = self.getbalance()
        maxspendable = balance - ((gprice * glimit) * 10 ** 9)
        if paymentvalue > maxspendable or paymentvalue < 0:
            raise Exception("Not enough fund for the tx")
        self.nonce = int2bytearray(self.getnonce())
        self.gasprice = int2bytearray(gprice * 10 ** 9)
        self.startgas = int2bytearray(glimit)
        self.to = bytearray.fromhex(toaddr)
        self.value = int2bytearray(int(paymentvalue))
        self.data = bytearray(b"")
        if self.network == "mainnet":
            self.chainID = 56
        if self.network == "testnet":
            self.chainID = 97
        v = int2bytearray(self.chainID)
        r = int2bytearray(0)
        s = int2bytearray(0)
        signing_tx = rlp_encode(
            [
                self.nonce,
                self.gasprice,
                self.startgas,
                self.to,
                self.value,
                self.data,
                v,
                r,
                s,
            ]
        )
        self.datahash = sha3.keccak_256(signing_tx).digest()
        return self.datahash

    def send(self, signature_der):
        # Signature decoding
        lenr = int(signature_der[3])
        lens = int(signature_der[5 + lenr])
        r = int.from_bytes(signature_der[4 : lenr + 4], "big")
        s = int.from_bytes(signature_der[lenr + 6 : lenr + 6 + lens], "big")
        # Parity recovery
        Q = ecdsa.keys.VerifyingKey.from_public_key_recovery_with_digest(
            signature_der,
            self.datahash,
            ecdsa.curves.SECP256k1,
            sigdecode=ecdsa.util.sigdecode_der,
        )[1]
        if Q.to_string("uncompressed") == cryptos.encode_pubkey(self.Qpub, "bin"):
            i = 36
        else:
            i = 35
        # Signature encoding
        v = int2bytearray(2 * self.chainID + i)
        r = int2bytearray(r)
        s = int2bytearray(s)
        tx_final = rlp_encode(
            [
                self.nonce,
                self.gasprice,
                self.startgas,
                self.to,
                self.value,
                self.data,
                v,
                r,
                s,
            ]
        )
        txhex = tx_final.hex()
        return "\nDONE, txID : " + self.api.pushtx(txhex)[2:]


BSC_units = 10 ** 18


class BSC_wallet:

    networks = [
        "Mainnet",
        "Testnet",
    ]

    wtypes = [
        "Standard",
    ]

    derive_paths = [
        # mainnet
        [
            "m/44'/60'/0'/0/0",
        ],
        # testnet
        [
            "m/44'/1'/0'/0/0",
        ],
    ]

    GAZ_LIMIT_SIMPLE_TX = 21000

    def __init__(self, network, wtype, device):
        self.network = BSC_wallet.networks[network].lower()
        self.current_device = device
        pubkey = self.current_device.get_public_key()
        self.bsc = BSCwalletCore(pubkey, self.network, web3_api(None, self.network))

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
        # Read address to fund the wallet
        return f"0x{self.bsc.address}"

    def get_balance(self):
        # Get balance in base integer unit
        return str(self.bsc.getbalance() / BSC_units) + " BSC"

    def check_address(self, addr_str):
        # Check if address is valid
        return testaddr(addr_str)

    def history(self):
        # Get history page
        if self.network == "mainnet":
            BSC_EXPLORER_URL = f"https://www.bscscan.com/address/0x{self.bsc.address}"
        else:
            BSC_EXPLORER_URL = (
                f"https://testnet.bscscan.com/address/0x{self.bsc.address}"
            )
        return BSC_EXPLORER_URL

    def raw_tx(self, amount, gazprice, ethgazlimit, account):
        hash_to_sign = self.bsc.prepare(account, amount, gazprice, ethgazlimit)
        tx_signature = self.current_device.sign(hash_to_sign)
        return self.bsc.send(tx_signature)

    def transfer(self, amount, to_account, priority_fee):
        # Transfer x unit to an account, pay
        ethgazlimit = BSC_wallet.GAZ_LIMIT_SIMPLE_TX
        if to_account.startswith("0x"):
            to_account = to_account[2:]
        ethgazprice = self.bsc.api.get_fee(priority_fee)  # gwei per gaz unit
        return self.raw_tx(int(amount * BSC_units), ethgazprice, ethgazlimit, to_account)

    def transfer_inclfee(self, amount, to_account, fee_priority):
        # Transfer the amount in base unit minus fee, like the receiver paying the fee
        gazlimit = BSC_wallet.GAZ_LIMIT_SIMPLE_TX
        if to_account.startswith("0x"):
            to_account = to_account[2:]
        gazprice = self.bsc.api.get_fee(fee_priority)
        fee = gazlimit * gazprice
        return self.raw_tx(amount - int(fee * 10 ** 9), gazprice, gazlimit, to_account)

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.bsc.getbalance()
        return self.transfer_inclfee(all_amount, to_account, fee_priority)
