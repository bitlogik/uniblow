#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW SOL wallet with with RPC
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

from wallets.name_service import resolve
from wallets.wallets_utils import balance_string, shift_10, NotEnoughTokens
from cryptolib.base58 import base58_to_bin, bin_to_base58
from cryptolib.uintEncode import uint8, uint32, uint64, encode_varuint


SOL_units = 9  # 1 SOL = 1 billion lamports
FEE_LEVEL = 5000  # 1 signature costs 5000 lamports

TRANSFER_INSTRUCTION_INDEX = 2
SYSTEM_ACCOUNT = "11111111111111111111111111111111"


def encode_instruction(instr_obj):
    """Serialize an instruction."""
    # Program ID index
    prog_idx = uint8(instr_obj["program_idx"])
    # Accounts indexes
    acct_idxs = encode_varuint(len(instr_obj["accounts_idx"]))
    acct_idxs += b"".join([uint8(actidx) for actidx in instr_obj["accounts_idx"]])
    # Data
    data = encode_varuint(len(instr_obj["data"])) + instr_obj["data"]
    return prog_idx + acct_idxs + data


def serialize_tx(tx_obj):
    """Serialize a transaction to binary."""
    # Encode transaction header
    # 1 sig required, 0 read-only signed account, 1 read-only unsigned account
    header = bytes([1, 0, 1])  # Hardcoded values
    # Encode accounts
    accounts = encode_varuint(len(tx_obj["accounts"]))
    accounts += b"".join([base58_to_bin(act) for act in tx_obj["accounts"]])
    # recent block hash
    block_hash = base58_to_bin(tx_obj["recentBlockhash"])
    # instructions
    instrs = encode_varuint(len(tx_obj["instructions"]))
    instrs += b"".join([encode_instruction(inst) for inst in tx_obj["instructions"]])
    return header + accounts + block_hash + instrs


def gen_instruction(prog_idx, acct_idxs, datains):
    """Generate an instruction object."""
    return {"program_idx": prog_idx, "accounts_idx": acct_idxs, "data": datains}


def gen_transfer_data(amount):
    """Generate the data instructions for a token transfer."""
    return uint32(TRANSFER_INSTRUCTION_INDEX) + uint64(amount)


def gen_transfer_transaction(from_account, to_account, amount, block_hash):
    """Generate a transaction for a token transfer."""
    return {
        "accounts": [from_account, to_account, SYSTEM_ACCOUNT],
        "recentBlockhash": block_hash,
        "instructions": [gen_instruction(2, [0, 1], gen_transfer_data(amount))],
    }


def add_signature(tx_bin, sig_bin):
    """Add a single signature to a serialized transaction."""
    return uint8(1) + sig_bin + tx_bin


class sol_api:
    def __init__(self, network):
        self.url = "https://api.mainnet-beta.solana.com/"
        if network.lower() != "mainnet":
            self.url = f"https://api.{network.lower()}.solana.com/"
        self.jsres = []

    def getData(self, method, params=None):
        if params is None:
            params = []
        if isinstance(params, str):
            params = [params]
        data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        try:
            req = urllib.request.Request(
                self.url,
                headers={"User-Agent": "Uniblow/2", "Content-Type": "application/json"},
                data=json.dumps(data).encode("utf-8"),
            )
            self.webrsc = urllib.request.urlopen(req)
            self.jsres = json.load(self.webrsc)
        except urllib.error.HTTPError as exc:
            strerr = exc.read()
            raise IOError(f"{exc.code}  :  {strerr.decode('utf8')}")
        except urllib.error.URLError as exc:
            raise IOError(exc)
        except Exception:
            raise IOError(f"Error while processing request:\n {self.url}  :  {method} ,  {params}")

    def checkapiresp(self):
        if "error" in self.jsres:
            print(" !! ERROR :")
            raise Exception(self.jsres["error"])
        if "errors" in self.jsres:
            print(" !! ERRORS :")
            raise Exception(self.jsres["errors"])

    def get_balance(self, addr):
        self.getData("getBalance", [addr])
        balance = int(self.getKey("result/value"))
        self.getData("getAccountInfo", [addr])
        return balance

    def get_recent_block_hash(self):
        self.getData("getRecentBlockhash")
        block_hash = self.getKey("result/value/blockhash")
        return block_hash

    def pushtx(self, txb58):
        self.getData("sendTransaction", [txb58])
        self.checkapiresp()
        return self.getKey("result")

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


