#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW ETH wallet with RPC API REST
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

from cryptolib.cryptography import public_key_recover, decompress_pubkey, sha2, sha3
from cryptolib.coins.ethereum import rlp_encode, int2bytearray, uint256, read_string
from wallets.wallets_utils import shift_10, compare_eth_addresses, InvalidOption, NotEnoughTokens
from wallets.ETHtokens import tokens_values, ledger_tokens
from wallets.typed_data_hash import typed_sign_hash, print_text_query
from pyweb3 import Web3Client
from pywalletconnect import WCClient, WCClientInvalidOption, WCClientException


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


MESSAGE_HEADER = b"\x19Ethereum Signed Message:\n"
EIP712_HEADER = b"\x19\x01"

USER_SCREEN = (
    "\n>> !!!  Once approved, check on your device screen to confirm the signature  !!! <<"
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
    if has_checksum(eth_addr):
        return checksum_address(eth_addr)
    return True


class ETHwalletCore:
    def __init__(self, pubkey, network, api, chainID, ERC20=None):
        self.pubkey = decompress_pubkey(pubkey)
        key_hash = sha3(self.pubkey[1:])
        self.address = format_checksum_address(key_hash.hex()[-40:])
        self.ERC20 = ERC20
        self.api = api
        self.decimals = self.get_decimals()
        self.token_symbol = self.get_symbol()
        self.chainID = chainID

    def getbalance(self, native=True):
        block_state = "latest"
        if native:
            # ETH native balance
            return self.api.get_balance(f"0x{self.address}", block_state)
        # ERC20 token balance
        balraw = self.api.call(
            self.ERC20,
            BALANCEOF_FUNCTION,
            f"000000000000000000000000{self.address}",
            block_state,
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
        value in wei, gprice in Wei
        """
        if self.ERC20:
            maxspendable = self.getbalance(False)
            balance_eth = self.getbalance()
            if balance_eth < (gprice * glimit):
                raise NotEnoughTokens("Not enough native ETH funding for the tx fee")
        else:
            maxspendable = self.getbalance() - (gprice * glimit)
        if paymentvalue > maxspendable or paymentvalue < 0:
            if self.ERC20:
                sym = self.token_symbol
            else:
                sym = "native ETH"
            raise NotEnoughTokens(f"Not enough {sym} tokens for the tx")
        self.nonce = int2bytearray(self.getnonce())
        self.gasprice = int2bytearray(gprice)
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
        "Rinkeby",
        "Ropsten",
        "Kovan",
        "Goerli",
    ]

    wtypes = ["Standard", "ERC20", "WalletConnect"]

    derive_paths = [
        # mainnet
        [
            "m/44'/60'/{}'/0/{}",
        ],
        # testnets
        [
            "m/44'/1'/{}'/0/{}",
        ],
        [
            "m/44'/1'/{}'/0/{}",
        ],
        [
            "m/44'/1'/{}'/0/{}",
        ],
        [
            "m/44'/1'/{}'/0/{}",
        ],
    ]

    # ETH wallet type 1 and 2 have option
    user_options = [1, 2]
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
    ]

    GAZ_LIMIT_SIMPLE_TX = 21000
    GAZ_LIMIT_ERC_20_TX = 180000

    def __init__(
        self, network, wtype, device, contract_addr=None, wc_uri=None, confirm_callback=None
    ):
        self.network = self.networks[network].lower()
        if self.network == "mainnet":
            self.chainID = 1
        if self.network == "ropsten":
            self.chainID = 3
        if self.network == "rinkeby":
            self.chainID = 4
        if self.network == "goerli":
            self.chainID = 5
        if self.network == "kovan":
            self.chainID = 42
        INFURA_KEY = "xxx"  # Put your Infura key here
        if INFURA_KEY == "xxx" and self.network != "mainnet":
            raise Exception(
                "To use Uniblow from source with an Ethereum testnet, bring your own Infura key."
            )
        if self.network == "mainnet":
            rpc_endpoint = "https://cloudflare-eth.com/"
            self.explorer = "https://etherscan.io/address/0x"
        else:
            rpc_endpoint = f"https://{self.network}.infura.io/v3/{INFURA_KEY}"
            self.explorer = f"https://{self.network}.etherscan.io/address/0x"
        if INFURA_KEY != "xxx" and self.network == "mainnet":
            # If an Infura key is provided, also use it for mainnet
            rpc_endpoint = f"https://{self.network}.infura.io/v3/{INFURA_KEY}"
        self.load_base(rpc_endpoint, device, contract_addr, wc_uri, confirm_callback)
        self.ledger_tokens = ledger_tokens

    def load_base(self, rpc_endpoint, device, contract_addr, wc_uri, confirm_callback):
        """Finish initialization, second part common for all chains"""
        self.current_device = device
        self.confirm_callback = confirm_callback
        pubkey_hex = self.current_device.get_public_key()

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
            pubkey_hex,
            self.network,
            Web3Client(rpc_endpoint, "Uniblow/1"),
            self.chainID,
            contract_addr_str,
        )
        if contract_addr_str is not None:
            self.coin = self.eth.token_symbol
        if wc_uri is not None:
            WCClient.set_wallet_metadata(WALLET_DESCR)
            WCClient.set_project_id(WALLETCONNECT_PROJID)
            try:
                self.wc_client = WCClient.from_wc_uri(wc_uri)
                req_id, req_chain_id, request_info = self.wc_client.open_session()
            except (WCClientInvalidOption, WCClientException) as exc:
                if hasattr(self, "wc_client"):
                    self.wc_client.close()
                raise InvalidOption(exc)
            request_message = (
                "WalletConnect request from :\n\n"
                f"{request_info['name']}\n\n"
                f"website   : {request_info['url']}\n"
                f"Relay URL : {self.wc_client.get_relay_url()}\n"
            )
            approve = self.confirm_callback(request_message)
            if approve:
                self.wc_client.reply_session_request(req_id, self.chainID, self.get_account())
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
            if method == "wc_sessionUpdate":
                if parameters[0].get("approved") is False:
                    raise Exception("Disconnected by the web app service.")
            if method == "wc_sessionDelete":
                if parameters.get("reason"):
                    raise Exception(
                        "Disconnected by the web app service.\n"
                        f"Reason : {parameters['reason']['message']}"
                    )
            elif method == "personal_sign":
                if compare_eth_addresses(parameters[1], self.get_account()):
                    signature = self.process_sign_message(parameters[0])
                    if signature is not None:
                        self.wc_client.reply(id_request, f"0x{signature.hex()}")
            elif method == "eth_sign":
                if compare_eth_addresses(parameters[0], self.get_account()):
                    signature = self.process_sign_message(parameters[1])
                    if signature is not None:
                        self.wc_client.reply(id_request, f"0x{signature.hex()}")
            elif method == "eth_signTypedData":
                if compare_eth_addresses(parameters[0], self.get_account()):
                    signature = self.process_sign_typeddata(parameters[1])
                    if signature is not None:
                        self.wc_client.reply(id_request, f"0x{signature.hex()}")
            elif method == "eth_sendTransaction":
                # sign and sendRaw
                tx_obj_tosign = parameters[0]
                if compare_eth_addresses(tx_obj_tosign["from"], self.get_account()):
                    tx_signed = self.process_signtransaction(tx_obj_tosign)
                    if tx_signed is not None:
                        tx_hash = self.broadcast_tx(tx_signed)
                        self.wc_client.reply(id_request, tx_hash)
            elif method == "eth_signTransaction":
                tx_obj_tosign = parameters[0]
                if compare_eth_addresses(tx_obj_tosign["from"], self.get_account()):
                    tx_signed = self.process_signtransaction(tx_obj_tosign)
                    if tx_signed is not None:
                        self.wc_client.reply(id_request, f"0x{tx_signed}")
            elif method == "eth_sendRawTransaction":
                tx_data = parameters[0]
                tx_hash = self.broadcast_tx(tx_data)
                self.wc_client.reply(id_request, tx_hash)
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
        explorer_url = f"{self.explorer}{self.eth.address}"
        if self.eth.ERC20:
            explorer_url += "#tokentxns"
        return explorer_url

    def build_tx(self, amount, gazprice, ethgazlimit, account, data=None):
        """Build and sign a transaction.
        Used to transfer tokens native or ERC20 with the given parameters.
        """
        if data is None:
            data = bytearray(b"")
        tx_bin, hash_to_sign = self.eth.prepare(account, amount, gazprice, ethgazlimit, data)
        if self.current_device.has_screen:
            if self.eth.ERC20 and self.current_device.ledger_tokens_compat:
                # Token known by Ledger ?
                ledger_info = self.ledger_tokens.get(self.eth.ERC20)
                if ledger_info:
                    # Known token : provide the trusted info to the device
                    name = ledger_info["ticker"]
                    data_sig = ledger_info["signature"]
                    self.current_device.register_token(
                        name, self.eth.ERC20[2:], self.eth.decimals, self.chainID, data_sig
                    )
            vrs = self.current_device.sign(tx_bin)
            return self.eth.add_vrs(vrs)
        else:
            tx_signature = self.current_device.sign(hash_to_sign)
            return self.eth.add_signature(tx_signature)

    def broadcast_tx(self, txdata):
        """Broadcast and return the tx hash as 0xhhhhhhhh"""
        return self.eth.send(txdata)

    def process_sign_message(self, data_hex):
        """Process a WalletConnect personal_sign and eth_sign call"""
        # sign(keccak256("\x19Ethereum Signed Message:\n" + len(message) + message)))
        data_bin = bytes.fromhex(data_hex[2:])
        msg_header = MESSAGE_HEADER + str(len(data_bin)).encode("ascii")
        sign_request = (
            "WalletConnect signature request :\n\n"
            f"- Data to sign (hex) :\n"
            f"- {data_hex}\n"
            f"\n Data to sign (ASCII/UTF8) :\n"
            f" {data_bin.decode('utf8')}\n"
        )
        if self.current_device.has_screen:
            hash2_data = sha2(data_bin).hex().upper()
            sign_request += f"\n Hash data to sign (hex) :\n {hash2_data}\n"
            sign_request += USER_SCREEN
        if self.confirm_callback(sign_request):
            if self.current_device.has_screen:
                v, r, s = self.current_device.sign_message(data_bin)
                return self.eth.encode_vrs(v, r, s)
            # else
            hash_sign = sha3(msg_header + data_bin)
            der_signature = self.current_device.sign(hash_sign)
            return self.eth.encode_datasign(hash_sign, der_signature)

    def process_sign_typeddata(self, data_bin):
        """Process a WalletConnect eth_signTypedData call"""
        data_obj = json.loads(data_bin)
        hash_domain, hash_data = typed_sign_hash(data_obj, self.chainID)
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
            sign_request += USER_SCREEN
        if self.confirm_callback(sign_request):
            if self.current_device.has_screen:
                v, r, s = self.current_device.sign_eip712(hash_domain, hash_data)
                return self.eth.encode_vrs(v, r, s)
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
        gas_limit = txdata.get("gas", 90000)
        if gas_limit != 90000:
            gas_limit = int(gas_limit, 16)
        request_message = (
            "WalletConnect transaction request :\n\n"
            f" To    :  0x{to_addr}\n"
            f" Value :  {value / (10 ** self.eth.decimals)} {self.coin}\n"
            f" Gas price  : {gas_price / GWEI_UNIT} Gwei\n"
            f" Gas limit  : {gas_limit}\n"
            f"Max fee cost: {gas_limit*gas_price / (10 ** self.eth.decimals)} {self.coin}\n"
        )
        if self.current_device.has_screen:
            sign_request += USER_SCREEN
        if self.confirm_callback(request_message):
            data_hex = txdata.get("data", "0x")
            data = bytearray.fromhex(data_hex[2:])
            return self.build_tx(value, gas_price, gas_limit, to_addr, data)

    def transfer(self, amount, to_account, fee_priority):
        # Transfer x unit to an account, pay
        if self.eth.ERC20:
            gazlimit = ETH_wallet.GAZ_LIMIT_ERC_20_TX
        else:
            gazlimit = ETH_wallet.GAZ_LIMIT_SIMPLE_TX
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
            Exception("fee_priority must be 0, 1 or 2 (slow, normal, fast)")
        tx_data = self.build_tx(
            shift_10(amount, self.eth.decimals), gaz_price, gazlimit, to_account
        )
        return "\nDONE, txID : " + self.broadcast_tx(tx_data)

    def transfer_inclfee(self, amount, to_account, fee_priority):
        # Transfer the amount in base unit minus fee, like the receiver paying the fee
        if self.eth.ERC20:
            gazlimit = ETH_wallet.GAZ_LIMIT_ERC_20_TX
        else:
            gazlimit = ETH_wallet.GAZ_LIMIT_SIMPLE_TX
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
            Exception("fee_priority must be 0, 1 or 2 (slow, normal, fast)")
        if self.eth.ERC20:
            fee = 0
        else:
            fee = int(gazlimit * gaz_price)
        tx_data = self.build_tx(amount - fee, gaz_price, gazlimit, to_account)
        return "\nDONE, txID : " + self.broadcast_tx(tx_data)

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.eth.getbalance(not self.eth.ERC20)
        return self.transfer_inclfee(all_amount, to_account, fee_priority)
