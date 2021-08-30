#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW typed structured data hashing
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


"""
An EIP-712 wallet implementation for Ethereum typed structured data hashing.
"""


from pprint import pformat
from sys import version_info

from cryptolib.cryptography import sha3
from cryptolib.coins.ethereum import uint256

uint_types = [f"uint{l}" for l in range(8, 257)]
int_types = [f"int{l}" for l in range(8, 257)]
bytes_types = [f"bytes{l}" for l in range(1, 33)]
std_types = ["bool", *uint_types, *int_types, "address", *bytes_types, "bytes", "string"]


def collect_sub_types(name, types_obj, list_types=None):
    """Collect all types of a struct."""
    if not list_types:
        list_types = []
    if name.endswith("[]"):
        name = name[:-2]
    if name in list_types:
        return list_types
    if name not in types_obj.keys():
        return list_types
    list_types.append(name)
    for member in types_obj[name]:
        for submember in collect_sub_types(member["type"], types_obj, list_types):
            if submember in std_types:
                continue
            if submember not in list_types:
                list_types.append(submember)
    return list_types[1:]


def encode_atype(name, types_list):
    """Encode a struct type string for typeHash."""
    member_list = []
    for member in types_list:
        if "name" in member:
            member_list.append(f"{member['type']} {member['name']}")
    return f"{name}({','.join(member_list)})"


def encode_types(types_list, types_dict):
    """Provide the struct type string signature (encodeType)."""
    types_enc = ""
    for type_key in types_list:
        print(type_key)
        if type_key.endswith("[]"):
            type_key = type_key[:-2]
        types_enc += encode_atype(type_key, types_dict[type_key])
    return types_enc


def type_hash(name, types_obj):
    """Compute typeHash (hash of the encodeType type string)."""
    subtypes_list = collect_sub_types(name, types_obj)
    subtypes_list.sort()
    print("subtypes", subtypes_list)
    types_list = [name, *subtypes_list]
    print(encode_types(types_list, types_obj).encode("utf8"))
    return sha3(encode_types(types_list, types_obj).encode("utf8"))


def encode_value(vtype, value, go):
    """Encode a value in Python bytes."""
    if vtype == "bool":
        # check is bool
        return uint256(1) if value else uint256(0)
    if vtype == "address":
        # check is hex 40 chars
        return uint256(int(value[2:], 16))
    if vtype in int_types or vtype in uint_types:
        # check is int
        if value > 0:
            intval_bin = uint256(value)
        else:
            intval_bin = uint256(2 ** 256 + value)
        return intval_bin
    if vtype in bytes_types:
        # check is 0x hex
        out = bytes.fromhex(value[2:])
        while len(out) < 32:
            out += b"\0"
        return out
    if vtype == "bytes":
        # check is 0x hex
        out = bytes.fromhex(value[2:])
        return sha3(out)
    if vtype == "string":
        # check is str
        return sha3(value.encode("utf8"))
    # array not implemented
    if vtype.endswith("[]"):
        # check is list
        elements = [encode_value(vtype[:-2], val, go) for val in value]
        return sha3(b"".join(elements))
    # should be a struct
    # test if value is dict
    return hash_struct(vtype, go, value)


def encode_data(name, types_obj, data_obj):
    """encodeData : Encode all the data of the members values."""
    out = b""
    for member in types_obj[name]:
        if "name" in member:
            mvalue = data_obj[member["name"]]
            mtype = member["type"]
            if isinstance(mvalue, dict):
                out += hash_struct(mtype, types_obj, mvalue)
            else:
                out += encode_value(mtype, mvalue, types_obj)
    return out


def hash_struct(name, types_obj, data_obj):
    """Compute the hashStruct = keccak256(typeHash ‖ encodeData(s))."""
    return sha3(type_hash(name, types_obj) + encode_data(name, types_obj, data_obj))


def typed_sign_hash(query_obj, chain_id=None):
    """Compute the hash to sign form the typed data object."""

    # Checking the query format
    if "primaryType" not in query_obj:
        raise Exception("Missing primaryType in typedhash query.")
    if "types" not in query_obj:
        raise Exception("Missing types in typedhash query.")
    if "EIP712Domain" not in query_obj["types"]:
        raise Exception("Missing EIP712Domain in typedhash.types.")
    if query_obj["primaryType"] not in query_obj["types"]:
        if query_obj["primaryType"] not in std_types:
            raise Exception("Missing primary type in typedhash.types query.")
    if "message" not in query_obj:
        raise Exception("Missing message in typedhash query.")
    if "domain" not in query_obj:
        raise Exception("Missing domain in typedhash query.")
    if chain_id is not None and "chainId" in query_obj["domain"]:
        if chain_id != query_obj["domain"]["chainId"]:
            raise Exception("ChainID is not matching the current active chain.")
    hash_msg = hash_struct(query_obj["primaryType"], query_obj["types"], query_obj["message"])

    # Compute the hash to sign
    domain_separator = hash_struct("EIP712Domain", query_obj["types"], query_obj["domain"])
    return sha3(b"\x19\x01" + domain_separator + hash_msg)


def print_text_query(query_obj):
    """Generate the string for user display approval."""
    format_args = {"indent": 4}
    if version_info >= (3, 8):
        format_args["sort_dicts"] = False
    datam = pformat(query_obj["message"], **format_args)
    return f"{query_obj['primaryType']}\n{datam}\n"
