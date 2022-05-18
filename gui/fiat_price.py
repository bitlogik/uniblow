from json import load
from threading import Thread
from urllib.request import urlopen


chain_names = {
    "GMLR": "moonbeam",
    "EOS": "eos",
    "XTZ": "tezos",
    "ARB": "arbitrum-one",
    "BSC": "binance-smart-chain",
    "SOL": "solana",
    "FTM": "fantom",
    "CELO": "celo",
    "MATIC": "polygon-pos",
    "MOVR": "moonriver",
    "CRO": "cronos",
    "BOBA": "boba",
    "ONE": "harmony-shard-0",
    "AVAX": "avalanche",
    "METIS": "metis-andromeda",
    "ETH": "ethereum",
    "OP": "optimistic-ethereum",
}

native_tokens = {
    "GMLR": "moonbeam",
    "EOS": "eos",
    "XTZ": "tezos",
    "ARB": "ethereum",
    "BSC": "binancecoin",
    "SOL": "solana",
    "FTM": "fantom",
    "CELO": "celo",
    "MATIC": "matic-network",
    "MOVR": "moonriver",
    "CRO": "cronos",
    "BOBA": "boba-network",
    "ONE": "harmony",
    "AVAX": "avalanche-2",
    "METIS": "metis-token",
    "ETH": "ethereum",
    "OP": "optimism",
}


class PriceAPI:

    BASE_URL = "https://api.coingecko.com/api/v3/"

    def __init__(self, cb, token, chain=""):
        """Async query"""
        Thread(target=self.get_price, args=(token, chain, cb)).start()

    def get_price(self, token_id, chainid, cb):
        """Read token price in USD from CoinGecko"""
        call_url = ""
        if chainid:
            call_url = (
                f"{PriceAPI.BASE_URL}simple/token_price/"
                f"{chain_names.get(chainid)}?"
                f"contract_addresses={token_id.lower()}"
                "&vs_currencies=usd"
            )
        else:
            token_id = native_tokens.get(token_id)
            if token_id is not None:
                call_url = f"{PriceAPI.BASE_URL}simple/price?ids={token_id}" "&vs_currencies=usd"
        if call_url:
            rsp = urlopen(call_url)
            value_json = load(rsp)
            value = value_json[token_id.lower()]["usd"]
            cb(value)
