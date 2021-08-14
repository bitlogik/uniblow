#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW ETH wallet with with BlockCypher, Etherscan or Infura API REST
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
import time
import urllib.parse
import urllib.request

from cryptolib.cryptography import public_key_recover, decompress_pubkey, sha3
from cryptolib.coins.ethereum import rlp_encode, int2bytearray, uint256, read_string
from wallets.wallets_utils import shift_10, compare_eth_addresses, InvalidOption
from wallets.ETHtokens import tokens_values
from pywalletconnect import WalletConnectClient, WalletConnectClientInvalidOption


ETH_units = 18
GWEI_UNIT = 10 ** 9


# ERC20 functions codes
#   balanceOf(address)
BALANCEOF_FUNCTION = "70a08231"
#   decimals()
DECIMALS_FUNCTION = "313ce567"
#   symbol()
SYMBOL_FUNCTION = "95d89b41"
#   transfer(address,uint256)
TRANSFERT_FUNCTION = "a9059cbb"


class infura_api:
    def __init__(self, api_key, network):
        # https://ropsten.infura.io/v3/YOUR-PROJECT-ID
        #         mainnet
        self.apikey = api_key
        self.url = f"https://{network}.infura.io/v3/{self.apikey}"
        self.jsres = []

    def getData(self, method, params=[]):
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
        except urllib.error.HTTPError as e:
            strerr = e.read()
            raise IOError(f"{e.code}  :  {strerr.decode('utf8')}")
        except urllib.error.URLError as e:
            raise IOError(e)
        except Exception:
            raise IOError(f"Error while processing request:\n {self.url}  :  {method} ,  {params}")

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
        if balraw == [] or balraw == "":
            return 0
        balance = int(balraw, 16)
        return balance

    def call(self, contract, command_code, data=""):
        datab = f"0x{command_code}{data}"
        self.getData("eth_call", [{"to": contract, "data": datab}, "pending"])
        return self.getKey("result")

    def pushtx(self, txhex):
        self.getData("eth_sendRawTransaction", ["0x" + txhex])
        self.checkapiresp()
        return self.getKey("result")

    def get_tx_num(self, addr, blocks):
        self.getData("eth_getTransactionCount", ["0x" + addr, blocks])
        self.checkapiresp()
        return int(self.getKey("result")[2:], 16)

    def get_fee(self, priority):
        """Get the gas price in Gwei units"""
        self.getData("eth_gasPrice")
        self.checkapiresp()
        gaz_price = int(self.getKey("result")[2:], 16) / GWEI_UNIT
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


class etherscan_api:
    def __init__(self, api_key, network):
        self.apikey = api_key
        # https://api.etherscan.io/api?module=account&action=balance&address=0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae&tag=latest&apikey=YourApiKeyToken
        if network == "mainnet":
            self.url = "https://api.etherscan.io/api"
        else:
            self.url = f"https://api-{network}.etherscan.io/api"
        self.params = {"token": self.apikey}
        self.params = {}
        self.jsres = []

    def getData(self, parameters={}):
        parameters.update(self.params)
        params_enc = urllib.parse.urlencode(parameters)
        # data = {"jsonrpc":"2.0","method":method,"params":params ,"id":1}
        try:
            # Enforce 5s per query without apikey
            time.sleep(5)
            req = urllib.request.Request(
                self.url + "?" + params_enc,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Content-Type": "application/json",
                },
                # data = json.dumps(data).encode('utf-8')
            )
            self.webrsc = urllib.request.urlopen(req)
            self.jsres = json.load(self.webrsc)
        except Exception:
            raise IOError(
                "Error while processing request:\n%s"
                % (self.url + "->" + parameters + " : " + str(self.params))
            )

    def checkapiresp(self):
        if "error" in self.jsres:
            print(" !! ERROR :")
            raise Exception(self.jsres["error"])
        if "errors" in self.jsres:
            print(" !! ERRORS :")
            raise Exception(self.jsres["errors"])

    def get_balance(self, addr, nconf):  # nconf 0 or 1
        self.getData({"module": "account", "action": "balance", "address": "0x" + addr})
        balraw = self.getKey("result")
        if balraw == []:
            return 0
        balance = int(balraw)
        return balance

    def call(self, contract, command_code, data=""):
        raise NotImplementedError()

    def pushtx(self, txhex):
        self.getData({"module": "proxy", "action": "eth_sendRawTransaction", "hex": "0x" + txhex})
        self.checkapiresp()
        return self.getKey("result")

    def get_tx_num(self, addr, blocks):
        self.getData(
            {
                "module": "proxy",
                "action": "eth_getTransactionCount",
                "address": f"0x{addr}",
            }
        )
        self.checkapiresp()
        return int(self.getKey("result")[2:], 16)

    def get_fee(self, priority):
        raise Exception("Not yet implemented for this API")

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
    addr_sha3hash = sha3(addr.encode("ascii")).hex()
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


