# -*- coding: utf8 -*-

# UNIBLOW BTC lib wallet
# Copyright (C) 2015-2019 Vitalik Buterin and pycryptools developers
# Copyright (C) 2019-2021 primal100
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

import binascii
import copy
import re
from functools import reduce

from cryptolib.cryptography import Hash160, dbl_sha2
from cryptolib.base58 import encode_base58_header, decode_base58


string_or_bytes_types = (str, bytes)
int_types = (int, float)


def pubkey_to_hash(pubkey):
    if len(pubkey) in [66, 130]:
        return Hash160(bytes.fromhex(pubkey))
    assert len(pubkey) in [33, 65]
    return Hash160(pubkey)


def pubkey_to_hash_hex(pubkey):
    return pubkey_to_hash(pubkey).hex()


def pubtoaddr(pubkey, magicbyte=0):
    pubkey_hash = pubkey_to_hash(pubkey)
    return encode_base58_header(pubkey_hash, magicbyte)


def b58check_to_hex(data_b58):
    return decode_base58(data_b58)[1:].hex()


def num_to_var_int(x):
    x = int(x)
    if x < 253:
        return bytes([x])
    elif x < 65536:
        return bytes([253]) + encode(x, 256, 2)[::-1]
    elif x < 4294967296:
        return bytes([254]) + encode(x, 256, 4)[::-1]
    else:
        return bytes([255]) + encode(x, 256, 8)[::-1]


def hex_to_hash160(data_hex):
    return Hash160(bytes.fromhex(data_hex)).hex()


def dbl_sha256(data):
    return dbl_sha2(data).hex()


string_types = str
string_or_bytes_types = (str, bytes)
int_types = (int, float)

code_strings = {
    2: "01",
    10: "0123456789",
    16: "0123456789abcdef",
    32: "abcdefghijklmnopqrstuvwxyz234567",
    58: "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz",
    256: "".join([chr(x) for x in range(256)]),
}


def lpad(msg, symbol, length):
    if len(msg) >= length:
        return msg
    return symbol * (length - len(msg)) + msg


def get_code_string(base):
    if base in code_strings:
        return code_strings[base]
    else:
        raise ValueError("Invalid base!")


def changebase(string, frm, to, minlen=0):
    if frm == to:
        return lpad(string, get_code_string(frm)[0], minlen)
    return encode(decode(string, frm), to, minlen)


def bytes_to_hex_string(b):
    if isinstance(b, str):
        return b

    return "".join("{:02x}".format(y) for y in b)


def safe_from_hex(s):
    return bytes.fromhex(s)


def from_int_representation_to_bytes(a):
    return bytes(str(a), "utf-8")


def from_int_to_byte(a):
    return bytes([a])


def from_string_to_bytes(a):
    return a if isinstance(a, bytes) else bytes(a, "utf-8")


def safe_hexlify(a):
    return str(binascii.hexlify(a), "utf-8")


def encode(val, base, minlen=0):
    base, minlen = int(base), int(minlen)
    code_string = get_code_string(base)
    result_bytes = bytes()
    while val > 0:
        curcode = code_string[val % base]
        result_bytes = bytes([ord(curcode)]) + result_bytes
        val //= base

    pad_size = minlen - len(result_bytes)

    padding_element = b"\x00" if base == 256 else b"1" if base == 58 else b"0"
    if pad_size > 0:
        result_bytes = padding_element * pad_size + result_bytes

    result_string = "".join([chr(y) for y in result_bytes])
    result = result_bytes if base == 256 else result_string

    return result


def decode(string, base):
    if base == 256 and isinstance(string, str):
        string = bytes(bytearray.fromhex(string))
    base = int(base)
    code_string = get_code_string(base)
    result = 0

    if base == 256:

        def extract(d, cs):
            return d

    else:

        def extract(d, cs):
            return cs.find(d if isinstance(d, str) else chr(d))

    if base == 16:
        string = string.lower()
    while len(string) > 0:
        result *= base
        result += extract(string[0], code_string)
        string = string[1:]
    return result


