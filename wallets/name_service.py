from cryptolib.cryptography import sha2, sha3
from cryptolib.coins.ethereum import read_string
from pyweb3 import Web3Client

nullValue = bytes.fromhex("00" * 32)
nullAddress = "0x0000000000000000000000000000000000000000"
ENSResolver = "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e"
resolver_polygon = "0x3E67b8c702a1292d1CEb025494C84367fcb12b45"
resolver_eth = "0x1BDc0fD4fbABeed3E611fd6195fCd5d41dcEF393"
ZILresolver = "9611c53BE6d1b32058b2747bdeCECed7e1216793"


ENS_TLDS = ["eth"]
UD_TLDS = [
    "crypto",
    "nft",
    "blockchain",
    "bitcoin",
    "wallet",
    "888",
    "dao",
    "x",
    "klever",
    "hi",
    "kresus",
    "polygon",
]
ZIL_TLDS = ["zil"]


def name_hash(name, hash_alg=sha3):
    """EIP137 namehash computation, returns hex chain w/o 0x"""
    node = nullValue
    if name:
        labels = name.split(".")
        for label in labels[::-1]:
            node = hash_alg(node + hash_alg(label.encode("utf8")))
    return node.hex()


def get_addr(rep32B):
    """Extract hex address from full 32 bytes width hex."""
    return f"0x{rep32B[26:]}"


def check_res(res):
    """Check the response data, if empty."""
    if (
        res is None
        or res == 0
        or res == nullAddress
        or res == "0x"
        or res == "0x0"
        or res == "0x00"
    ):
        return False
    return True


def get_domain(api, contract, id, crypto_str):
    """Resolve at an UD UNS ProxyReader."""
    # call : getData([string],uint256)
    # hashID packing with string=["crypto.<crypto>.address"]
    crhex = crypto_str.encode("utf-8").hex()
    nhex_around = 15
    crlen = (len(crhex) // 2) + nhex_around
    if crlen > 255:
        raise ValueError("crypto_str is too large.")
    crlenhex = "%0.2X" % crlen
    data = (
        f"0000000000000000000000000000000000000000000000000000000000000040{id}"
        f"00000000000000000000000000000000000000000000000000000000000000{crlenhex}"
        f"63727970746f2e{crhex}2e61646472657373"
    )
    if crlen < 32:
        data += "00" * (32 - crlen)
    res = api.call(contract, "1be5e7ed", data)
    if not check_res(res):
        return None
    res_str = read_string(res)
    if res_str:
        return res_str
    return None


def get_zil_domain(api, contract, id):
    """Resolve at a ZIL contract."""
    q = []
    if id:
        q.append(id)
    res = api.jsonrpc.request("GetSmartContractSubState", [contract, "records", q])
    if res is not None and res.get("records"):
        return res["records"]
    return None


def resolveENS(name):
    """Ethereum Domain Name Service on-chain resolution"""
    api = Web3Client("https://ethereum-rpc.publicnode.com", "Uniblow/2")
    nodeid = name_hash(name)
    # Call the registry to get the resolver for this node id
    # resolver(bytes32)
    result = api.call(ENSResolver, "0178b8bf", nodeid)
    if not check_res(result):
        return None
    # Resolve at the ENS resolver
    # addr(bytes32)
    result = api.call(get_addr(result), "3b3b57de", nodeid)
    if not check_res(result):
        return None
    return get_addr(result)


def resolveUD(name, crypto):
    """UnstoppableDomains service EVM chain resolution"""
    # Try on the Polygon blockchain
    api = Web3Client("https://polygon-bor-rpc.publicnode.com", "Uniblow/2")
    name_id = name_hash(name)
    res = get_domain(api, resolver_polygon, name_id, crypto)
    if res:
        return res
    # Retry on the Ethereum blockchain
    api = Web3Client("https://ethereum-rpc.publicnode.com", "Uniblow/2")
    return get_domain(api, resolver_eth, name_id, crypto)


def resolveZIL(name, crypto):
    """UnstoppableDomains service ZIL chain resolution"""
    api = Web3Client("https://api.zilliqa.com/", "Uniblow/2")
    name_id = f"0x{name_hash(name, sha2)}"
    # Call the registry to get the resolver for this node id
    res = get_zil_domain(api, ZILresolver, name_id)
    if res is None:
        pass
    elif name_id not in res:
        pass
    elif "arguments" not in res[name_id]:
        pass
    elif isinstance(res[name_id]["arguments"], list):
        if len(res[name_id]["arguments"]) >= 2:
            resolver = res[name_id]["arguments"][1]
            # Resolve at the resolver
            if check_res(resolver):
                res = get_zil_domain(api, resolver.replace("0x", ""), "")
                if res:
                    res = res.get(f"crypto.{crypto}.address")
                    if res:
                        return res
    # Try on the Polygon blockchain
    api = Web3Client("https://polygon-bor-rpc.publicnode.com", "Uniblow/2")
    name_id = name_hash(name)
    return get_domain(api, resolver_polygon, name_id, crypto)


def resolve(domain, crypto, is_token=False, chain="XXX"):
    """Generic name resolution for the wallets."""
    dom_split = domain.split(".")
    if not dom_split or len(dom_split) < 2:
        return None
    tld = dom_split[-1]
    if crypto == "ETH" and tld in ENS_TLDS:
        return resolveENS(domain)
    if crypto == "POL":
        crypto = "MATIC"
    if not is_token:
        if crypto == "MATIC":
            crypto = "MATIC.version.MATIC"
        if crypto == "FTM":
            crypto = "FTM.version.OPERA"
    else:
        if chain == "BSC":
            chn = "BEP20"
        else:
            chn = "ERC20"
        crypto = f"{crypto}.version.{chn}"
    if tld in UD_TLDS:
        return resolveUD(domain, crypto)
    if tld in ZIL_TLDS:
        return resolveZIL(domain, crypto)
    return None
