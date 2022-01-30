from cryptolib.cryptography import sha3
from wallets.typed_data_hash import encode_data, type_hash, hash_struct, typed_sign_hash


# Tests for EIP712 typed structured data hashing


def full_message_digest(domain_hash, digest_data):
    return sha3(b"\x19\x01" + domain_hash + digest_data)


def test_eip712_simple():
    mail_struct = {
        "Mail": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "contents", "type": "string"},
        ],
    }
    mail_enc = type_hash("Mail", mail_struct)
    assert mail_enc.hex() == "536e54c54e6699204b424f41f6dea846ee38ac369afec3e7c141d2c92c65e67f"


def test_eip712_A():

    # Official test vector from EIP712
    # https://eips.ethereum.org/EIPS/eip-712#test-cases
    # https://github.com/ethereum/EIPs/blob/master/assets/eip-712/Example.js#L129

    typed_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Person": [{"name": "name", "type": "string"}, {"name": "wallet", "type": "address"}],
            "Mail": [
                {"name": "from", "type": "Person"},
                {"name": "to", "type": "Person"},
                {"name": "contents", "type": "string"},
            ],
        },
        "primaryType": "Mail",
        "domain": {
            "name": "Ether Mail",
            "version": "1",
            "chainId": 1,
            "verifyingContract": "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC",
        },
        "message": {
            "from": {
                "name": "Cow",
                "wallet": "0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826",
            },
            "to": {
                "name": "Bob",
                "wallet": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB",
            },
            "contents": "Hello, Bob!",
        },
    }

    type_hash_mail = type_hash("Mail", typed_data["types"])
    # keccak256("Mail(Person from,Person to,string contents)Person(string name,address wallet)")
    assert (
        type_hash_mail.hex() == "a0cedeb2dc280ba39b857546d74f5549c3a1d7bdc2dd96bf881f76108e23dac2"
    )

    enc_data = encode_data("Mail", typed_data["types"], typed_data["message"])
    assert enc_data.hex() == (
        "fc71e5fa27ff56c350aa531bc129ebdf613b772b6604664f5d8dbe21b85eb0c8cd54f074a4af31b4"
        "411ff6a60c9719dbd559c221c8ac3492d9d872b041d703d1b5aadf3154a261abdd9086fc627b61ef"
        "ca26ae5702701d05cd2305f7c52a2fc8"
    )

    dom_sep, hashf = typed_sign_hash(typed_data)
    assert dom_sep.hex() == "f2cee375fa42b42143804025fc449deafd50cc031ca257e0b194a650a912090f"
    assert hashf.hex() == "c52c0ee5d84264471806290a3f2c4cecfc5490626bf912d01f240d7a274b371e"
    assert (
        full_message_digest(dom_sep, hashf).hex()
        == "be609aee343fb3c4b28e1df9e632fca64fcfaede20f02e86244efddf30957bd2"
    )


