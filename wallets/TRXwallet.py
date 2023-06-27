#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW TRON wallet
# Copyright (C) 2023- BitLogiK

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
from logging import getLogger

from cryptolib.base58 import encode_base58, decode_base58
from cryptolib.cryptography import sha2, sha3, public_key_recover
from wallets.wallets_utils import InvalidOption, balance_string, shift_10, NotEnoughTokens
from cryptolib.coins.ethereum import uint256, read_string
from wallets.TRXtokens import tokens_values

logger = getLogger(__name__)


T_HEADER = b"\x41"


def compute_trx_address(pubkey):
    key_hash = sha3(pubkey[1:])[-20:]
    return encode_base58(T_HEADER + key_hash)


def compute_evm_addr(trx_addr):
    """Convert base58 Tron address into 256 bit EVM hex address"""
    bin_addr = decode_base58(trx_addr)
    if len(bin_addr) != 21:
        raise ValueError("Invalid TRX address")
    if bin_addr[:1] != T_HEADER:
        raise ValueError("Invalid TRX address header")
    return "00" * 12 + bin_addr[1:].hex()


def testaddr(tron_addr):
    # Safe tests of the address format
    checked = False
    if tron_addr.startswith("T"):
        checked = re.match("^[T][a-km-zA-HJ-NP-Z1-9]{25,33}$", tron_addr) is not None
    try:
        if checked:
            decode_base58(tron_addr)
    except ValueError:
        return False
    if checked:
        return tron_addr
    return False


def convert_signature(pubkey, datahash, signature_der):
    """Convert DER signature into Tron format XYV hex."""
    # Signature decoding
    lenr = int(signature_der[3])
    lens = int(signature_der[5 + lenr])
    r_int = int.from_bytes(signature_der[4 : lenr + 4], "big")
    s_int = int.from_bytes(signature_der[lenr + 6 : lenr + 6 + lens], "big")
    h = int.from_bytes(datahash, "big")

    # Parity recovery
    parity = 0
    if public_key_recover(h, r_int, s_int, parity) == pubkey:
        parity = 1

    # Signature encoding
    r = uint256(r_int)
    s = uint256(s_int)
    v = bytes([parity])
    return (r + s + v).hex()


