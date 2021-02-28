from os import path
from secrets import randbelow
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils

CURVE_K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
EC_BYTES_SIZE = 32

FILE_NAME = "SimpleDeviceWallet.key"


def encode_int(intarray):
    # encode a bytes array to a DER integer (bytes list)
    if intarray[0] >= 128:
        return [2, len(intarray) + 1, 0, *intarray]
    if intarray[0] == 0:
        return encode_int(intarray[1:])
    return [2, len(intarray), *intarray]


def encode_der_s(int_r, int_s):
    # Encode raw signature R|S (2x EC size bytes) into ASN1 DER
    # Enforce low S
    array_r = encode_int(int_r.to_bytes(EC_BYTES_SIZE, byteorder="big"))
    if int_s > (CURVE_K1_ORDER >> 1):
        s_data = (CURVE_K1_ORDER - int_s).to_bytes(EC_BYTES_SIZE, byteorder="big")
        array_s = encode_int(s_data)
    else:
        array_s = encode_int(int_s.to_bytes(EC_BYTES_SIZE, byteorder="big"))
    return bytes([0x30, len(array_r) + len(array_s), *array_r, *array_s])


def fix_s_sig(sig):
    # DER to DER with low S
    if sig[0] != 0x30:
        raise Exception("Wrong signature header")
    if sig[2] != 0x02:
        raise Exception("Wrong signature format")
    rlen = sig[3]
    r_value = int.from_bytes(sig[4 : 4 + rlen], "big")
    slen = sig[5 + rlen]
    s_value = int.from_bytes(sig[6 + rlen : 6 + rlen + slen], "big")
    if sig[1] != 4 + rlen + slen or len(sig) != 6 + rlen + slen:
        raise Exception("Wrong signature encoding")
    return encode_der_s(r_value, s_value)


class BasicFile:
    # Using Python cryptography lib
    def __init__(self):
        self.open_account()

    def open_account(self):
        if path.isfile(FILE_NAME):
            # Open the current key from its file
            key_file = open(FILE_NAME, "rb")
            pvkey_int = int.from_bytes(key_file.read(), "big")
        else:
            # Generate a new key and save it in a file
            pvkey_int = randbelow(CURVE_K1_ORDER)
            key_file = open(FILE_NAME, "wb")
            key_file.write(pvkey_int.to_bytes(EC_BYTES_SIZE, byteorder="big"))
        key_file.close()
        self.pvkey = ec.derive_private_key(pvkey_int, ec.SECP256K1())
        # or self.pvkey = ec.generate_private_key(ec.SECP256K1())

    def get_public_key(self):
        # pubkey = cryptos.coins.bitcoin.Bitcoin(testnet=True).privtopub(self.pvkey)
        # return cryptos.encode_pubkey(pubkey, 'hex_compressed')
        return (
            self.pvkey.public_key()
            .public_bytes(serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint)
            .hex()
        )

    def sign(self, message):
        raw_sig = self.pvkey.sign(message, ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        return fix_s_sig(raw_sig)
