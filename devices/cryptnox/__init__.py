#!/usr/bin/python3
# -*- coding: utf8 -*-

# Cryptnox smartcard applet commands
# Copyright (C) 2019-2022  BitLogiK & Cryptnox

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


import secrets

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import load_der_x509_certificate

from smartcard.System import readers
from smartcard.CardConnection import CardConnection
from smartcard.util import toBytes
from smartcard.Exceptions import CardConnectionException

from cryptolib.cryptography import random_generator
from cryptolib.ECKeyPair import ECpubkey
from .scp import CryptnoxSecureChannel, init_encrypt


from logging import getLogger

logger = getLogger(__name__)


class CryptnoxException(Exception):
    """Cryptnox generic exception."""

    pass


class CryptnoxInvalidException(CryptnoxException):
    """Cryptnox exception for invalid data or invalid state."""

    pass


class CryptnoxCommException(CryptnoxException):
    """Cryptnox communication exception"""

    pass


class cardinfo_(dict):
    """Class helpers to handle card info."""

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)


def public_bytes(pubkey):
    """Output cryptography.EllipticCurvePrivateKey bytes"""
    # Use to input data into custom cryptolib ECpubkey
    return pubkey.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )


class CryptnoxCard:
    """Cryptnox card commands class."""

    def __init__(self, AppID="A0000010000112"):
        """Search for a Cryptnox and connect to it."""
        reader_detected = False
        self.appid = AppID
        readers_list = readers()
        if len(readers_list) > 0:
            logger.debug("Available smartcard readers : %s", readers_list)
            for r in readers_list:
                if not str(r).startswith("Yubico"):
                    try:
                        logger.debug("Trying with reader : %s", r)
                        self.connection = r.createConnection()
                        self.connection.connect(CardConnection.T1_protocol)
                        reader_detected = hasattr(self, "connection")
                    except Exception:
                        logger.debug("Fail with this reader")
                        pass
                if reader_detected:
                    logger.debug("A Cryptnox detected, using %s", r)
                    break
        if reader_detected:
            self.select()
        else:
            raise Exception("Can't find any Cryptnox connected.")
        self.sec_chan = None
        self.SNID = None  # will be set by get_manufacturer_cert (cert ID)
        self.session_pub_key = self.check_genuine()

    def __del__(self):
        """Disconnect from a Cryptnox."""
        if hasattr(self, "connection"):
            del self.connection

    def select(self):
        """Select the internal applet and read info."""
        APDUapp = [0x00, 0xA4, 0x04, 0x00, len(self.appid) // 2] + toBytes(self.appid)
        datasel = self.send_apdu(APDUapp)
        if len(datasel) == 0:
            raise CryptnoxInvalidException(
                "This card is not answering any data. Are you using NFC?\n"
            )
        if len(datasel) != 24:
            raise CryptnoxInvalidException("This card is not answering correct select length")
        # Decoding flags
        self.cardtype = datasel[0]
        self.applet_version = datasel[1:4]
        card_status_bytes = datasel[4] * 256 + datasel[5]
        self.initialized = bool(card_status_bytes & 64)
        self.seeded = bool(card_status_bytes & 32)
        self.pinauth = bool(card_status_bytes & 16)
        self.pinless = bool(card_status_bytes & 8)
        self.xpubread = bool(card_status_bytes & 4)
        self.clearpubrd = bool(card_status_bytes & 2)
        self.custom_bytes = datasel[8:24]  # uintegers list
        logger.debug("Card Type : %s", chr(self.cardtype))
        logger.debug("Applet Version : %s", self.applet_version)

    def send_apdu(self, APDU):
        """Send a full APDU command, APDU is a list of integers."""
        data_send = len(APDU) - 5
        command = "0x" + hex(APDU[1])[2:].upper()
        if data_send > 0:
            if data_send >= 2 and APDU[4] != data_send:
                data_send -= 2
            logger.debug("--> sending %s with %i bytes data ", command, data_send)
        else:
            logger.debug("--> sending %s", command)
        logger.debug(bytes(APDU).hex())
        try:
            data, sw1, sw2 = self.connection.transmit(APDU)
        except CardConnectionException:
            raise CryptnoxCommException("Cryptnox card was disconnected.")
        logger.debug(
            "<-- received : %02x%02x : %i bytes data",
            sw1,
            sw2,
            len(data),
        )
        logger.debug(bytes(data).hex())
        if sw1 == 0x69 and sw2 == 0x85:
            raise Exception("This command may need a secured channel")
        if sw1 == 0x69 and sw2 == 0x82:
            raise CryptnoxInvalidException("Invalid Pairing key\n")
        if sw1 == 0x6A and sw2 == 0x82:
            raise CryptnoxInvalidException(
                "Error firmware not found\nCheck a Cryptnox is connected\n"
            )
        if sw1 != 0x90 or sw2 != 0x00:
            raise Exception("Error : %02X%02X" % (sw1, sw2))
        return data

    def init(self, name, email, PIN, PUK):
        """Process initialization of the card."""
        # Basic : string PIN : 9 numbers, string PUK : 12 chars
        # PIN can be 4-9 numbers for Basic version
        # bytes PUK : 12 bytes chars
        if self.initialized:
            raise CryptnoxInvalidException("Card was already initialized")
        bname = bytes(name, "ascii")
        bemail = bytes(email, "ascii")
        while len(PIN) < 9:
            PIN += "\0"
        init_data = (
            bytes([len(bname)]) + bname + bytes([len(bemail)]) + bemail + bytes(PIN, "ascii") + PUK
        )
        enc_datainit = init_encrypt(self.session_pub_key, init_data)
        apdu_init = [0x80, 0xFE, 0x00, 0x00, len(enc_datainit)] + enc_datainit
        self.send_apdu(apdu_init)
        self.sec_chan = None
        self.initialized = True
        # Read again the card session key since the init reset the secure channel key
        self.session_pub_key = self.check_genuine()

    def get_manufacturer_cert(self):
        """Read the manufacturer certificate"""
        # Called by instantiation through check_genuine to get card SN ID
        idx_page = 0
        mnft_cert_resp = self.send_apdu([0x80, 0xF7, 0x00, idx_page, 0x00])
        if len(mnft_cert_resp) == 0:
            return b""
        certlen = (mnft_cert_resp[0] << 8) + mnft_cert_resp[1]
        while len(mnft_cert_resp) < (certlen + 2):
            idx_page += 1
            mnft_cert_resp = mnft_cert_resp + self.send_apdu([0x80, 0xF7, 0x00, idx_page, 0x00])
        assert len(mnft_cert_resp) == (certlen + 2)
        cert = mnft_cert_resp[2:]
        return bytes(cert)

    def get_card_certificate(self, nonce):
        """Read the card dynamic certificate"""
        # nonce is a 64 bits integer
        # card cert is : 'C' + ..
        assert len(nonce) == 8
        res = self.send_apdu([0x80, 0xF8, 0x00, 0x00] + [8] + list(nonce))
        return bytes(res)

    def check_genuine(self):
        """Check card authenticity and prepare secure channel."""
        # The secure channels keys are in the authenticated from Cryptnox.
        # So we are sure it communicates with a genuine Cryptnox card.
        PubKey_Mnft_data = bytes.fromhex(
            "04"
            "d9e6b0fb5fbdb835cadd4703748555f55c65a12a79f7b3ca02a2c7048912ad34"
            "6080df7e09e73952adfa9f176219f5772c43826ae69642e31251d9b9ff9955d3"
        )
        pubkey_manufacturer = ECpubkey(PubKey_Mnft_data, "R1")
        mnft_cert_data = self.get_manufacturer_cert()
        logger.debug("Mft cert")
        logger.debug(mnft_cert_data.hex())
        manufacturer_cert = load_der_x509_certificate(mnft_cert_data)
        # Is ECDSA SHA256
        if manufacturer_cert.signature_algorithm_oid.dotted_string != "1.2.840.10045.4.3.2":
            raise CryptnoxInvalidException("Bad Manufacturer signature format.")
        # Check if P256 R1 curve
        try:
            card_pubkey = ECpubkey(public_bytes(manufacturer_cert.public_key()), "R1")
        except Exception:
            raise CryptnoxInvalidException("Bad key format for card certificate public key.")
        try:
            pubkey_manufacturer.check_signature(
                manufacturer_cert.tbs_certificate_bytes, manufacturer_cert.signature
            )
        except InvalidSignature:
            raise CryptnoxInvalidException("Bad Cryptnox signature in card certificate.")
        # Extract card SN ID from cert
        self.SNID = manufacturer_cert.serial_number
        logger.debug("Card SN ID %s", self.SNID)
        # Now proceed the dynamic auth of the card
        nonce4cert = secrets.token_bytes(8)
        card_cert = self.get_card_certificate(nonce4cert)
        logger.debug("Card cert")
        logger.debug(card_cert)
        # C ?
        if card_cert[0] != 0x43:
            logger.error("Bad card certificate header")
            return None
        # Nonce?
        if card_cert[1:9] != nonce4cert:
            logger.error("Card certificate nonce is not the one provided")
            return None
        session_pub_key = card_cert[9:74]
        card_cert_msg = card_cert[:74]
        card_cert_sig = card_cert[74:]
        logger.debug("Card msg")
        logger.debug(card_cert_msg.hex())
        logger.debug("Card sig")
        logger.debug(card_cert_sig.hex())
        logger.debug("Card ephemeral pub key")
        logger.debug(session_pub_key.hex())
        try:
            card_pubkey.check_signature(card_cert_msg, card_cert_sig)
        except InvalidSignature:
            raise CryptnoxInvalidException("Bad card signature in dynamic certificate.")
        return session_pub_key

    def send_enc_apdu(self, APDUh, APDUdata, RcvLong=False):
        """Send encrypted APDU."""
        #    APDUh   : integer list of the APDU header
        #    APDUdata: bytes of the data payload (in clear, will be encrypted)
        if self.sec_chan is None:
            raise CryptnoxInvalidException("Secured channel was not opened.")
        enc_apdu = self.sec_chan.encrypt(APDUh, APDUdata, RcvLong)
        # Send ADPU
        logger.debug("--> sending (SCP) : %i bytes data " % len(APDUdata))
        lenapdu = len(APDUdata)
        if RcvLong or lenapdu >= 256:
            logger.debug(bytes(APDUh + [0, (lenapdu) >> 8, (lenapdu) & 255] + list(APDUdata)).hex())
        else:
            logger.debug(bytes(APDUh + [len(APDUdata)] + list(APDUdata)).hex())
        replist = self.send_apdu(enc_apdu)
        # Decode response
        datadec = self.sec_chan.decrypt(replist)
        status = datadec[-2:]
        datarcvd = datadec[:-2]
        logger.debug("<-- received (SCP) : %s : %i bytes data ", status.hex(), len(datarcvd))
        logger.debug(datarcvd.hex())
        if status != b"\x90\x00":
            raise Exception("Error (SCP) : %02X%02X" % (status[0], status[1]))
        # return bytes instead of a int list
        return datarcvd

    def open_secure_channel(self, PairingKeyIndex=0):
        """Open a secure channel with the card."""
        if not self.initialized:
            raise CryptnoxInvalidException("Card is not initialized")
        # Read card session public key, certified by Crytpnox and dynamic from the card
        self.sec_chan = CryptnoxSecureChannel()
        session_pub_key_host = self.sec_chan.get_session_pubkey()
        APDUosc = [0x80, 0x10, PairingKeyIndex, 0x00, len(session_pub_key_host)] + list(
            session_pub_key_host
        )
        rep = self.send_apdu(APDUosc)
        if len(rep) != 32:
            raise CryptnoxInvalidException("Bad data during secure channel opening")
        ssalt = bytes(rep[:32])
        self.sec_chan.compute_keys(self.session_pub_key, ssalt)
        # Check the secure channel is OK
        self.mutual_auth()

    def mutual_auth(self):
        """Check and finalize the secure channel opening."""
        data = random_generator()
        cmd = [0x80, 0x11, 0, 0]
        resp = self.send_enc_apdu(cmd, data)
        if len(resp) != 32:
            raise CryptnoxInvalidException("Bad data during secure channel testing")

    def set_pairing_key(self, PKi, PK, PUK):
        """Change Pairing Key in the card."""
        SELp = [0x80, 0xDA, PKi, 0x00]
        self.send_enc_apdu(SELp, PK + PUK)

    def get_card_info(self, pk_user_idx=0):
        """Read card info."""
        SELp = [0x80, 0xFA, pk_user_idx, 0x00]
        cardinfo_data = self.send_enc_apdu(SELp, bytes([0]), True)
        if pk_user_idx == 0:
            cardinfo = cardinfo_()
            offset = 0
            cardinfo.key_type = chr(cardinfo_data[offset])
            offset += 1
            lenuser = cardinfo_data[offset]
            offset += 1
            cardinfo.owner = cardinfo_data[offset : lenuser + offset].decode("ascii")
            lenemail = cardinfo_data[lenuser + offset]
            offset += 1
            offuserlist = lenemail + offset + lenuser
            cardinfo.email = cardinfo_data[lenuser + offset : offuserlist].decode("ascii")
            offset += 2
            cardinfo.counter = int.from_bytes(
                cardinfo_data[offuserlist : offuserlist + offset], "big"
            )
        else:
            cardinfo = cardinfo_data
        return cardinfo

    def read_user_data_slot(self, page=0):
        """Read a user data slot."""
        SELp = [0x80, 0xFA, 0, 1 + page]
        return self.send_enc_apdu(SELp, b"", True)

    def write_data(self, P1, data, P2=0):
        """Write data in data slots."""
        SELp = [0x80, 0xFC, P1, P2]
        return self.send_enc_apdu(SELp, data)

    def write_user_data_slot(self, data, page=0):
        """Write data in a user data slot."""
        return self.write_data(0, data, page)

    def write_custom_data_slot(self, data):
        """Write data in the custom data slot."""
        return self.write_data(1, data)

    def get_signing_history(self, slot_hist):
        """Read signing history."""
        SELp = [0x80, 0xFB, slot_hist, 0x00]
        history_slot_data = self.send_enc_apdu(SELp, b"")
        if len(history_slot_data) != 36:
            raise CryptnoxInvalidException("Bad data received during signing history read")
        return history_slot_data

    def testPIN(self, pin):
        """Verify PIN code."""
        SELp = [0x80, 0x20, 0x00, 0x00]
        return self.send_enc_apdu(SELp, bytes(pin, "ascii"))

    def get_pin_left(self):
        """Read remaining PIN left."""
        resp_pinleft = self.testPIN("")
        return resp_pinleft[0]

    def changePIN(self, selPINPUK, newPINPUK):
        """Change PIN."""
        # Select PIN PUK :
        # 0x00 = PIN
        # 0x01 = PUK
        SELp = [0x80, 0x21, selPINPUK, 0x00]
        if selPINPUK == 0:
            while len(newPINPUK) < 9:
                newPINPUK += b"\0"
        self.send_enc_apdu(SELp, newPINPUK)

    def changePUK(self, currentPUK, newPUK):
        """Change the PUK code."""
        self.changePIN(0x01, currentPUK + newPUK)

    def unblockPIN(self, PUK, newPIN):
        """Perform unlock PIN."""
        SELp = [0x80, 0x22, 0x00, 0x00]
        if self.cardtype == 66:
            while len(newPIN) < 9:
                newPIN += "\0"
        self.send_enc_apdu(SELp, PUK + bytes(newPIN, "ascii"))

    def gen_random(self, size):
        """Read random data from card."""
        SELg = [0x80, 0xD3, size, 0x00]
        rep_random = self.send_enc_apdu(SELg, b"")
        if len(rep_random) != size:
            raise CryptnoxInvalidException("Bad random size read")
        return rep_random

    def gen_key(self, PIN=""):
        """Generate a key in the card."""
        SELg = [0x80, 0xD4, 0x00, 0x00]
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        gen_resp = self.send_enc_apdu(SELg, PINb)
        if len(gen_resp) != 0:
            raise CryptnoxInvalidException("Bad data received during key generation")
        return gen_resp

    def load_seed(self, seed, PIN=""):
        """Load a seed in the card."""
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        bytes_result = self.send_enc_apdu([0x80, 0xD0, 0x03, 0x00], seed + PINb)
        if len(bytes_result) != 0:
            raise CryptnoxInvalidException("Bad data received during key generation")
        self.seeded = True
        return bytes_result

    def load_dualseed_readpubkey(self, PIN=""):
        """Perform dual generation."""
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        # First step of dual : get pubkey + sig (w Group Key)
        bytes_result = self.send_enc_apdu([0x80, 0xD0, 0x04, 0x00], PINb)
        if len(bytes_result) < 65:
            raise CryptnoxInvalidException(
                "Bad data received during dual seed read card public key"
            )
        return bytes_result

    def load_dualseed_loadpubkey(self, pk, PIN=""):
        """Second final step of dual : send pubkey + sig."""
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        bytes_result = self.send_enc_apdu([0x80, 0xD0, 0x05, 0x00], pk + PINb)
        if len(bytes_result) != 0:
            raise CryptnoxInvalidException("Bad data received during key generation")
        self.seeded = True
        return bytes_result

    def derive(self, path_bin, curve="K1"):
        """Perform in card a BIP32 derivation."""
        # 0 derive from master keys
        # 1 derive from parent keys
        # 2 derive from current keys
        # + 16 for R1
        derivation = 0
        deriv_code = derivation << 6
        if curve.upper() == "R1":
            derivation += 16
        SELg = [0x80, 0xD1, deriv_code, 0x00]
        gen_resp = self.send_enc_apdu(SELg, path_bin)
        return gen_resp

    def set_pinauth(self, status, PUKb):
        """Set/unset PIN authentication."""
        # status = False : PIN allowed
        # status = True : PIN not allowed, only user auth w pubkey
        SPLPC = [0x80, 0xC3, 0x00, 0x00]
        if status:
            statbin = b"\x01"  # or anything not 00
        else:
            statbin = b"\x00"
        gen_resp = self.send_enc_apdu(SPLPC, statbin + PUKb)
        self.pinauth = not status
        return gen_resp

    def set_pubexport(self, status, P1, PUKb):
        """Command to change extended public key read."""
        # status = False : xpub export disabled
        # status = True : xpub output enabled
        cmd = [0x80, 0xC5, P1, 0x00]
        if status:
            statbin = b"\x01"  # or anything not 00
        else:
            statbin = b"\x00"
        gen_resp = self.send_enc_apdu(cmd, statbin + PUKb)
        return gen_resp

    def set_xpubread(self, status, PUKb):
        """Set/unset extended public key read."""
        # status = False : xpub export disabled
        # status = True : xpub output enabled
        self.set_pubexport(status, 0, PUKb)
        self.xpubread = status

    def set_clearpukey(self, status, PUKb):
        """Set/unset public key read within clear channel."""
        # status = False : clear public pubkey read disabled
        # status = True : clear public pubkey read enabled
        self.set_pubexport(status, 1, PUKb)
        self.clearpubrd = status

    def get_pubkey_clear(self, derivation, path_bin=b""):
        """Get the public key within clear channel, if enabled."""
        # Derivation
        # 0x00 = Current key
        # 0x01 = Derive
        # 0x10 added if R1
        SELe = [0x80, 0xC2, derivation, 1]
        if path_bin == b"":
            pubkeyl = self.send_apdu(SELe + [0])
        else:
            # Only for testing, should throw error
            pubkeyl = self.send_apdu(SELe + [len(path_bin)] + list(path_bin))
        pubkey = bytes(pubkeyl)
        if pubkey[0] != 0x04:
            raise CryptnoxInvalidException("Bad data received during public key reading")
        return pubkey

    def get_pubkey(self, curve, path_bin=b""):
        """Get the public key."""
        # Derivation
        # 0x00 = Current key
        # 0x01 = Derive
        # 0x10 added if R1
        derivation = 0
        if curve.upper() == "R1":
            derivation += 16
        SELe = [0x80, 0xC2, derivation, 1]
        if path_bin == b"":
            pubkey = self.send_enc_apdu(SELe, b"")
        else:
            pubkey = self.send_enc_apdu(SELe, path_bin)
        if pubkey[0] != 0x04:
            raise CryptnoxInvalidException("Bad data received during public key reading")
        return pubkey

    def get_xpub(self):
        """Get the current xpub, if enabled."""
        SELe = [0x80, 0xC2, 0, 2]
        xpubkey = self.send_enc_apdu(SELe, b"")
        return xpubkey

    def get_path(self, curvetype="K1", path=b""):
        """Read the current key path."""
        curve_code = 0x00
        if curvetype[-2:].upper() == "R1":
            curve_code = 0x10
        SELe = [0x80, 0xC2, curve_code, 0]
        if path == b"":
            data = self.send_enc_apdu(SELe, b"")
        else:
            data = self.send_enc_apdu(SELe, path)
        return data

    def decrypt(self, pub_key, PIN=""):
        """Like DECipher / SLIP17 / ECDH."""
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        bytes_result = self.send_enc_apdu([0x80, 0xC4, 0x00, 0x00], PINb + pub_key)
        if len(bytes_result) != 32:
            raise CryptnoxInvalidException("Bad data received during encrypt")
        return bytes_result

    def decrypt_with_data(self, pub_key, data, PIN=""):
        """Onchip decrypt AES from ECDH."""
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        bytes_result = self.send_enc_apdu([0x80, 0xC4, 0x01, 0x00], PINb + pub_key + data)
        return bytes_result

    def sign(self, hashdata, curve, path_bin=None, sigtype=0, pin=""):
        """Perform a pre-hashed ECD signature."""
        # Derivation
        #  0x00 = Current key (k1)
        #  0x10 = Current key (r1)
        #  0x01 = Derive (k1)
        #  0x11 = Derive (r1)
        #  0x03 = PIN-less path
        # Sig type
        #  0x00 ECDSA
        #  0x01 ECDSA with EOSIO filtering
        derivation = 0
        if curve.upper() == "R1":
            derivation += 16
        COMMsig = [0x80, 0xC0, derivation, sigtype]
        if derivation & 0x0F == 1 and derivation != 3:
            path = path_bin
        else:
            path = b""
        if pin:
            while len(pin) < 9:
                pin += "\0"
            path += pin.encode("ascii")
        data = self.send_enc_apdu(COMMsig, hashdata + path)
        if sigtype != 2 and data[0] != 0x30:
            raise CryptnoxInvalidException("Bad data received during signature")
        return data

    def reset(self, PUK):
        """Reset the card."""
        sigder = self.send_enc_apdu([0x80, 0xFD, 0, 0], PUK)
        if sigder != b"":
            raise CryptnoxInvalidException("Card not reset")
        if hasattr(self, "SessionPubKey"):
            del self.SessionPubKey
        if hasattr(self, "AESkey"):
            del self.AESkey
        # Init internal status of the card object
        # Real flags can be read on card reselect (new object instantiation)
        self.initialized = False
        self.seeded = False
        self.pinauth = False
        self.xpubread = False
        self.clearpubrd = False
        self.pinless = False
        self.userpubkey01 = False
        self.userpubkey02 = False
        self.userpubkey03 = False
        self.custom_bytes = [0] * 16
        self.sec_chan = None

    def send_auth_pubkey(self, EC_auth_pub_key, DataKey, idx, PUK=b""):
        """D5 instruction, add user auth pubkey, EC_auth_pub_key is int list."""
        DataKeybytes = bytes(DataKey, "utf8")
        datalen = 30
        if self.cardtype == 66:  # Basic
            datalen = 64
            EC_auth_pub_key += PUK
        if len(DataKeybytes) > datalen:
            raise CryptnoxInvalidException(f"DataKey can't be longer than {datalen} chars")
        DataKeybytespad = DataKeybytes.ljust(datalen, b"\0")
        bytes_result = self.send_enc_apdu(
            [0x80, 0xD5, 0x00, 0x00], bytes([idx]) + DataKeybytespad + EC_auth_pub_key
        )
        return bytes_result

    def check_auth_sign(self, sig, msg, idx):
        """D6 instruction, over a secure channel.
        Check a signature for sign auth.
        """
        bytes_result = self.send_enc_apdu([0x80, 0xD6, 0x00, 0x00], bytes([idx]) + msg + sig)
        return bytes_result

    def check_auth_challenge(self, sig, idx):
        """D6 instruction, over a secure channel.
        Check a signature reponse for challenge auth.
        """
        bytes_result = self.send_enc_apdu([0x80, 0xD6, 0x02, 0x00], bytes([idx]) + sig)
        return bytes_result

    def get_challenge(self):
        """Auth User Get PinChallenge"""
        bytes_result = self.send_enc_apdu([0x80, 0xD6, 0x01, 0x00], b"")
        return bytes_result

    def get_credID(self):
        """Auth User : Get credential id of the FIDO slot."""
        bytes_result = self.send_enc_apdu([0x80, 0xD6, 0x03, 0x01], b"")
        return bytes_result

    def check_response(self, sig, idx):
        """Auth User Get "Pin" challenge response."""
        # send the signature of the challenge
        #  counter must be prepended if FIDO signature
        # 0x6985 means challenge was reset (e.g. card power cycle)
        bytes_result = self.send_enc_apdu([0x80, 0xD6, 0x02, 0x00], bytes([idx]) + sig)
        assert len(bytes_result) == 1
        return bytes_result[0]

    def del_auth(self, idx, PUK):
        """D7 instruction, over a secure channel, delete a user key for auth."""
        bytes_result = self.send_enc_apdu([0x80, 0xD7, 0x00, 0x00], bytes([idx]) + PUK)
        return bytes_result