def json_is_base(obj, base):
    if isinstance(obj, bytes):
        return False

    alpha = get_code_string(base)
    if isinstance(obj, string_types):
        for i in range(len(obj)):
            if alpha.find(obj[i]) == -1:
                return False
        return True
    elif isinstance(obj, int_types) or obj is None:
        return True
    elif isinstance(obj, list):
        for i in range(len(obj)):
            if not json_is_base(obj[i], base):
                return False
        return True
    else:
        for x in obj:
            if not json_is_base(obj[x], base):
                return False
        return True


def json_changebase(obj, changer):
    if isinstance(obj, string_or_bytes_types):
        return changer(obj)
    elif isinstance(obj, int_types) or obj is None:
        return obj
    elif isinstance(obj, list):
        return [json_changebase(x, changer) for x in obj]
    return dict((x, json_changebase(obj[x], changer)) for x in obj)


SIGHASH_ALL = 1
SIGHASH_NONE = 2
SIGHASH_SINGLE = 3
SIGHASH_ANYONECANPAY = 0x81
SIGHASH_FORKID = 0x40


def encode_1_byte(val):
    return encode(val, 256, 1)[::-1]


def encode_4_bytes(val):
    return encode(val, 256, 4)[::-1]


def encode_8_bytes(val):
    return encode(val, 256, 8)[::-1]


def list_to_bytes(vals):
    return reduce(lambda x, y: x + y, vals, bytes())


def dbl_sha256_list(vals):
    return dbl_sha2(list_to_bytes(vals))


# Transaction serialization and deserialization


def is_segwit(tx):
    return tx[4] == 0


def deserialize(tx):
    if isinstance(tx, str) and re.match("^[0-9a-fA-F]*$", tx):
        # tx = bytes(bytearray.fromhex(tx))
        return json_changebase(deserialize(binascii.unhexlify(tx)), lambda x: safe_hexlify(x))
    # http://stackoverflow.com/questions/4851463/python-closure-write-to-variable-in-parent-scope
    # Python's scoping rules are demented, requiring me to make pos an object
    # so that it is call-by-reference
    pos = [0]

    def read_as_int(bytez):
        pos[0] += bytez
        return decode(tx[pos[0] - bytez : pos[0]][::-1], 256)

    def read_var_int():
        pos[0] += 1
        val = tx[pos[0] - 1]
        if val < 253:
            return val
        return read_as_int(pow(2, val - 252))

    def read_bytes(bytez):
        pos[0] += bytez
        return tx[pos[0] - bytez : pos[0]]

    def read_var_string():
        size = read_var_int()
        return read_bytes(size)

    def read_segwit_string():
        size = read_var_int()
        return num_to_var_int(size) + read_bytes(size)

    obj = {"ins": [], "outs": []}
    obj["version"] = read_as_int(4)
    has_witness = is_segwit(tx)
    if has_witness:
        obj["marker"] = read_as_int(1)
        obj["flag"] = read_as_int(1)
    ins = read_var_int()
    for i in range(ins):
        obj["ins"].append(
            {
                "outpoint": {"hash": read_bytes(32)[::-1], "index": read_as_int(4)},
                "script": read_var_string(),
                "sequence": read_as_int(4),
            }
        )
    outs = read_var_int()
    for i in range(outs):
        obj["outs"].append({"value": read_as_int(8), "script": read_var_string()})
    if has_witness:
        obj["witness"] = []
        for i in range(ins):
            number = read_var_int()
            scriptCode = []
            for i in range(number):
                scriptCode.append(read_segwit_string())
            obj["witness"].append({"number": number, "scriptCode": list_to_bytes(scriptCode)})
    obj["locktime"] = read_as_int(4)
    return obj