def test_eip712_B():

    # Test vectors from the npm package ethers-eip712
    # https://github.com/0xsequence/ethers-eip712/blob/master/tests/typed-data.test.ts

    types_tst = {
        "Person": [
            {"name": "name", "type": "string"},
            {"name": "wallet", "type": "address"},
        ],
        "Mail": [
            {"name": "from", "type": "Person"},
            {"name": "to", "type": "Person"},
            {"name": "contents", "type": "string"},
            {"name": "asset", "type": "Asset"},
        ],
        "Asset": [{"name": "name", "type": "string"}],
    }
    phash = type_hash("Person", types_tst)
    assert phash.hex() == "b9d8c78acf9b987311de6c7b45bb6a9c8e1bf361fa7fd3467a2163f994c79500"
    thash = type_hash("Mail", types_tst)
    assert thash.hex() == "5848dd854dd9179bf93f24186c392747bac3b59ff85125874ed562b05c02d8a6"

    # Test encoding 1
    typed_data1 = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Person": [
                {"name": "name", "type": "string"},
                {"name": "wallet", "type": "address"},
            ],
        },
        "primaryType": "Person",
        "domain": {
            "name": "Ether Mail",
            "version": "1",
            "chainId": 1,
            "verifyingContract": "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC",
        },
        "message": {"name": "Bob", "wallet": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"},
    }
    dom_sep, thash = typed_sign_hash(typed_data1)
    assert dom_sep.hex() == "f2cee375fa42b42143804025fc449deafd50cc031ca257e0b194a650a912090f"
    assert (
        full_message_digest(dom_sep, thash).hex()
        == "0a94cf6625e5860fc4f330d75bcd0c3a4737957d2321d1a024540ab5320fe903"
    )

    # Test encoding 2
    typed_data2 = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Person": [
                {"name": "name", "type": "string"},
                {"name": "wallet", "type": "address"},
                {"name": "count", "type": "uint8"},
            ],
        },
        "primaryType": "Person",
        "domain": {
            "name": "Ether Mail",
            "version": "1",
            "chainId": 1,
            "verifyingContract": "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC",
        },
        "message": {
            "name": "Bob",
            "wallet": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB",
            "count": 4,
        },
    }
    dom_sep, thash = typed_sign_hash(typed_data2)
    assert dom_sep.hex() == "f2cee375fa42b42143804025fc449deafd50cc031ca257e0b194a650a912090f"
    assert (
        full_message_digest(dom_sep, thash).hex()
        == "2218fda59750be7bb9e5dfb2b49e4ec000dc2542862c5826f1fe980d6d727e95"
    )

    # Test encoding 3
    typed_data3 = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Person": [
                {"name": "name", "type": "string"},
                {"name": "wallets", "type": "address[]"},
            ],
            "Mail": [
                {"name": "from", "type": "Person"},
                {"name": "to", "type": "Person[]"},
                {"name": "contents", "type": "string"},
            ],
            "Group": [
                {"name": "name", "type": "string"},
                {"name": "members", "type": "Person[]"},
            ],
        },
        "domain": {
            "name": "Ether Mail",
            "version": "1",
            "chainId": 1,
            "verifyingContract": "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC",
        },
        "primaryType": "Mail",
        "message": {
            "from": {
                "name": "Cow",
                "wallets": [
                    "0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826",
                    "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF",
                ],
            },
            "to": [
                {
                    "name": "Bob",
                    "wallets": [
                        "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB",
                        "0xB0BdaBea57B0BDABeA57b0bdABEA57b0BDabEa57",
                        "0xB0B0b0b0b0b0B000000000000000000000000000",
                    ],
                }
            ],
            "contents": "Hello, Bob!",
        },
    }
    phash3 = type_hash("Group", typed_data3["types"])
    assert phash3.hex() == "1d953c52160a9018dbb518700e05da47418ac2b6044f0c044f84c15a80103107"
    phash3 = type_hash("Person", typed_data3["types"])
    assert phash3.hex() == "fabfe1ed996349fc6027709802be19d047da1aa5d6894ff5f6486d92db2e6860"
    hash_person_1 = hash_struct("Person", typed_data3["types"], typed_data3["message"]["from"])
    assert hash_person_1.hex() == "9b4846dd48b866f0ac54d61b9b21a9e746f921cefa4ee94c4c0a1c49c774f67f"
    hash_person_2 = hash_struct("Person", typed_data3["types"], typed_data3["message"]["to"][0])
    assert hash_person_2.hex() == "efa62530c7ae3a290f8a13a5fc20450bdb3a6af19d9d9d2542b5a94e631a9168"
    phash3 = type_hash("Mail", typed_data3["types"])
    assert phash3.hex() == "4bd8a9a2b93427bb184aca81e24beb30ffa3c747e2a33d4225ec08bf12e2e753"
    dom_sep, hash_primary = typed_sign_hash(typed_data3)
    assert hash_primary.hex() == "eb4221181ff3f1a83ea7313993ca9218496e424604ba9492bb4052c03d5c3df8"
    assert dom_sep.hex() == "f2cee375fa42b42143804025fc449deafd50cc031ca257e0b194a650a912090f"
    assert (
        full_message_digest(dom_sep, hash_primary).hex()
        == "a85c2e2b118698e88db68a8105b794a8cc7cec074e89ef991cb4f5f533819cc2"
    )

    # Test encoding 4
    typed_data4 = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Person": [
                {"name": "name", "type": "string"},
                {"name": "wallet", "type": "address"},
                {"name": "count", "type": "bytes8"},
            ],
        },
        "primaryType": "Person",
        "domain": {
            "name": "Ether Mail",
            "version": "1",
            "chainId": 1,
            "verifyingContract": "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC",
        },
        "message": {
            "name": "Bob",
            "wallet": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB",
            "count": "0x1122334455667788",
        },
    }
    dom_sep, hashdf = typed_sign_hash(typed_data4)
    assert dom_sep.hex() == "f2cee375fa42b42143804025fc449deafd50cc031ca257e0b194a650a912090f"
    assert (
        full_message_digest(dom_sep, hashdf).hex()
        == "2a3e64893ed4ba30ea34dbff3b0aa08c7677876cfdf7112362eccf3111f58d1d"
    )


def test_real_dapp():
    data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "RelayRequest": [
                {"name": "target", "type": "address"},
                {"name": "encodedFunction", "type": "bytes"},
                {"name": "gasData", "type": "GasData"},
                {"name": "relayData", "type": "RelayData"},
            ],
            "GasData": [
                {"name": "gasLimit", "type": "uint256"},
                {"name": "gasPrice", "type": "uint256"},
                {"name": "pctRelayFee", "type": "uint256"},
                {"name": "baseRelayFee", "type": "uint256"},
            ],
            "RelayData": [
                {"name": "senderAddress", "type": "address"},
                {"name": "senderNonce", "type": "uint256"},
                {"name": "relayWorker", "type": "address"},
                {"name": "paymaster", "type": "address"},
            ],
        },
        "domain": {
            "name": "GSN Relayed Transaction",
            "version": "1",
            "chainId": 42,
            "verifyingContract": "0x6453D37248Ab2C16eBd1A8f782a2CBC65860E60B",
        },
        "primaryType": "RelayRequest",
        "message": {
            "target": "0x9cf40ef3d1622efe270fe6fe720585b4be4eeeff",
            "encodedFunction": "0xa9059cbb0000000000000000000000002e0d94754b348d208d64d52d78bcd443afa9fa520000000000000000000000000000000000000000000000000000000000000007",
            "gasData": {
                "gasLimit": "39507",
                "gasPrice": "1700000000",
                "pctRelayFee": "70",
                "baseRelayFee": "0",
            },
            "relayData": {
                "senderAddress": "0x22d491bde2303f2f43325b2108d26f1eaba1e32b",
                "senderNonce": "3",
                "relayWorker": "0x3baee457ad824c94bd3953183d725847d023a2cf",
                "paymaster": "0x957F270d45e9Ceca5c5af2b49f1b5dC1Abb0421c",
            },
        },
    }
    typed_sign_hash(data)
