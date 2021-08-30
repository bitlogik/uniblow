from wallets.typed_data_hash import encode_data, type_hash, hash_struct, typed_sign_hash


def test_eip712():

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

    struct_hash = hash_struct("Mail", typed_data["types"], typed_data["message"])
    assert struct_hash.hex() == "c52c0ee5d84264471806290a3f2c4cecfc5490626bf912d01f240d7a274b371e"

    dom_sep = hash_struct("EIP712Domain", typed_data["types"], typed_data["domain"])
    assert dom_sep.hex() == "f2cee375fa42b42143804025fc449deafd50cc031ca257e0b194a650a912090f"

    res = typed_sign_hash(typed_data)
    assert res.hex() == "be609aee343fb3c4b28e1df9e632fca64fcfaede20f02e86244efddf30957bd2"