def testaddr(sol_addr):
    # Safe reading of the address format
    if len(sol_addr) != 44:
        return False
    try:
        dec_b58 = base58_to_bin(sol_addr)
        if len(dec_b58) == 32:
            return sol_addr
    except ValueError:
        return False
    return False


class SOLwalletCore:
    def __init__(self, pubkey, network, api):
        self.address = bin_to_base58(pubkey)
        self.api = api
        self.decimals = self.get_decimals()

    def getbalance(self):
        return self.api.get_balance(self.address)

    def get_decimals(self):
        return SOL_units

    def get_recentBlockHash(self):
        blkhash = self.api.get_recent_block_hash()
        return blkhash

    def prepare(self, toaddr, paymentvalue):
        """Build a transaction to be signed.
        value in lamport
        """
        maxspendable = self.getbalance() - FEE_LEVEL
        if paymentvalue > maxspendable or paymentvalue < 0:
            sym = "native SOL"
            raise NotEnoughTokens(f"Not enough {sym} tokens for the tx")
        transaction = gen_transfer_transaction(
            self.address, toaddr, paymentvalue, self.get_recentBlockHash()
        )
        return serialize_tx(transaction)

    def add_signature(self, tx_bin, signature):
        """Add a signature into the built transaction."""
        return add_signature(tx_bin, signature)

    def send(self, tx_bin):
        """Upload the tx"""
        return self.api.pushtx(bin_to_base58(tx_bin))


class SOL_wallet:
    coin = "SOL"

    networks = [
        "Mainnet",
        "Testnet",
    ]

    wtypes = ["Standard"]

    derive_paths = [
        # mainnet
        [
            "m/44'/501'/{}'/{}",
        ],
        # testnet
        [
            "m/44'/1'/{}'/{}",
        ],
    ]

    # SOL wallet have no option
    user_options = []
    # self.__init__ ( option_name = "user input option" )
    options_data = []

    def __init__(
        self,
        network,
        wtype,
        device,
        contract_addr=None,
    ):
        self.network = SOL_wallet.networks[network].lower()
        self.current_device = device
        pubkey = self.current_device.get_public_key()
        self.sol = SOLwalletCore(pubkey, self.network, sol_api(self.network))

    @classmethod
    def get_networks(cls):
        return cls.networks

    @classmethod
    def get_account_types(cls):
        return cls.wtypes

    @classmethod
    def get_path(cls, network_name, wtype, legacy):
        return cls.derive_paths[network_name][0]

    @classmethod
    def get_key_type(cls, wtype):
        # No list, it's all Ed25519
        return "ED"

    def get_account(self):
        # Read address to fund the wallet
        return self.sol.address

    def get_balance(self):
        # Get balance in base integer unit
        return f"{balance_string(self.sol.getbalance(), self.sol.decimals)} {self.coin}"

    def check_address(self, addr_str):
        # Check if address or domain is valid
        resolved = resolve(addr_str, SOL_wallet.coin)
        if resolved:
            addr_str = resolved
        return testaddr(addr_str)

    def history(self):
        # Get history page
        SOL_EXPLORER_URL = f"https://explorer.solana.com/address/{self.sol.address}"
        if self.network != "mainnet":
            SOL_EXPLORER_URL += f"?cluster={self.network}"
        return SOL_EXPLORER_URL

    def build_tx(self, amount, account):
        """Build and sign a transfer transaction.
        Used to transfer tokens with the given parameters.
        """
        unsigned_tx_bin = self.sol.prepare(account, amount)
        # Since this is EdDSA, provide the full tx to sign device
        tx_signature = self.current_device.sign(unsigned_tx_bin)
        return self.sol.add_signature(unsigned_tx_bin, tx_signature)

    def broadcast_tx(self, txdata):
        """Broadcast and return the tx id"""
        return self.sol.send(txdata)

    def transfer(self, amount, to_account, priority_fee):
        # Transfer x unit to an account, pay
        tx_data = self.build_tx(shift_10(amount, self.sol.decimals), to_account)
        return "\nDONE, txID : " + self.broadcast_tx(tx_data)

    def transfer_inclfee(self, amount, to_account):
        # Transfer the amount in base unit minus fee, like the receiver paying the fee
        tx_data = self.build_tx(amount - FEE_LEVEL, to_account)
        return "\nDONE, txID : " + self.broadcast_tx(tx_data)[2:]

    def transfer_all(self, to_account, fee_priority):
        # Transfer all the wallet to an address (minus fee)
        all_amount = self.sol.getbalance()
        return self.transfer_inclfee(all_amount, to_account)