class ETHwalletCore:
    def __init__(self, pubkey, network, api, ERC20=None):
        self.pubkey = decompress_pubkey(pubkey)
        key_hash = sha3(self.pubkey[1:])
        self.address = format_checksum_address(key_hash.hex()[-40:])
        self.ERC20 = ERC20
        self.api = api
        if network == "mainnet":
            self.chainID = 1
        if network == "ropsten":
            self.chainID = 3
        if network == "rinkeby":
            self.chainID = 4
        if network == "goerli":
            self.chainID = 5
        if network == "kovan":
            self.chainID = 42
        self.decimals = self.get_decimals()
        self.token_symbol = self.get_symbol()

    def getbalance(self, native=True):
        if native:
            # ETH native balance
            return self.api.get_balance(self.address, 0)
        else:
            # ERC20 token balance
            balraw = self.api.call(
                self.ERC20, BALANCEOF_FUNCTION, "000000000000000000000000" + self.address
            )
            if balraw == [] or balraw == "0x":
                return 0
            balance = int(balraw[2:], 16)
            return balance

    def get_decimals(self):
        if self.ERC20:
            balraw = self.api.call(self.ERC20, DECIMALS_FUNCTION)
            if balraw == [] or balraw == "0x":
                return 1
            return int(balraw[2:], 16)
        else:
            return ETH_units

    def get_symbol(self):
        if self.ERC20:
            balraw = self.api.call(self.ERC20, SYMBOL_FUNCTION)
            if balraw == [] or balraw == "0x":
                return "---"
            return read_string(balraw)

    def getnonce(self):
        numtx = self.api.get_tx_num(self.address, "pending")
        return numtx

    def prepare(self, toaddr, paymentvalue, gprice, glimit, data=bytearray(b"")):
        """Build a transaction to be signed.
        toaddr in hex without 0x
        value in wei, gprice in Gwei
        """
        if self.ERC20:
            maxspendable = self.getbalance(False)
            balance_eth = self.getbalance()
            if balance_eth < ((gprice * glimit) * GWEI_UNIT):
                raise Exception("Not enough native ETH funding for the tx fee")
        else:
            maxspendable = self.getbalance() - ((gprice * glimit) * GWEI_UNIT)
        if paymentvalue > maxspendable or paymentvalue < 0:
            raise Exception(f"Not enough {self.token_symbol} tokens for the tx")
        self.nonce = int2bytearray(self.getnonce())
        self.gasprice = int2bytearray(gprice * GWEI_UNIT)
        self.startgas = int2bytearray(glimit)
        if self.ERC20:
            self.to = bytearray.fromhex(self.ERC20[2:])
            self.value = int2bytearray(int(0))
            self.data = bytearray.fromhex(TRANSFERT_FUNCTION + "00" * 12 + toaddr) + uint256(
                paymentvalue
            )
        else:
            self.to = bytearray.fromhex(toaddr)
            self.value = int2bytearray(int(paymentvalue))
            self.data = data
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
        self.datahash = sha3(signing_tx)
        return self.datahash

    def add_signature(self, signature_der):
        # Signature decoding
        lenr = int(signature_der[3])
        lens = int(signature_der[5 + lenr])
        r = int.from_bytes(signature_der[4 : lenr + 4], "big")
        s = int.from_bytes(signature_der[lenr + 6 : lenr + 6 + lens], "big")
        # Parity recovery
        i = 35
        h = int.from_bytes(self.datahash, "big")
        if public_key_recover(h, r, s, i) != self.pubkey:
            i += 1
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
        return tx_final.hex()

    def send(self, tx_hex):
        """Upload the tx"""
        return self.api.pushtx(tx_hex)