def serialize(txobj, include_witness=True):
    if isinstance(txobj, bytes):
        txobj = bytes_to_hex_string(txobj)
    o = []
    if json_is_base(txobj, 16):
        json_changedbase = json_changebase(txobj, lambda x: binascii.unhexlify(x))
        hexlified = safe_hexlify(serialize(json_changedbase, include_witness=include_witness))
        return hexlified
    o.append(encode_4_bytes(txobj["version"]))
    if include_witness and all(k in txobj.keys() for k in ["marker", "flag"]):
        o.append(encode_1_byte(txobj["marker"]))
        o.append(encode_1_byte(txobj["flag"]))
    o.append(num_to_var_int(len(txobj["ins"])))
    for inp in txobj["ins"]:
        o.append(inp["outpoint"]["hash"][::-1])
        o.append(encode_4_bytes(inp["outpoint"]["index"]))
        o.append(num_to_var_int(len(inp["script"])) + (inp["script"] if inp["script"] else bytes()))
        o.append(encode_4_bytes(inp["sequence"]))
    o.append(num_to_var_int(len(txobj["outs"])))
    for out in txobj["outs"]:
        o.append(encode_8_bytes(out["value"]))
        o.append(num_to_var_int(len(out["script"])) + out["script"])
    if include_witness and "witness" in txobj.keys():
        for witness in txobj["witness"]:
            o.append(
                num_to_var_int(witness["number"])
                + (witness["scriptCode"] if witness["scriptCode"] else bytes())
            )
    o.append(encode_4_bytes(txobj["locktime"]))
    return list_to_bytes(o)


# https://github.com/Bitcoin-UAHF/spec/blob/master/replay-protected-sighash.md#OP_CHECKSIG
def uahf_digest(txobj, i):
    if isinstance(txobj, bytes):
        txobj = bytes_to_hex_string(txobj)
    o = []

    if json_is_base(txobj, 16):
        txobj = json_changebase(txobj, lambda x: binascii.unhexlify(x))
    o.append(encode(txobj["version"], 256, 4)[::-1])

    serialized_ins = []
    for inp in txobj["ins"]:
        serialized_ins.append(inp["outpoint"]["hash"][::-1])
        serialized_ins.append(encode_4_bytes(inp["outpoint"]["index"]))
    inputs_hashed = dbl_sha256_list(serialized_ins)
    o.append(inputs_hashed)

    sequences = dbl_sha256_list([encode_4_bytes(inp["sequence"]) for inp in txobj["ins"]])
    o.append(sequences)

    inp = txobj["ins"][i]
    o.append(inp["outpoint"]["hash"][::-1])
    o.append(encode_4_bytes(inp["outpoint"]["index"]))
    o.append(num_to_var_int(len(inp["script"])) + (inp["script"] if inp["script"] else bytes()))
    o.append(encode_8_bytes(inp["amount"]))
    o.append(encode_4_bytes(inp["sequence"]))

    serialized_outs = []
    for out in txobj["outs"]:
        serialized_outs.append(encode_8_bytes(out["value"]))
        serialized_outs.append(num_to_var_int(len(out["script"])) + out["script"])
    outputs_hashed = dbl_sha256_list(serialized_outs)
    o.append(outputs_hashed)

    o.append(encode_4_bytes(txobj["locktime"]))

    return list_to_bytes(o)


def signature_form(tx, i, script, hashcode=SIGHASH_ALL):
    i, hashcode = int(i), int(hashcode)
    if isinstance(tx, string_or_bytes_types):
        tx = deserialize(tx)
    is_segwit = tx["ins"][i].get("segwit", False) or tx["ins"][i].get("new_segwit", False)
    newtx = copy.deepcopy(tx)
    for inp in newtx["ins"]:
        inp["script"] = ""
    newtx["ins"][i]["script"] = script
    if is_segwit or hashcode & 255 == SIGHASH_ALL + SIGHASH_FORKID:
        return uahf_digest(newtx, i)
    elif hashcode == SIGHASH_NONE:
        newtx["outs"] = []
    elif hashcode == SIGHASH_SINGLE:
        newtx["outs"] = newtx["outs"][: len(newtx["ins"])]
        for out in newtx["outs"][: len(newtx["ins"]) - 1]:
            out["value"] = 2**64 - 1
            out["script"] = ""
    elif hashcode == SIGHASH_ANYONECANPAY:
        newtx["ins"] = [newtx["ins"][i]]
    else:
        pass
    return serialize(newtx, include_witness=False)


# Making the actual signatures