class TronApi:
    def __init__(self, network):
        if network == "mainnet":
            self.api_domain = "https://api.trongrid.io"
        elif network == "shasta":
            self.api_domain = "https://api.shasta.trongrid.io"
        elif network == "nile":
            self.api_domain = "https://nile.trongrid.io"
        else:
            raise ValueError("Invalid network")

    def getData(self, endpoint, data=None):
        """POST data to the Tron RPC API endpoint"""
        if data is not None and isinstance(data, dict):
            data = json.dumps(data).encode("utf8")
        try:
            req = urllib.request.Request(
                f"{self.api_domain}{endpoint}",
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
            raise IOError(f"Error while processing request:\n{self.api_domain}{endpoint}")

    def get_balance(self, addr):
        # TRX native balance
        data_call = {"address": addr, "visible": True}
        ret = self.getData("/wallet/getaccount", data_call)
        if ret == {} or "balance" not in ret:
            return 0
        return ret["balance"]

    def call(self, from_addr, contract, method, data_params=""):
        """EVM call, equivalent to eth_call"""
        query = {
            "owner_address": from_addr,
            "contract_address": contract,
            "function_selector": method,
            "parameter": data_params,
            "visible": True,
        }
        resp = self.getData("/wallet/triggerconstantcontract", query)
        if "result" in resp and resp["result"].get("result") is True:
            if "constant_result" in resp:
                res = resp["constant_result"]
                if isinstance(res, list) and len(res) >= 1:
                    return res[0]
        return ""

    def create_tx(self, from_addr, to, amount, token_contract=None):
        """Build a transaction to be signed."""
        req = {"owner_address": from_addr, "visible": True}
        if token_contract is None:
            # TRX transfer
            req.update({"to_address": to, "amount": amount})
            resp = self.getData("/wallet/createtransaction", req)
            if not resp:
                return {}
            return resp
        # TRC20 transfer
        params = compute_evm_addr(to) + uint256(amount).hex()
        req.update(
            {
                "contract_address": token_contract,
                "function_selector": "transfer(address,uint256)",
                "parameter": params,
                "fee_limit": 25000000,
                "call_value": 0,
            }
        )
        resp = self.getData("/wallet/triggersmartcontract", req)
        if "result" in resp and resp["result"].get("result") is True:
            if "transaction" in resp:
                return resp["transaction"]
        return {}

    def broadcast(self, tx_data):
        resp = self.getData("/wallet/broadcasttransaction", tx_data)
        if resp.get("result") is True and "txid" in resp:
            return resp["txid"]
        logger.error(resp)
        if "message" in resp:
            try:
                err_msg = bytes.fromhex(resp["message"]).decode("utf8")
            except ValueError:
                err_msg = resp["message"]
            raise Exception(f"Broadcast error : {err_msg}")
        raise Exception("Broadcast error")


TRX_DECIMALS = 6


class TRX_wallet:
    coin = "TRX"

    networks = [
        "Mainnet",
        "Shasta",
        "Nile",
    ]

    wtypes = ["Standard", "ERC20"]

    derive_paths = [
        # Mainnet
        [
            "m/44'/195'/{}'/0/{}",
        ],
        # Testnet Shasta
        [
            "m/44'/1'/{}'/0/{}",
        ],
        # Testnet Nile
        [
            "m/44'/1'/{}'/0/{}",
        ],
    ]

    user_options = [1]
    # self.__init__ ( option_name = "user input option" )
    options_data = [
        {
            "option_name": "contract_addr",
            "prompt": "TRC20 contract address",
            "preset": tokens_values,
        },
    ]

    def __init__(
        self, network, wtype, device, contract_addr=None, wc_uri=None, confirm_callback=None
    ):
        self.network = TRX_wallet.networks[network].lower()

        if wtype == 0:
            if contract_addr is not None:
                raise ValueError("Invalid type choice.")
        elif wtype == 1:
            if contract_addr is None:
                raise ValueError("Invalid type choice.")
            if not testaddr(contract_addr):
                raise InvalidOption("Invalid contract address format :\nshould be T...")
        else:
            raise ValueError("Invalid wtype.")

        if self.network == "mainnet":
            self.explorer = "https://tronscan.org/#/address/"
        elif self.network == "shasta":
            self.explorer = "https://shasta.tronscan.org/#/address/"
        elif self.network == "nile":
            self.explorer = "https://nile.tronscan.org/#/address/"
        else:
            raise ValueError("Invalid network")

        self.current_device = device
        self.pubkey = self.current_device.get_public_key()
        self.address = compute_trx_address(self.pubkey)
        self.evm_addr = compute_evm_addr(self.address)
        self.api = TronApi(self.network)
        self.contract = contract_addr
        self.coin = self.get_symbol()
        self.decimals = self.get_decimals()

    @classmethod
    def get_networks(cls):
        return cls.networks

    @classmethod
    def get_account_types(cls):
        return cls.wtypes

    @classmethod
    def get_path(cls, network_name, wtype, legacy):
        deriv_path = cls.derive_paths[network_name][0]
        if legacy:
            # Legacy path alternative derivation
            deriv_path = deriv_path.replace("0/", "")
        return deriv_path

    @classmethod
    def get_key_type(cls, wtype):
        # No list, it's all k1
        return "K1"

    def get_decimals(self):
        if self.contract:
            # ERC20
            dec_raw = self.api.call(self.address, self.contract, "decimals()")
            if dec_raw == "":
                return 0
            return int(dec_raw, 16)
        return TRX_DECIMALS

    def get_symbol(self):
        if self.contract:
            symbraw = self.api.call(self.address, self.contract, "symbol()")
            if symbraw == "":
                return "---"
            return read_string("0x" + symbraw)
        return TRX_wallet.coin

    def get_account(self):
        # Read address to fund the wallet
        return self.address

    def get_int_bal(self):
        if self.contract:
            balraw = self.api.call(self.address, self.contract, "balanceOf(address)", self.evm_addr)
            if balraw == "":
                balance = 0
            else:
                balance = int(balraw, 16)
        else:
            balance = self.api.get_balance(self.address)
        return balance

    def get_balance(self):
        # Get balance in base integer unit and return string with unit
        balance = self.get_int_bal()
        return balance_string(balance, self.decimals)[:20] + " " + self.coin

    def check_address(self, addr_str):
        # Check if address is valid
        return testaddr(addr_str)

    def history(self):
        # Get history page
        explorer_url = f"{self.explorer}{self.address}"
        if self.contract:
            explorer_url += "/transfers"
        return explorer_url

    def prepare(self, amnt, to):
        """Build a tx"""
        maxspendable = self.get_int_bal()
        if amnt > maxspendable:
            raise NotEnoughTokens(f"Not enough {self.coin} tokens for the tx.")
        new_tx = self.api.create_tx(self.address, to, amnt, self.contract)
        if "raw_data_hex" not in new_tx or "txID" not in new_tx:
            raise Exception("Error : cannot build the transaction.")
        return new_tx

    def build_tx(self, amount, to_account):
        """Build and sign a transaction.
        Used to transfer tokens.
        """
        tx = self.prepare(amount, to_account)
        logger.debug(tx)
        # Check TxID is correct
        try:
            txid = sha2(bytes.fromhex(tx["raw_data_hex"]))
        except ValueError:
            raise Exception("Bad rawtx format.")
        if txid != bytes.fromhex(tx["txID"]):
            raise Exception("Invalid hash data.")
        # Before signing, a quick check that
        # the money wasn't fully diverted during CreateTx.
        dest_addr = compute_evm_addr(to_account)
        if not self.contract:
            dest_addr = dest_addr[24:]
        if dest_addr not in tx["raw_data_hex"].lower():
            raise Exception("Destination not present in tx created.")
        signature = self.current_device.sign(txid)
        sig_hex_tron = convert_signature(self.pubkey, txid, signature)
        tx["signature"] = [sig_hex_tron]
        return tx

    def transfer(self, amount, to_account, fee_priority):
        amnt_int = shift_10(amount, self.get_decimals())
        tx_data = self.build_tx(amnt_int, to_account)
        return "\nDONE, txID : " + self.api.broadcast(tx_data)

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the tokens to an address
        if self.contract is None:
            raise NotImplementedError(
                "Transfer all is not implemented for native TRX. Set amount manually."
            )
        all_amount = self.get_int_bal()
        tx_data = self.build_tx(all_amount, to_account)
        return "\nDONE, txID : " + self.api.broadcast(tx_data)
