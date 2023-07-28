#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW ETH wallet with RPC API REST
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
from logging import getLogger
from textwrap import fill

from pyweb3 import Web3Client
from pywalletconnect import WCClient, WCClientInvalidOption, WCClientException

from cryptolib.cryptography import public_key_recover, sha2, sha3
from cryptolib.coins.ethereum import rlp_encode, int2bytearray, uint256, read_string
from wallets.name_service import resolve
from wallets.wallets_utils import (
    shift_10,
    balance_string,
    compare_eth_addresses,
    InvalidOption,
    NotEnoughTokens,
)
from wallets.ETHtokens import tokens_values, nfts_values, ledger_tokens
from wallets.typed_data_hash import typed_sign_hash, print_text_query


ETH_DECIMALS = 18
GWEI_DECIMALS = 9


logger = getLogger(__name__)


# ERC20 functions codes
#   balanceOf(address)
BALANCEOF_FUNCTION = "70a08231"
#   decimals()
DECIMALS_FUNCTION = "313ce567"
#   symbol()
SYMBOL_FUNCTION = "95d89b41"
#   transfer(address,uint256)
TRANSFER_FUNCTION = "a9059cbb"
#   safeTransferFrom(address,address,uint256)
SAFETRANSFER_FUNCTION = "42842e0e"


MESSAGE_HEADER = b"\x19Ethereum Signed Message:\n"
EIP712_HEADER = b"\x19\x01"

USER_SCREEN = (
    "\n>> !!!  Once approved, check on your {check_type} to confirm the signature  !!! <<"
)
USER_BUTTON = (
    "\n>> !!!  Once approved, press the button on the device to confirm the signature  !!! <<"
)

WALLETCONNECT_PROJID = "5af34a5c60298f270f4281f8bae67f33"
WALLET_DESCR = {
    "description": "A universal blockchain wallet for cryptos",
    "url": "https://uniblow.org",
    "icons": ["https://uniblow.org/img/uniblow_logo.png"],
    "name": "Uniblow",
}

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
    if has_checksum(eth_addr) and not checksum_address(eth_addr):
        return False
    return f"0x{eth_addr}"