def der_encode_sig(v, r, s):
    b1, b2 = safe_hexlify(encode(r, 256)), safe_hexlify(encode(s, 256))
    if len(b1) and b1[0] in "89abcdef":
        b1 = "00" + b1
    if len(b2) and b2[0] in "89abcdef":
        b2 = "00" + b2
    left = "02" + encode(len(b1) // 2, 16, 2) + b1
    right = "02" + encode(len(b2) // 2, 16, 2) + b2
    return "30" + encode(len(left + right) // 2, 16, 2) + left + right


def der_decode_sig(sig):
    leftlen = decode(sig[6:8], 16) * 2
    left = sig[8 : 8 + leftlen]
    rightlen = decode(sig[10 + leftlen : 12 + leftlen], 16) * 2
    right = sig[12 + leftlen : 12 + leftlen + rightlen]
    return (None, decode(left, 16), decode(right, 16))


def is_bip66(sig):
    """Checks hex DER sig for BIP66 consistency"""
    # https://raw.githubusercontent.com/bitcoin/bips/master/bip-0066.mediawiki
    # 0x30  [total-len]  0x02  [R-len]  [R]  0x02  [S-len]  [S]  [sighash]
    sig = bytearray.fromhex(sig) if re.match("^[0-9a-fA-F]*$", sig) else bytearray(sig)
    if (sig[0] == 0x30) and (sig[1] == len(sig) - 2):  # check if sighash is missing
        sig.extend(b"\1")  # add SIGHASH_ALL for testing
    # assert (sig[-1] & 124 == 0) and (not not sig[-1]), "Bad SIGHASH value"

    if len(sig) < 9 or len(sig) > 73:
        return False
    if sig[0] != 0x30:
        return False
    if sig[1] != len(sig) - 3:
        return False
    rlen = sig[3]
    if 5 + rlen >= len(sig):
        return False
    slen = sig[5 + rlen]
    if rlen + slen + 7 != len(sig):
        return False
    if sig[2] != 0x02:
        return False
    if rlen == 0:
        return False
    if sig[4] & 0x80:
        return False
    if rlen > 1 and (sig[4] == 0x00) and not (sig[5] & 0x80):
        return False
    if sig[4 + rlen] != 0x02:
        return False
    if slen == 0:
        return False
    if sig[rlen + 6] & 0x80:
        return False
    if slen > 1 and (sig[6 + rlen] == 0x00) and not (sig[7 + rlen] & 0x80):
        return False
    return True


def txhash(tx, hashcode=None, wtxid=True):
    if isinstance(tx, str) and re.match("^[0-9a-fA-F]*$", tx):
        tx = changebase(tx, 16, 256)
    if not wtxid and is_segwit(tx):
        tx = serialize(deserialize(tx), include_witness=False)
    if hashcode:
        return dbl_sha256(from_string_to_bytes(tx) + encode(int(hashcode), 256, 4)[::-1])
    else:
        return safe_hexlify(dbl_sha2(tx)[::-1])


def public_txhash(tx, hashcode=None):
    return txhash(tx, hashcode=hashcode, wtxid=False)


def bin_txhash(tx, hashcode=None):
    return binascii.unhexlify(txhash(tx, hashcode))


# Scripts


def mk_pubkey_script(addr):
    """
    Used in converting p2pkh address to input or output script
    """
    return "76a914" + b58check_to_hex(addr) + "88ac"


def mk_scripthash_script(addr):
    """
    Used in converting p2sh address to output script
    """
    return "a914" + b58check_to_hex(addr) + "87"


def output_script_to_address(script, magicbyte=0):
    if script.startswith("76"):
        script = script[6:]
    else:
        script = script[4:]
    if script.endswith("88ac"):
        script = script[:-4]
    else:
        script = script[:-2]
    return encode_base58_header(safe_from_hex(script), magicbyte=magicbyte)


def mk_p2w_scripthash_script(witver, witprog):
    """
    Used in converting a decoded pay to witness script hash address to output script
    """
    if witver < 0 or witver > 16:
        raise Exception("Bad Witness version number.")
    OP_n = witver + 0x50 if witver > 0 else 0
    len_prog = len(witprog)
    if len_prog < 2 or len_prog > 40:
        raise Exception("Bad Witness program data length.")
    return bytes_to_hex_string([OP_n]) + "%0.2X" % len_prog + (bytes_to_hex_string(witprog))


def mk_p2wpkh_redeemscript(pubkey):
    """
    Used in converting public key to p2wpkh script
    """
    return "160014" + pubkey_to_hash_hex(pubkey)


def mk_p2wpkh_script(pubkey):
    """
    Used in converting public key to p2wpkh script
    """
    script = mk_p2wpkh_redeemscript(pubkey)[2:]
    return "a914" + hex_to_hash160(script) + "87"


def mk_p2wpkh_scriptcode(pubkey):
    """
    Used in signing for tx inputs
    """
    return "76a914" + pubkey_to_hash_hex(pubkey) + "88ac"


def p2wpkh_nested_script(pubkey):
    return "0014" + pubkey_to_hash_hex(pubkey)


# Output script to address representation


def deserialize_script(script):
    if isinstance(script, str) and re.match("^[0-9a-fA-F]*$", script):
        return json_changebase(
            deserialize_script(binascii.unhexlify(script)), lambda x: safe_hexlify(x)
        )
    out, pos = [], 0
    while pos < len(script):
        code = script[pos]
        if code == 0:
            out.append(None)
            pos += 1
        elif code <= 75:
            out.append(script[pos + 1 : pos + 1 + code])
            pos += 1 + code
        elif code <= 78:
            szsz = pow(2, code - 76)
            sz = decode(script[pos + szsz : pos : -1], 256)
            out.append(script[pos + 1 + szsz : pos + 1 + szsz + sz])
            pos += 1 + szsz + sz
        elif code <= 96:
            out.append(code - 80)
            pos += 1
        else:
            out.append(code)
            pos += 1
    return out


def serialize_script_unit(unit):
    if isinstance(unit, int):
        if unit < 16:
            return from_int_to_byte(unit + 80)
        else:
            return from_int_to_byte(unit)
    elif unit is None:
        return b"\x00"
    else:
        if len(unit) <= 75:
            return from_int_to_byte(len(unit)) + unit
        elif len(unit) < 256:
            return from_int_to_byte(76) + from_int_to_byte(len(unit)) + unit
        elif len(unit) < 65536:
            return from_int_to_byte(77) + encode(len(unit), 256, 2)[::-1] + unit
        else:
            return from_int_to_byte(78) + encode(len(unit), 256, 4)[::-1] + unit


def serialize_script(script):
    if json_is_base(script, 16):
        return safe_hexlify(serialize_script(json_changebase(script, binascii.unhexlify)))
    result = bytes()
    for b in map(serialize_script_unit, script):
        result += b if isinstance(b, bytes) else bytes(b, "utf-8")
    return result


def mk_multisig_script(*args):  # [pubs],k or pub1,pub2...pub[n],M
    """
    :param args: List of public keys to used to create multisig and M, the number of signatures required to spend
    :return: multisig script
    """
    if isinstance(args[0], list):
        pubs, M = args[0], int(args[1])
    else:
        pubs = list(filter(lambda x: len(str(x)) >= 32, args))
        M = int(args[len(pubs)])
    N = len(pubs)
    return serialize_script([M] + pubs + [N] + [0xAE])


# Signing and verifying


def apply_multisignatures(txobj, i, script, *args):
    # tx,i,script,sigs OR tx,i,script,sig1,sig2...,sig[n]
    sigs = args[0] if isinstance(args[0], list) else list(args)

    if isinstance(script, str) and re.match("^[0-9a-fA-F]*$", script):
        script = binascii.unhexlify(script)
    sigs = [binascii.unhexlify(x) if x[:2] == "30" else x for x in sigs]
    if not isinstance(txobj, dict):
        txobj = deserialize(txobj)
    if isinstance(txobj, str) and re.match("^[0-9a-fA-F]*$", txobj):
        return safe_hexlify(apply_multisignatures(binascii.unhexlify(txobj), i, script, sigs))

    # Not pushing empty elements on the top of the stack if passing no
    # script (in case of bare multisig inputs there is no script)
    script_blob = [] if script.__len__() == 0 else [script]

    txobj["ins"][i]["script"] = safe_hexlify(serialize_script([None] + sigs + script_blob))
    return serialize(txobj)


def is_inp(arg):
    return len(arg) > 64 or "output" in arg or "outpoint" in arg
