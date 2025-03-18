from json import load
from urllib.request import urlopen

from wx import CallAfter


chain_names = {
    "GLMR": "moonbeam",
    "EOS": "eos",
    "XTZ": "tezos",
    "ARB": "arbitrum-one",
    "BSC": "binance-smart-chain",
    "SOL": "solana",
    "FTM": "fantom",
    "S": "sonic",
    "CELO": "celo",
    "MATIC": "polygon-pos",
    "TRX": "tron",
    "MOVR": "moonriver",
    "CRO": "cronos",
    "BOBA": "boba",
    "ONE": "harmony-shard-0",
    "AVAX": "avalanche",
    "METIS": "metis-andromeda",
    "ETH": "ethereum",
    "OP": "optimistic-ethereum",
    "BASE": "base",
}

native_tokens = {
    "BTC": "bitcoin",
    "DOGE": "dogecoin",
    "LTC": "litecoin",
    "TRX": "tron",
    "GLMR": "moonbeam",
    "EOS": "eos",
    "XTZ": "tezos",
    "ARB/ETH": "ethereum",
    "BSC": "binancecoin",
    "SOL": "solana",
    "FTM": "fantom",
    "S": "sonic-3",
    "CELO": "celo",
    "POL": "matic-network",
    "MOVR": "moonriver",
    "CRO": "cronos",
    "BOBA": "boba-network",
    "ONE": "harmony",
    "AVAX": "avalanche-2",
    "METIS": "metis-token",
    "ETH": "ethereum",
    "OP/ETH": "ethereum",
    "BASE/ETH": "ethereum",
}


class PriceAPI:
    BASE_URL = "https://api.coingecko.com/api/v3/"

    def __init__(self, cb, token, chain=""):
        """Async query"""
        CallAfter(self.get_price, token, chain, cb)

    def get_price(self, token_id, chainid, cb):
        """Read token price in USD from CoinGecko"""
        if chainid and chainid != "TRX":
            token_id = token_id.lower()
        if chainid:
            chain = chain_names.get(chainid)
            if chain is None:
                return
            call_url = (
                f"{PriceAPI.BASE_URL}simple/token_price/"
                f"{chain}?"
                f"contract_addresses={token_id}"
                "&vs_currencies=usd"
            )
        else:
            token_id = native_tokens.get(token_id)
            if token_id is None:
                return
            call_url = f"{PriceAPI.BASE_URL}simple/price?ids={token_id}&vs_currencies=usd"

        try:
            rsp = urlopen(call_url)
            value_json = load(rsp)
        except Exception:
            return
        try:
            value = value_json[token_id]["usd"]
        except KeyError:
            return
        cb(value)