class ETHwalletCore:
    def __init__(self, pubkey, network, api, chainID, contract=None, is_fungible=True):
        self.pubkey = pubkey
        self.is_fungible = is_fungible
        key_hash = sha3(self.pubkey[1:])
        self.address = format_checksum_address(key_hash.hex()[-40:])
        self.contract = contract
        self.api = api
        self.decimals = self.get_decimals()
        self.token_symbol = self.get_symbol()
        self.chainID = chainID

    def call(self, method, data=""):
        """eth_call to the current contract"""
        return self.api.call(self.contract, method, data)

    def getbalance(self, native=True):
        if native:
            # ETH native balance
            return self.api.get_balance(f"0x{self.address}")
        # Token balance
        balraw = self.call(BALANCEOF_FUNCTION, f"000000000000000000000000{self.address}")
        if balraw == [] or balraw == "0x":
            return 0
        balance = int(balraw[2:], 16)
        return balance

    def get_decimals(self):
        if self.contract:
            if self.is_fungible:
                # ERC20
                balraw = self.call(DECIMALS_FUNCTION)
                if balraw == [] or balraw == "0x":
                    return 0
                return int(balraw[2:], 16)
            else:
                # NFT
                return 0
        return ETH_DECIMALS

    def get_symbol(self):
        if self.contract:
            balraw = self.call(SYMBOL_FUNCTION)
            if balraw == [] or balraw == "0x":
                return "---"
            return read_string(balraw)

    def getnonce(self):
        numtx = self.api.get_tx_num(self.address, "pending")
        return numtx

    def prepare(self, toaddr, paymentvalue, gprice, glimit, data=bytearray(b"")):
        """Build a transaction to be signed.
        toaddr in hex without 0x
        value in wei, gprice in Wei
        If NFT : paymentvalue is id
        """
        if self.contract:
            maxspendable = self.getbalance(False)
            balance_eth = self.getbalance()
            if balance_eth < (gprice * glimit):
                raise NotEnoughTokens("Not enough native gas for the tx fee.")
        else:
            maxspendable = self.getbalance() - (gprice * glimit)
        if self.is_fungible:
            if paymentvalue > maxspendable or paymentvalue < 0:
                if self.contract:
                    sym = self.token_symbol
                else:
                    sym = "native gas"
                raise NotEnoughTokens(f"Not enough {sym} tokens for the tx.")
        else:
            # NFT
            # For now, dont test whether the exact id is owned
            if maxspendable < 1:
                raise NotEnoughTokens("You have no NFT for the tx.")
        self.nonce = int2bytearray(self.getnonce())
        self.gasprice = int2bytearray(gprice)
        self.startgas = int2bytearray(glimit)
        if self.contract:
            self.to = bytearray.fromhex(self.contract[2:])
            self.value = int2bytearray(int(0))
            if self.is_fungible:
                # ERC20
                self.data = bytearray.fromhex(TRANSFER_FUNCTION + "00" * 12 + toaddr) + uint256(
                    paymentvalue
                )
            else:
                # NFT
                self.data = (
                    bytearray.fromhex(SAFETRANSFER_FUNCTION + "00" * 12 + self.address)
                    + bytearray.fromhex("00" * 12 + toaddr)
                    + uint256(paymentvalue)
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
        return (signing_tx, self.datahash)

    def add_signature(self, signature_der):
        """Add a DER signature into the built transaction."""
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

    def add_vrs_satochip(self, vrs):
        v_int = vrs[0] + 35 + 2*self.chainID #EIP155
        logger.debug(f"v_int: {v_int}")
        v = int2bytearray(v_int)
        r = int2bytearray(vrs[1])
        s = int2bytearray(vrs[2])
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
        logger.debug(f"tx_final: {tx_final.hex()}")
        return tx_final.hex()

    def add_vrs(self, vrs):
        # v from Ledger hardware device is only the 8 bits LSB
        v_high = self.chainID >> 7
        v = int2bytearray(256 * v_high + vrs[0])
        r = int2bytearray(vrs[1])
        s = int2bytearray(vrs[2])
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

    def encode_datasign(self, datahash, signature_der):
        """Encode a message signature from the DER sig."""
        # Signature decoding
        lenr = int(signature_der[3])
        lens = int(signature_der[5 + lenr])
        r = int.from_bytes(signature_der[4 : lenr + 4], "big")
        s = int.from_bytes(signature_der[lenr + 6 : lenr + 6 + lens], "big")
        # Parity recovery
        v = 27
        h = int.from_bytes(datahash, "big")
        if public_key_recover(h, r, s, v) != self.pubkey:
            v += 1
        # Signature encoding
        return uint256(r) + uint256(s) + bytes([v])

    def encode_vrs(self, v, r, s):
        """Encode a message signature from vrs integers."""
        return uint256(r) + uint256(s) + bytes([v])

    def send(self, tx_hex):
        """Upload the tx"""
        return self.api.pushtx(tx_hex)


class ETH_wallet:
    coin = "ETH"

    networks = [
        "Mainnet",
        "Goerli",
        "Sepolia",
    ]

    wtypes = ["Standard", "ERC20", "WalletConnect", "NFT"]

    derive_paths = [
        # mainnet
        [
            "m/44'/60'/{}'/0/{}",
        ],
        # testnets
        [
            "m/44'/60'/{}'/0/{}", #"m/44'/1'/{}'/0/{}",
        ],
        [
            "m/44'/60'/{}'/0/{}", #"m/44'/1'/{}'/0/{}",
        ],
    ]

    # ETH wallet type 1 and 2 have option
    user_options = [1, 2, 3]
    # self.__init__ ( option_name = "user input option" )
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
        {
            "option_name": "contract_addr",
            "prompt": "ERC721 contract address",
            "preset": nfts_values,
        },
    ]

    GAZ_LIMIT_SIMPLE_TX = 21000
    GAZ_LIMIT_ERC_20_TX = 180000

    def __init__(
        self, network, wtype, device, contract_addr=None, wc_uri=None, confirm_callback=None
    ):
        self.network = self.networks[network].lower()
        if self.network == "mainnet":
            self.chainID = 1
            rpc_endpoint = "https://rpc.ankr.com/eth/"
            self.explorer = "https://etherscan.io/address/0x"
        elif self.network == "goerli":
            self.chainID = 5
            rpc_endpoint = "https://rpc.ankr.com/eth_goerli"
            self.explorer = f"https://{self.network}.etherscan.io/address/0x"
        elif self.network == "sepolia":
            self.chainID = 11155111
            rpc_endpoint = "https://rpc.sepolia.org"
            self.explorer = "https://sepolia.etherscan.io/address/0x"
        else:
            raise InvalidOption("Invalid network name.")
        self.load_base(rpc_endpoint, device, contract_addr, wc_uri, confirm_callback, wtype != 3)
        self.ledger_tokens = ledger_tokens

    def load_base(self, rpc_endpoint, device, contract_addr, wc_uri, confirm_callback, fungible):
        """Finish initialization, second part common for all chains"""
        self.current_device = device
        self.confirm_callback = confirm_callback
        pubkey = self.current_device.get_public_key()

        if contract_addr is not None:
            if not testaddr(contract_addr):
                raise InvalidOption(
                    "Invalid contract address format :\nshould be 0x/40hex/ or /40hex/"
                )
            contract_addr_str = contract_addr.lower()
            if len(contract_addr_str) == 40:
                contract_addr_str = "0x" + contract_addr_str
        else:
            contract_addr_str = None
        self.eth = ETHwalletCore(
            pubkey,
            self.network,
            Web3Client(rpc_endpoint, "Uniblow/2"),
            self.chainID,
            contract_addr_str,
            fungible,
        )
        if contract_addr_str is not None:
            self.coin = self.eth.token_symbol
        if wc_uri is not None:
            WCClient.set_wallet_metadata(WALLET_DESCR)
            WCClient.set_project_id(WALLETCONNECT_PROJID)
            WCClient.set_origin("https://uniblow.org")
            try:
                self.wc_client = WCClient.from_wc_uri(wc_uri)
                req_id, req_chain_id, request_info = self.wc_client.open_session()
            except (WCClientInvalidOption, WCClientException) as exc:
                if hasattr(self, "wc_client"):
                    self.wc_client.close()
                raise InvalidOption(exc)
            relay = self.wc_client.get_relay_url()
            request_message = (
                "WalletConnect request from :\n\n"
                f"{request_info['name']}\n\n"
                f"website  :  {request_info['url']}\n"
            )
            if relay:
                request_message += f"Relay URL : {relay}\n"
            approve = self.confirm_callback(request_message)
            if approve:
                self.wc_client.reply_session_request(req_id, self.chainID, self.get_account())
            else:
                self.wc_client.reject_session_request(req_id)
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

    def get_account(self):
        # Read address to fund the wallet
        return f"0x{self.eth.address}"

    # Process messages for WalletConnect
    # Get messages more often than balance
    def get_messages(self):
        # wc_message : (id, method, params) or (None, "", [])
        wc_message = self.wc_client.get_message()
        while wc_message[0] is not None:
            id_request = wc_message[0]
            method = wc_message[1]
            parameters = wc_message[2]
            logger.debug(
                "WC request id: %s, method: %s, params: %s", id_request, method, parameters
            )
            if method == "wc_sessionRequest" or method == "wc_sessionPayload":
                # Read if WCv2 and extract to v1 format
                logger.debug("WCv2 request")
                if parameters.get("request"):
                    logger.debug("request decoding")
                    method = parameters["request"].get("method")
                    parameters = parameters["request"].get("params")
                    logger.debug("Actual method: %s, params: %s", method, parameters)
            if method == "wc_sessionUpdate":
                if parameters[0].get("approved") is False:
                    raise Exception("Disconnected by the web app service.")
            if method == "wc_sessionDelete":
                if parameters.get("reason"):
                    raise Exception(
                        "Disconnected by the web app service.\n"
                        f"Reason : {parameters['reason']['message']}"
                    )
                if parameters.get("message"):
                    raise Exception(
                        "Disconnected by the web app service.\n" f"Reason : {parameters['message']}"
                    )
            elif method == "personal_sign" and len(parameters) > 1:
                if compare_eth_addresses(parameters[1], self.get_account()):
                    signature = self.process_sign_message(parameters[0])
                    if signature is not None:
                        self.wc_client.reply(id_request, f"0x{signature.hex()}")
                    else:
                        self.wc_client.reject(id_request)
            elif method == "eth_sign" and len(parameters) > 1:
                if compare_eth_addresses(parameters[0], self.get_account()):
                    signature = self.process_sign_message(parameters[1])
                    if signature is not None:
                        self.wc_client.reply(id_request, f"0x{signature.hex()}")
                    else:
                        self.wc_client.reject(id_request)
            elif method == "eth_signTypedData" and len(parameters) > 1:
                if compare_eth_addresses(parameters[0], self.get_account()):
                    signature = self.process_sign_typeddata(parameters[1])
                    if signature is not None:
                        self.wc_client.reply(id_request, f"0x{signature.hex()}")
                    else:
                        self.wc_client.reject(id_request)
            elif method == "eth_sendTransaction" and len(parameters) > 0:
                # sign and sendRaw
                tx_obj_tosign = parameters[0]
                if compare_eth_addresses(tx_obj_tosign["from"], self.get_account()):
                    tx_signed = self.process_signtransaction(tx_obj_tosign)
                    if tx_signed is not None:
                        tx_hash = self.broadcast_tx(tx_signed)
                        self.wc_client.reply(id_request, tx_hash)
                    else:
                        self.wc_client.reject(id_request)
            elif method == "eth_signTransaction" and len(parameters) > 0:
                tx_obj_tosign = parameters[0]
                if compare_eth_addresses(tx_obj_tosign["from"], self.get_account()):
                    tx_signed = self.process_signtransaction(tx_obj_tosign)
                    if tx_signed is not None:
                        self.wc_client.reply(id_request, f"0x{tx_signed}")
                    else:
                        self.wc_client.reject(id_request)
            elif method == "eth_sendRawTransaction" and len(parameters) > 0:
                tx_data = parameters[0]
                tx_hash = self.broadcast_tx(tx_data)
                self.wc_client.reply(id_request, tx_hash)
            logger.debug("WC command processing finished, now reading next available message.")
            wc_message = self.wc_client.get_message()

    def get_balance(self):
        # Get balance in base integer unit and return string with unit
        return (
            balance_string(self.eth.getbalance(not self.eth.contract), self.eth.decimals)[:20]
            + " "
            + self.coin
        )

    def check_address(self, addr_str):
        # Check if address or domain is valid
        resolved = resolve(addr_str, self.coin, self.eth.contract, self.__class__.coin)
        if not resolved:
            resolved = resolve(addr_str, ETH_wallet.coin)
        if resolved:
            addr_str = resolved
        return testaddr(addr_str)

    def history(self):
        # Get history page
        explorer_url = f"{self.explorer}{self.eth.address}"
        if self.eth.contract:
            explorer_url += "#tokentxns"
        return explorer_url

    # def build_tx_old(self, amount, gazprice, ethgazlimit, account, data=None):
    #     """Build and sign a transaction.
    #     Used to transfer tokens with the given parameters.
    #     amount is id when NFT.
    #     """
    #     if data is None:
    #         data = bytearray(b"")
    #     tx_bin, hash_to_sign = self.eth.prepare(account, amount, gazprice, ethgazlimit, data)
    #     if self.current_device.device_name == "Satochip":
    #         vrs = self.current_device.sign(tx_bin)
    #         logger.debug(f"vrs: {vrs}")
    #         return self.eth.add_vrs_satochip(vrs)
    #     elif self.current_device.has_screen:
    #         if self.eth.contract and self.current_device.ledger_tokens_compat:
    #             # Token known by Ledger ?
    #             ledger_info = self.ledger_tokens.get(self.eth.contract.lower())
    #             if ledger_info:
    #                 # Known token : provide the trusted info to the device
    #                 name = ledger_info["ticker"]
    #                 data_sig = ledger_info["signature"]
    #                 self.current_device.register_token(
    #                     name, self.eth.contract[2:], self.eth.decimals, self.chainID, data_sig
    #                 )
    #         vrs = self.current_device.sign(tx_bin)
    #         return self.eth.add_vrs(vrs)
    #     tx_signature = self.current_device.sign(hash_to_sign)
    #     return self.eth.add_signature(tx_signature)

    def build_tx(self, amount, gazprice, ethgazlimit, account, data=None):
        """Build and sign a transaction.
        Used to transfer tokens with the given parameters.
        amount is id when NFT.
        """
        if data is None:
            data = bytearray(b"")
        tx_bin, hash_to_sign = self.eth.prepare(account, amount, gazprice, ethgazlimit, data)
        if self.current_device.has_screen:

            if self.eth.contract and self.current_device.ledger_tokens_compat:
                # Token known by Ledger ?
                ledger_info = self.ledger_tokens.get(self.eth.contract.lower())
                if ledger_info:
                    # Known token : provide the trusted info to the device
                    name = ledger_info["ticker"]
                    data_sig = ledger_info["signature"]
                    self.current_device.register_token(
                        name, self.eth.contract[2:], self.eth.decimals, self.chainID, data_sig
                    )
            tx_signature = self.current_device.sign(tx_bin)
        else:
            tx_signature = self.current_device.sign(hash_to_sign)
        if self.current_device.provide_parity:
            tx_signed = self.eth.add_vrs(tx_signature)
        else:
            tx_signed = self.eth.add_signature(tx_signature)
        return tx_signed

    def broadcast_tx(self, txdata):
        """Broadcast and return the tx hash as 0xhhhhhhhh"""
        return self.eth.send(txdata)

    # def process_sign_message(self, data_hex):
    #     """Process a WalletConnect personal_sign and eth_sign call"""
    #     # sign(keccak256("\x19Ethereum Signed Message:\n" + len(message) + message)))
    #     data_bin = bytes.fromhex(data_hex[2:])
    #     msg_header = MESSAGE_HEADER + str(len(data_bin)).encode("ascii")
    #     sign_request = (
    #         "WalletConnect signature request :\n\n"
    #         f"- Data to sign (hex) :\n"
    #         f"- {fill(data_hex)}\n"
    #         f"\n Data to sign (ASCII/UTF8) :\n"
    #     )
    #     try:
    #         sign_request += f" {fill(data_bin.decode('utf8'))}\n"
    #     except UnicodeDecodeError:
    #         sign_request += " <can't decode sign data to text>"
    #     if self.current_device.has_screen:
    #         hash2_data = sha2(data_bin).hex().upper()
    #         sign_request += f"\n Hash data to sign (hex) :\n {hash2_data}\n"
    #         sign_request += USER_SCREEN
    #     elif self.current_device.has_hardware_button:
    #         sign_request += USER_BUTTON
    #     if self.confirm_callback(sign_request):
    #         if self.current_device.has_screen:
    #             v, r, s = self.current_device.sign_message(data_bin)
    #             return self.eth.encode_vrs(v, r, s)
    #         # else
    #         hash_sign = sha3(msg_header + data_bin)
    #         der_signature = self.current_device.sign(hash_sign)
    #         return self.eth.encode_datasign(hash_sign, der_signature)

    def process_sign_message(self, data_hex):
        """Process a WalletConnect personal_sign and eth_sign call"""
        # sign(keccak256("\x19Ethereum Signed Message:\n" + len(message) + message)))
        data_bin = bytes.fromhex(data_hex[2:])
        msg_header = MESSAGE_HEADER + str(len(data_bin)).encode("ascii")
        sign_request = (
            "WalletConnect signature request :\n\n"
            f"- Data to sign (hex) :\n"
            f"- {fill(data_hex)}\n"
            f"\n Data to sign (ASCII/UTF8) :\n"
        )
        try:
            sign_request += f" {fill(data_bin.decode('utf8'))}\n"
        except UnicodeDecodeError:
            sign_request += " <can't decode sign data to text>"
        if self.current_device.has_screen:
            hash2_data = sha2(data_bin).hex().upper()
            sign_request += f"\n Hash data to sign (hex) :\n {hash2_data}\n"
            sign_request += USER_SCREEN.format(check_type=self.current_device.on_device_check_type)
        elif self.current_device.has_hardware_button:
            sign_request += USER_BUTTON
        if self.confirm_callback(sign_request):
            if self.current_device.has_screen:
                if self.current_device.provide_parity: 
                    v, r, s = self.current_device.sign_message(data_bin)
                    return self.eth.encode_vrs(v, r, s)
                else:
                    hash_sign = sha3(msg_header + data_bin)
                    der_signature = self.current_device.sign(data_bin)
                    return self.eth.encode_datasign(hash_sign, der_signature)
            else:
                hash_sign = sha3(msg_header + data_bin)
                der_signature = self.current_device.sign(hash_sign)
                return self.eth.encode_datasign(hash_sign, der_signature)

    # def process_sign_typeddata(self, data_bin):
    #     """Process a WalletConnect eth_signTypedData call"""
    #     data_obj = json.loads(data_bin)
    #     chain_id = None
    #     if "domain" in data_obj and "chainId" in data_obj["domain"]:
    #         chain_id = data_obj["domain"]["chainId"]
    #         if isinstance(chain_id, str) and chain_id.startswith("eip155:"):
    #             chain_id = int(chain_id[7:])
    #     # Silent ignore when chain ids mismatch
    #     if chain_id is not None and self.chainID != data_obj["domain"]["chainId"]:
    #         logger.debug("Wrong chain id in signedTypedData")
    #         return None
    #         #return self.eth.encode_vrs(0,0,0) # send dummy signature ?
    #     hash_domain, hash_data = typed_sign_hash(data_obj)
    #     sign_request = (
    #         "WalletConnect signature request :\n\n"
    #         f"- Data to sign (typed) :\n"
    #         f"{print_text_query(data_obj)}"
    #         f"\n - Hash domain (hex) :\n"
    #         f" 0x{hash_domain.hex().upper()}\n"
    #         f"\n - Hash data (hex) :\n"
    #         f" 0x{hash_data.hex().upper()}\n"
    #     )
    #     if self.current_device.has_screen:
    #         sign_request += USER_SCREEN
    #     elif self.current_device.has_hardware_button:
    #         sign_request += USER_BUTTON
    #     if self.confirm_callback(sign_request):
    #         logger.debug(f"type(current_device): {type(self.current_device)}")
    #         if self.current_device.device_name == "Satochip":
    #             v, r, s = self.current_device.sign_eip712(data_obj)
    #             return self.eth.encode_vrs(v, r, s)
    #         elif self.current_device.has_screen:
    #             v, r, s = self.current_device.sign_eip712(hash_domain, hash_data)
    #             return self.eth.encode_vrs(v, r, s)
    #         # else
    #         hash_sign = sha3(EIP712_HEADER + hash_domain + hash_data)
    #         der_signature = self.current_device.sign(hash_sign)
    #         return self.eth.encode_datasign(hash_sign, der_signature)

    def process_sign_typeddata(self, data_bin):
        """Process a WalletConnect eth_signTypedData call"""
        data_obj = json.loads(data_bin)
        chain_id = None
        if "domain" in data_obj and "chainId" in data_obj["domain"]:
            chain_id = data_obj["domain"]["chainId"]
            if isinstance(chain_id, str) and chain_id.startswith("eip155:"):
                chain_id = int(chain_id[7:])
        # Send user rejected when chain ids mismatch
        if chain_id is not None and self.chainID != data_obj["domain"]["chainId"]:
            logger.debug("Wrong chain id in signedTypedData")
            return None
            #return self.eth.encode_vrs(0,0,0) # send dummy signature ?
        hash_domain, hash_data = typed_sign_hash(data_obj)
        sign_request = (
            "WalletConnect signature request :\n\n"
            f"- Data to sign (typed) :\n"
            f"{print_text_query(data_obj)}"
            f"\n - Hash domain (hex) :\n"
            f" 0x{hash_domain.hex().upper()}\n"
            f"\n - Hash data (hex) :\n"
            f" 0x{hash_data.hex().upper()}\n"
        )
        if self.current_device.has_screen:
            sign_request += USER_SCREEN.format(check_type=self.current_device.on_device_check_type)
        elif self.current_device.has_hardware_button:
            sign_request += USER_BUTTON
        if self.confirm_callback(sign_request):
            logger.debug(f"type(current_device): {type(self.current_device)}")
            
            if self.current_device.has_screen:
                if self.current_device.provide_parity:
                    v, r, s = self.current_device.sign_eip712(hash_domain, hash_data)
                    return self.eth.encode_vrs(v, r, s)
                else:
                    hash_sign = sha3(EIP712_HEADER + hash_domain + hash_data)
                    der_signature = self.current_device.sign_eip712(data_obj)
                    return self.eth.encode_datasign(hash_sign, der_signature)
            # else
            hash_sign = sha3(EIP712_HEADER + hash_domain + hash_data)
            der_signature = self.current_device.sign(hash_sign)
            return self.eth.encode_datasign(hash_sign, der_signature)

    def process_signtransaction(self, txdata):
        """Build a signed tx, for WalletConnect eth_sendTransaction and eth_signTransaction call"""
        to_addr = txdata.get("to", "  New contract")[2:]
        value = txdata.get("value", 0)
        if value != 0:
            value = int(value, 16)
        gas_price = txdata.get("gasPrice", 0)
        if gas_price != 0:
            gas_price = int(gas_price, 16)
        else:
            gas_price = self.eth.api.get_gasprice()
        gas_limit = txdata.get("gas", ETH_wallet.GAZ_LIMIT_ERC_20_TX)
        if gas_limit != ETH_wallet.GAZ_LIMIT_ERC_20_TX:
            gas_limit = int(gas_limit, 16)
        request_message = (
            "WalletConnect transaction request :\n\n"
            f" To    :  0x{to_addr}\n"
            f" Value :  {balance_string(value , self.eth.decimals)} {self.coin}\n"
            f" Gas price  : {balance_string(gas_price, GWEI_DECIMALS)} Gwei\n"
            f" Gas limit  : {gas_limit}\n"
            f"Max fee cost: {balance_string(gas_limit*gas_price, self.eth.decimals)} {self.coin}\n"
        )
        if self.current_device.has_screen:
            request_message += USER_SCREEN.format(check_type=self.current_device.on_device_check_type)
        elif self.current_device.has_hardware_button:
            request_message += USER_BUTTON
        if self.confirm_callback(request_message):
            data_hex = txdata.get("data", "0x")
            data = bytearray.fromhex(data_hex[2:])
            return self.build_tx(value, gas_price, gas_limit, to_addr, data)

    def transfer(self, amount, to_account, fee_priority):
        # Transfer x unit to an account, pay
        if self.eth.contract:
            gazlimit = ETH_wallet.GAZ_LIMIT_ERC_20_TX
            if self.chainID == 42161:
                # Arbitrum : provide 4x more gas
                gazlimit *= 4
        else:
            gazlimit = ETH_wallet.GAZ_LIMIT_SIMPLE_TX
            if self.chainID == 42161:
                # Arbitrum : provide 25x more gas
                gazlimit *= 25
        if to_account.startswith("0x"):
            to_account = to_account[2:]
        gaz_price = self.eth.api.get_gasprice()  # wei per gaz unit
        if fee_priority == 0:
            gaz_price = int(gaz_price * 0.9)
        elif fee_priority == 1:
            gaz_price = int(gaz_price * 1.1)
        elif fee_priority == 2:
            gaz_price = int(gaz_price * 1.6)
        else:
            raise Exception("fee_priority must be 0, 1 or 2 (slow, normal, fast)")
        tx_data = self.build_tx(
            shift_10(amount, self.eth.decimals), gaz_price, gazlimit, to_account
        )
        return "\nDONE, txID : " + self.broadcast_tx(tx_data)

    def transfer_nft(self, id, to_account):
        # SafeTransfer NFT id to an account
        gazlimit = ETH_wallet.GAZ_LIMIT_ERC_20_TX * 2
        if to_account.startswith("0x"):
            to_account = to_account[2:]
        gaz_price = self.eth.api.get_gasprice()  # wei per gaz unit
        gaz_price = int(gaz_price * 1.2)
        tx_data = self.build_tx(id, gaz_price, gazlimit, to_account)
        return self.broadcast_tx(tx_data)

    def transfer_inclfee(self, amount, to_account, fee_priority):
        # Transfer the amount in base unit minus fee, like the receiver paying the fee
        if self.eth.contract:
            gazlimit = ETH_wallet.GAZ_LIMIT_ERC_20_TX
            if self.chainID == 42161:
                # Arbitrum : provide 4x more gas
                gazlimit *= 4
        else:
            gazlimit = ETH_wallet.GAZ_LIMIT_SIMPLE_TX
            if self.chainID == 42161:
                # Arbitrum : provide 25x more gas
                gazlimit *= 25
        if to_account.startswith("0x"):
            to_account = to_account[2:]
        gaz_price = self.eth.api.get_gasprice()
        if fee_priority == 0:
            gaz_price = int(gaz_price * 0.9)
        elif fee_priority == 1:
            gaz_price = int(gaz_price * 1.1)
        elif fee_priority == 2:
            gaz_price = int(gaz_price * 1.6)
        else:
            raise Exception("fee_priority must be 0, 1 or 2 (slow, normal, fast)")
        if self.eth.contract:
            fee = 0
        else:
            fee = int(gazlimit * gaz_price)
        tx_data = self.build_tx(amount - fee, gaz_price, gazlimit, to_account)
        return "\nDONE, txID : " + self.broadcast_tx(tx_data)

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.eth.getbalance(not self.eth.contract)
        return self.transfer_inclfee(all_amount, to_account, fee_priority)