class ETH_wallet:

    coin = "ETH"

    networks = [
        "Mainnet",
        "Rinkeby",
        "Ropsten",
        "Kovan",
        "Goerli",
    ]

    wtypes = ["Standard", "ERC20", "WalletConnect"]

    derive_paths = [
        # mainnet
        [
            "m/44'/60'/0'/0/",
        ],
        # testnets
        [
            "m/44'/1'/0'/0/",
        ],
        [
            "m/44'/1'/0'/0/",
        ],
        [
            "m/44'/1'/0'/0/",
        ],
        [
            "m/44'/1'/0'/0/",
        ],
    ]

    # ETH wallet type 1 and 2 have option
    user_options = [1, 2]
    # self.__init__ ( contract_addr = "user input option" )
    options_data = [
        {
            "option_name": "contract_addr",
            "prompt": "ERC20 contract address",
            "preset": tokens_values,
        },
        {
            "option_name": "wc_uri",
            "prompt": "WalletConnect URI link",
            "use_get_messages": True,
        },
    ]

    GAZ_LIMIT_SIMPLE_TX = 21000
    GAZ_LIMIT_ERC_20_TX = 180000

    def __init__(
        self, network, wtype, device, contract_addr=None, wc_uri=None, confirm_callback=None
    ):
        self.network = ETH_wallet.networks[network].lower()
        self.current_device = device
        self.confirm_callback = confirm_callback
        pubkey_hex = self.current_device.get_public_key()
        INFURA_KEY = "xxx"
        if INFURA_KEY == "xxx":
            raise Exception(
                "To use Uniblow from source, bring your own Infura key, or use etherscan_api"
            )
        if contract_addr is not None:
            if len(contract_addr) == 42 and "0x" == contract_addr[:2]:
                contract_addr_str = contract_addr.lower()
            elif len(contract_addr) == 40:
                contract_addr_str = "0x" + contract_addr.lower()
            else:
                raise InvalidOption(
                    "Invalid contract address format :\nshould be 0x/40hex/ or /40hex/"
                )
        else:
            contract_addr_str = None
        self.eth = ETHwalletCore(
            pubkey_hex, self.network, infura_api(INFURA_KEY, self.network), contract_addr_str
        )
        if contract_addr_str is not None:
            self.coin = self.eth.token_symbol
        if wc_uri is not None:
            try:
                self.wc_client = WalletConnectClient.from_wc_uri(wc_uri)
                req_id, req_chain_id, request_info = self.wc_client.open_session()
            except WalletConnectClientInvalidOption as exc:
                if hasattr(self, "wc_client"):
                    self.wc_client.close()
                raise InvalidOption(exc)
            if req_chain_id != self.eth.chainID:
                self.wc_client.close()
                raise InvalidOption("Chain ID is different.")
            request_message = (
                "WalletConnect request from :\n\n"
                f"{request_info['name']}\n"
                f"website : {request_info['url']}\n"
            )
            approve = self.confirm_callback(request_message)
            if approve:
                self.wc_client.reply_session_request(req_id, self.eth.chainID, self.get_account())
            else:
                self.wc_client.close()
                raise InvalidOption("You just declined the WalletConnect request.")

    def __del__(self):
        """Close the WebSocket connection when deleting the object."""
        if hasattr(self, "wc_client"):
            del self.wc_client

    @classmethod
    def get_networks(cls):
        return cls.networks

    @classmethod
    def get_account_types(cls):
        return cls.wtypes

    @classmethod
    def get_path(cls, network_name, wtype):
        return cls.derive_paths[network_name][0]

    def get_account(self):
        # Read address to fund the wallet
        return f"0x{self.eth.address}"

    # Process messages for WalletConnect
    # Get messages more often than balance
    def get_messages(self):
        # wc_message : (id, method, params) or (None, "", [])
        wc_message = self.wc_client.get_message()
        while wc_message[0] is not None:
            print(">>> received from WC :")
            print(wc_message)
            id_request = wc_message[0]
            method = wc_message[1]
            parameters = wc_message[2]
            if "wc_sessionUpdate" == method:
                if "approved" in parameters and parameters["approved"] is False:
                    self.wc_client.close()
                    raise Exception("Disconnected by the web app service")
            elif "personal_sign" == method:
                # Not implemented
                pass
            elif "eth_sign" == method:
                # Not implemented
                pass
            elif "eth_signTypedData" == method:
                # Not implemented
                pass
            elif "eth_sendTransaction" == method:
                print("----  Signature request received :")
                tx_to_sign = parameters[0]
                print(tx_to_sign)
                if compare_eth_addresses(tx_to_sign["from"], self.get_account()):
                    self.process_sendtransaction(id_request, tx_to_sign)
            elif "eth_signTransaction" == method:
                # Not implemented
                pass
            elif "eth_sendRawTransaction" == method:
                # Not implemented
                pass
            wc_message = self.wc_client.get_message()

    def get_balance(self):
        # Get balance in base integer unit
        return (
            str(self.eth.getbalance(not self.eth.ERC20) / (10 ** self.eth.decimals))
            + " "
            + self.coin
        )

    def check_address(self, addr_str):
        # Check if address is valid
        return testaddr(addr_str)

    def history(self):
        # Get history page
        if self.network == "mainnet":
            ETH_EXPLORER_URL = f"https://etherscan.io/address/0x{self.eth.address}"
        else:
            ETH_EXPLORER_URL = f"https://{self.network}.etherscan.io/address/0x{self.eth.address}"
        if self.eth.ERC20:
            ETH_EXPLORER_URL += "#tokentxns"
        return ETH_EXPLORER_URL

    def exec_tx(self, amount, gazprice, ethgazlimit, account, data=None):
        """Build, sign, and broadcast a transaction.
        Used to transfer tokens native or ERC20 with the given parameters.
        Return the tx hash broadcasted as 0xhhhhhhhh.
        """
        if data is None:
            data = bytearray(b"")
        hash_to_sign = self.eth.prepare(account, amount, gazprice, ethgazlimit, data)
        tx_signature = self.current_device.sign(hash_to_sign)
        tx_signed = self.eth.add_signature(tx_signature)
        return self.eth.send(tx_signed)

    def process_sendtransaction(self, id_request, txdata):
        """Process a WalletConnect eth_sendTransaction call"""
        to_addr = txdata.get("to", "  New contract")[2:]
        value = txdata.get("value", 0)
        if value != 0:
            value = int(value, 16)
        gas_price = txdata.get("gasPrice", 0)
        if gas_price != 0:
            gas_price = int(gas_price, 16) // GWEI_UNIT
        else:
            gas_price = self.eth.api.get_fee(1)
        gas_limit = txdata.get("gas", 90000)
        if gas_limit != 90000:
            gas_limit = int(gas_limit, 16)
        request_message = (
            "WalletConnect transaction request :\n\n"
            f" To    :  0x{to_addr}\n"
            f" Value :  {value / (10 ** self.eth.decimals)} {self.coin}\n"
            f" Gas price  : {gas_price} Gwei\n"
            f" Gas limit  : {gas_limit}\n"
            f"Max fee cost: {gas_limit*gas_price/GWEI_UNIT} {self.coin}\n"
        )
        if self.confirm_callback(request_message):
            data_hex = txdata.get("data", "0x")
            data = bytearray.fromhex(data_hex[2:])
            tx_hash = self.exec_tx(value, gas_price, gas_limit, to_addr, data)
            self.wc_client.reply(id_request, tx_hash)

    def transfer(self, amount, to_account, priority_fee):
        # Transfer x unit to an account, pay
        if self.eth.ERC20:
            ethgazlimit = ETH_wallet.GAZ_LIMIT_ERC_20_TX
        else:
            ethgazlimit = ETH_wallet.GAZ_LIMIT_SIMPLE_TX
        if to_account.startswith("0x"):
            to_account = to_account[2:]
        ethgazprice = self.eth.api.get_fee(priority_fee)  # gwei per gaz unit
        tx_hash = self.exec_tx(
            shift_10(amount, self.eth.decimals), ethgazprice, ethgazlimit, to_account
        )
        return "\nDONE, txID : " + tx_hash[2:]

    def transfer_inclfee(self, amount, to_account, fee_priority):
        # Transfer the amount in base unit minus fee, like the receiver paying the fee
        if self.eth.ERC20:
            gazlimit = ETH_wallet.GAZ_LIMIT_ERC_20_TX
        else:
            gazlimit = ETH_wallet.GAZ_LIMIT_SIMPLE_TX
        if to_account.startswith("0x"):
            to_account = to_account[2:]
        gazprice = self.eth.api.get_fee(fee_priority)
        if self.eth.ERC20:
            fee = 0
        else:
            fee = int(gazlimit * gazprice * GWEI_UNIT)
        tx_hash = self.exec_tx(amount - fee, gazprice, gazlimit, to_account)
        return "\nDONE, txID : " + tx_hash[2:]

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.eth.getbalance(not self.eth.ERC20)
        return self.transfer_inclfee(all_amount, to_account, fee_priority)
