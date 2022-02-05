#!/usr/bin/python3
# -*- coding: utf8 -*-

# Cryptnox smartcard applet communication for Uniblow
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


import base64
import secrets
import re
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from smartcard.System import readers
from smartcard.CardConnection import CardConnection


from logging import getLogger

logger = getLogger(__name__)

# Common public pairing key
# The Basic version can't auth the host, only by PIN
Basic_Pairing_Secret = b"Cryptnox Basic CommonPairingData"


class cardinfo_(dict):
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


class CryptnoxCard:
    def __init__(self, AppID="A0000010000112"):
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

    def __del__(self):
        if hasattr(self, "connection"):
            del self.connection

    def select(self):
        APDUapp = [0x00, 0xA4, 0x04, 0x00, len(self.appid) // 2] + hex2list(self.appid)
        datasel = self.send_apdu(APDUapp)
        if len(datasel) == 0:
            raise Exception("This card is not answering any data. Are you using NFC?\n")
        if len(datasel) != 24:
            raise Exception("This card is not answering correct select length")
        # init internal status about secure channel
        if hasattr(self, "SessionPubKey"):
            delattr(self, "SessionPubKey")
        if hasattr(self, "AESkey"):
            delattr(self, "AESkey")
        if hasattr(self, "MACkey"):
            delattr(self, "MACkey")
        if hasattr(self, "MACiv"):
            delattr(self, "MACiv")
        # Decoding flags
        self.SNID = None  # will be set by get_manufacturer_cert (cert ID)
        self.cardtype = datasel[0]
        self.applet_version = datasel[1:4]
        card_status_bytes = datasel[4] * 256 + datasel[5]
        self.initialized = bool(card_status_bytes & 64)
        self.seeded = bool(card_status_bytes & 32)
        self.pinauth = bool(card_status_bytes & 16)
        self.pinless = bool(card_status_bytes & 8)
        self.xpubread = bool(card_status_bytes & 4)
        self.clearpubrd = bool(card_status_bytes & 2)

        card_publickeys_flag = datasel[6] * 256 + datasel[7]
        self.userpubkey01 = bool(card_publickeys_flag & 1)
        self.userpubkey02 = bool(card_publickeys_flag & 2)
        self.userpubkey03 = bool(card_publickeys_flag & 4)

        self.custom_bytes = datasel[8:24]  # uintegers list

        mnft_cert_hex = self.get_manufacturer_cert()
        # extract card SN ID from cert
        certparts = mnft_cert_hex.split("0302010202")
        if len(certparts) > 1:
            if certparts[1][1] == "8":
                self.SNID = int(certparts[1][2:18], 16)
            if certparts[1][1] == "9":
                self.SNID = int(certparts[1][4:20], 16)
        logger.debug("Card Type : %s", chr(self.cardtype))
        logger.debug("Applet Version : %s", self.applet_version)
        logger.debug("Card SN ID %s", self.SNID)

    def send_apdu(self, APDU):
        # send full APDU, APDU is a list of integers
        logger.debug("--> sending : %i bytes data ", (len(APDU) - 5))
        logger.debug(list2hex(APDU))
        data, sw1, sw2 = self.connection.transmit(APDU)
        logger.debug(
            "<-- received : %02x%02x : %i bytes data",
            sw1,
            sw2,
            len(data),
        )
        logger.debug(list2hex(data))
        # if sw1 == 0x69 and sw2 == 0x85:
        #     raise Exception("This command may need a secured channel")
        if sw1 == 0x69 and sw2 == 0x82:
            raise Exception("Invalid Pairing key\n")
        if sw1 == 0x6A and sw2 == 0x82:
            raise Exception(
                "Error firmware not found\nCheck a Cryptnox is connected\n"
            )
        if sw1 == 0x99 and sw2 == 0x99:
            raise Exception("Radio link was broken")
        if sw1 != 0x90 or sw2 != 0x00:
            raise Exception("Error : %02X%02X" % (sw1, sw2))
        return data

    def init(self, name, email, PIN, PUK):
        # Basic : string PIN : 9 numbers, string PUK : 12 chars
        # PIN can be 4-9 numbers for Basic version
        # bytes PUK : 12 bytes chars
        if self.initialized:
            raise Exception("Card was already initialized")
        if not hasattr(self, "SessionPubKey"):
            if not self.check_genuine():
                raise Exception("Cryptnox genuine check failed, or card connection refresh.")
        InitSessionpvKey = gen_EC_pv_key()
        AESInitKey = derive_secret(InitSessionpvKey, self.SessionPubKey)
        IVinitkey = gen16Brandom()
        PairingSecret = Basic_Pairing_Secret
        while len(PIN) < 9:
            PIN += "\0"
        InitSessionpubKey = "41" + privkey_to_pubkey(InitSessionpvKey)
        logger.debug("InitPvKey")
        logger.debug(hex(InitSessionpvKey))
        logger.debug("InitPubKey")
        logger.debug(InitSessionpubKey)
        logger.debug("PairingSecret")
        logger.debug(PairingSecret.hex())
        logger.debug("IVinit")
        logger.debug(IVinitkey.hex())
        bname = bytes(name, "ascii")
        bemail = bytes(email, "ascii")
        Data = (
            bytes([len(bname)])
            + bname
            + bytes([len(bemail)])
            + bemail
            + bytes(PIN, "ascii")
            + PUK
            + PairingSecret
        )
        logger.debug("Init Data %s", Data.hex())
        Payload = pad_data(Data)
        EncPayload = aes_encrypt(AESInitKey, IVinitkey, Payload)
        datainit = bytes.fromhex(InitSessionpubKey) + IVinitkey + EncPayload
        APDUinit = [0x80, 0xFE, 0x00, 0x00, 82 + len(EncPayload)] + bin2list(datainit)
        self.send_apdu(APDUinit)
        if hasattr(self, "SessionPubKey"):
            # Since the applet initializes the secure channel with a new session key
            delattr(self, "SessionPubKey")
        self.initialized = True
        return bytes([0]) + PairingSecret

    def get_manufacturer_cert(self):
        # Read the manufacturer certificate (hex)
        # Called by instantiation to get card SN ID
        if self.cardtype == 66 or self.cardtype == 69 or self.cardtype == 78:  # Basic or EOS or NFT
            idx_page = 0
            mnft_cert_resp = self.send_apdu([0x80, 0xF7, 0x00, idx_page, 0x00])
            if len(mnft_cert_resp) == 0:
                return ""
            certlen = (mnft_cert_resp[0] << 8) + mnft_cert_resp[1]
            while len(mnft_cert_resp) < (certlen + 2):
                idx_page += 1
                mnft_cert_resp = mnft_cert_resp + self.send_apdu([0x80, 0xF7, 0x00, idx_page, 0x00])
        else:
            mnft_cert_resp = self.send_apdu([0x80, 0xF7, 0x00, 0x00, 0x00, 0x00, 0x00])
        assert len(mnft_cert_resp) == (certlen + 2)
        cert = mnft_cert_resp[2:]
        return list2hex(cert)

    def get_card_certificate(self, nonce):
        # Read the card certificate
        # nonce is a 64 bits integer
        # card cert is : 'C' + ..
        nonce_list = hex2list("%0.16X" % nonce)
        res = self.send_apdu([0x80, 0xF8, 0x00, 0x00] + [8] + nonce_list)
        return res

    def check_genuine(self):
        PubKey_Mnft_hex = (
            "04"
            "d9e6b0fb5fbdb835cadd4703748555f55c65a12a79f7b3ca02a2c7048912ad34"
            "6080df7e09e73952adfa9f176219f5772c43826ae69642e31251d9b9ff9955d3"
        )
        mnft_cert_hex = self.get_manufacturer_cert()
        logger.debug("Mft cert")
        logger.debug(mnft_cert_hex)
        # extract card SN ID from cert
        certparts = mnft_cert_hex.split("0302010202")
        if len(certparts) > 1:
            try:
                if certparts[1][1] == "8":
                    self.SNID = int(certparts[1][2:18], 16)
                elif certparts[1][1] == "9":
                    self.SNID = int(certparts[1][4:20], 16)
                else:
                    print("Bad certificate format")
                    return False
            except Exception:
                print("Bad card certificate format")
                return False
        else:
            print("No card certificate found")
            return False
        # car pub hex 65B after r1:2a8648ce3d030107034200 k1:2b8104000a034200
        pubK1OID = "2a8648ce3d030107034200"
        mnftcertparts = mnft_cert_hex.split(pubK1OID)
        if len(mnftcertparts) < 2:
            print("No ECDSA r1 Public key found")
            return False
        card_pubkey = mnftcertparts[1][:130]
        logger.debug("card pubkey hex")
        logger.debug(card_pubkey)
        # datacert_hex : prem partie + 2a8648ce3d030107034200 + pubhex
        datamnftcert = bytes.fromhex(mnftcertparts[0][8:] + pubK1OID + card_pubkey)
        logger.debug("Mnft data")
        logger.debug(datamnftcert.hex())
        # signature
        ECDSA_SHA256 = "06082a8648ce3d040302" + "03"
        datacertparts = mnft_cert_hex.split(ECDSA_SHA256)
        if len(datacertparts) < 2:
            print("No ECDSA signature found")
            return False
        len_mnftsig = int(datacertparts[1][0:2], 16)
        mnftsig_hex = datacertparts[1][2:]
        assert len(mnftsig_hex) == 2 * len_mnftsig
        if datacertparts[1][2:4] == "00":
            mnftsig_hex = datacertparts[1][4:]
        logger.debug("mft cert sig hex")
        logger.debug(mnftsig_hex)
        if not checksignature(datamnftcert, PubKey_Mnft_hex, mnftsig_hex):
            print("Wrong Cryptnox factory signature")
            return False
        nonce4cert = secrets.randbits(64)
        card_cert_hex = list2hex(self.get_card_certificate(nonce4cert))
        self.SessionPubKey = card_cert_hex[18:148]
        logger.debug("Card cert")
        logger.debug(card_cert_hex)
        # C ?
        if card_cert_hex[:2] != "43":
            logger.error("Bad card certificate header")
            return False
        # Nonce?
        if int(card_cert_hex[2:18], 16) != nonce4cert:
            logger.error("Card certificate nonce is not the one provided")
            return False
        card_cert_msg = bytes.fromhex(card_cert_hex[:148])
        card_cert_sig_hex = card_cert_hex[148:]
        logger.debug("Card msg")
        logger.debug(card_cert_msg.hex())
        logger.debug("Card sig")
        logger.debug(card_cert_sig_hex)
        logger.debug("Card ephemeral pub key")
        logger.debug(self.SessionPubKey)
        if not checksignature(card_cert_msg, card_pubkey, card_cert_sig_hex):
            logger.error("Wrong card signature with card (pub)key")
            logger.debug("Message signed : %s", card_cert_msg.hex())
            logger.debug("Card signature : %s", card_cert_sig_hex)
            return False
        return True

    def send_enc_apdu(self, APDUh, APDUdata, RcvLong=False):
        # send encrypted APDU :
        #    APDUh   : integer list of the APDU header
        #    APDUdata: bytes of the data payload (in clear, will be encrypted)
        if not hasattr(self, "AESkey"):
            raise Exception("Secured channel was not opened")
        lenapdu = len(APDUdata)
        logger.debug("--> sending (SCP) : %i bytes data " % len(APDUdata))
        if RcvLong or lenapdu >= 256:
            logger.debug(
                list2hex(APDUh + [0, (lenapdu) >> 8, (lenapdu) & 255] + bin2list(APDUdata))
            )
        else:
            logger.debug(list2hex(APDUh + [len(APDUdata)] + bin2list(APDUdata)))
        # Encrypt
        datap = pad_data(APDUdata)
        data_enc = aes_encrypt(self.AESkey, self.IV, datap)
        lendata = len(datap) + 16
        # Compute MAC
        if RcvLong or lendata >= 256:
            cmdh = APDUh + [0, (lendata) >> 8, (lendata) & 255]
            datamaclist = cmdh + [0] * 9
        else:
            cmdh = APDUh + [lendata]
            datamaclist = cmdh + [0] * 11
        MACdata = list2bytes(datamaclist) + data_enc
        MACval = aes_encrypt(self.MACkey, self.MACiv, MACdata)[-16:]
        # Send ADPU
        dataAPDU = MACval + data_enc
        replist = self.send_apdu(cmdh + bin2list(dataAPDU))
        rep = list2bytes(replist)
        # Decode response
        rep_data = rep[16:]
        repMAC = rep[:16]
        lendatarec = len(rep)
        # Check MAC
        if lendatarec >= 256:
            datamaclist = [0, lendatarec >> 8, lendatarec & 255] + [0] * 13
        else:
            datamaclist = [lendatarec & 255] + [0] * 15
        MACdatar = list2bytes(datamaclist) + rep_data
        MACvalr = aes_encrypt(self.MACkey, self.MACiv, MACdatar)[-16:]
        if MACvalr != repMAC:
            raise Exception("Error (SCP) : Bad MAC received")
        # Decrypt response
        try:
            datadec = unpad_data(aes_decrypt(self.AESkey, MACval, rep_data))
        except Exception:
            raise Exception("Error (SCP) : Error during decryption (bad padding, wrong key)")
        status = datadec[-2:]
        datarcvd = datadec[:-2]
        self.IV = repMAC
        logger.debug("<-- received (SCP) : %s : %i bytes data ", status.hex(), len(datarcvd))
        logger.debug(datarcvd.hex())
        if status != b"\x90\x00":
            raise Exception("Error (SCP) : %02X%02X" % (status[0], status[1]))
        # return bytes instead of a int list
        return datarcvd

    def open_secure_channel(self, PairingKey, PairingKeyIndex=0):
        if not self.initialized:
            raise Exception("Card is not initialized")
        if not hasattr(self, "SessionPubKey"):
            if not self.check_genuine():
                raise Exception("Cryptnox genuine check failed.")
        SessionpvKey = gen_EC_pv_key()
        SessionpubKeyHost = "41" + privkey_to_pubkey(SessionpvKey)
        data = bytes.fromhex(SessionpubKeyHost)
        APDUosc = [0x80, 0x10, PairingKeyIndex, 0x00] + bin2list(data)
        rep = self.send_apdu(APDUosc)
        if len(rep) != 32:
            raise Exception("Bad data during secure channel opening")
        # compute session keys
        SessSalt = bytes(rep[:32])
        self.IV = bytes([1] * 16)
        DHsecret = derive_secret(SessionpvKey, self.SessionPubKey)
        session_secrets = sha512(DHsecret + PairingKey + SessSalt)
        self.AESkey = session_secrets[:32]
        self.MACkey = session_secrets[32:]
        self.MACiv = bytes([0] * 16)
        self.mutual_auth()

    def mutual_auth(self):
        data = gen32Brandom()
        # data = data + sha2(data)[-4:], with IV and 48 bytes frames
        cmd = [0x80, 0x11, 0, 0]
        resp = self.send_enc_apdu(cmd, data)
        if len(resp) != 32:  # 36
            raise Exception("Bad data during secure channel testing")
        # check checksum

    def set_pairing_key(self, PKi, PK, PUK):
        SELp = [0x80, 0xDA, PKi, 0x00]
        self.send_enc_apdu(SELp, PK + PUK)

    def get_card_info(self, pk_user_idx=0):
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

    def get_user_key_info(self, pkidx):
        # Userinfo , UserPubKey
        key_data = self.get_card_info(pkidx)
        key_info = stripzero(key_data[:64])
        return key_info, key_data[64:]

    def read_user_data_slot(self, page=0):
        SELp = [0x80, 0xFA, 0, 1 + page]
        return self.send_enc_apdu(SELp, b"", True)

    def write_data(self, P1, data, P2=0):
        SELp = [0x80, 0xFC, P1, P2]
        return self.send_enc_apdu(SELp, data)

    def write_user_data_slot(self, data, page=0):
        return self.write_data(0, data, page)

    def write_custom_data_slot(self, data):
        return self.write_data(1, data)

    def get_signing_history(self, slot_hist):
        SELp = [0x80, 0xFB, slot_hist, 0x00]
        history_slot_data = self.send_enc_apdu(SELp, b"")
        if len(history_slot_data) != 36:
            raise Exception("Bad data received during signing history read")
        return history_slot_data

    def testPIN(self, pin):
        SELp = [0x80, 0x20, 0x00, 0x00]
        return self.send_enc_apdu(SELp, bytes(pin, "ascii"))

    def get_pin_left(self):
        resp_pinleft = self.testPIN("")
        return resp_pinleft[0]

    def changePIN(self, selPINPUK, newPINPUK):
        # sel PIN PUK
        # 0x00 = PIN
        # 0x01 = PUK
        SELp = [0x80, 0x21, selPINPUK, 0x00]
        if selPINPUK == 0:
            while len(newPINPUK) < 9:
                newPINPUK += b"\0"
        self.send_enc_apdu(SELp, newPINPUK)

    def changePUK(self, currentPUK, newPUK):
        self.changePIN(0x01, currentPUK + newPUK)

    def unblockPIN(self, PUK, newPIN):
        SELp = [0x80, 0x22, 0x00, 0x00]
        if self.cardtype == 66:
            while len(newPIN) < 9:
                newPIN += "\0"
        self.send_enc_apdu(SELp, PUK + bytes(newPIN, "ascii"))

    def gen_random(self, size):
        # Read random data from card
        SELg = [0x80, 0xD3, size, 0x00]
        rep_random = self.send_enc_apdu(SELg, b"")
        if len(rep_random) != size:
            raise Exception("Bad random size read")
        return rep_random

    def gen_key(self, PIN=""):
        SELg = [0x80, 0xD4, 0x00, 0x00]
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        gen_resp = self.send_enc_apdu(SELg, PINb)
        if len(gen_resp) != 0:
            raise Exception("Bad data received during key generation")
        return gen_resp

    def load_key(self, privkeyseed, PIN="", chain_code=None):
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        data = privkeyseed
        header = bytes.fromhex("A1228120")
        P1 = 1
        if chain_code is not None:
            data += bytes.fromhex("8220") + chain_code
            P1 = 2
        bytes_result = self.send_enc_apdu([0x80, 0xD0, P1, 0x00], header + data + PINb)
        if len(bytes_result) != 0:
            raise Exception("Bad data received during key generation")
        self.seeded = True
        return bytes_result

    def load_seed(self, seed, PIN=""):
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        bytes_result = self.send_enc_apdu([0x80, 0xD0, 0x03, 0x00], seed + PINb)
        if len(bytes_result) != 0:
            raise Exception("Bad data received during key generation")
        self.seeded = True
        return bytes_result

    def load_dualseed_readpubkey(self, PIN=""):
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        # First step of dual : get pubkey + sig (w Group Key)
        bytes_result = self.send_enc_apdu([0x80, 0xD0, 0x04, 0x00], PINb)
        if len(bytes_result) < 65:
            raise Exception("Bad data received during dual seed read card public key")
        return bytes_result

    def load_dualseed_loadpubkey(self, pk, PIN=""):  # Second final step of dual : send pubkey + sig
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        bytes_result = self.send_enc_apdu([0x80, 0xD0, 0x05, 0x00], pk + PINb)
        if len(bytes_result) != 0:
            raise Exception("Bad data received during key generation")
        self.seeded = True
        return bytes_result

    def derive(self, path_bin, curve="K1"):
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

    def set_pinless_path(self, PUKb, pinlesspath_bin):
        SPLPC = [0x80, 0xC1, 0x00, 0x00]
        gen_resp = self.send_enc_apdu(SPLPC, PUKb + pinlesspath_bin)
        self.seeded = len(pinlesspath_bin) > 0
        return gen_resp

    def set_pinauth(self, status, PUKb):
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
        # status = False : xpub export disabled
        # status = True : xpub output enabled
        self.set_pubexport(status, 0, PUKb)
        self.xpubread = status

    def set_clearpukey(self, status, PUKb):
        # status = False : clear public pubkey read disabled
        # status = True : clear public pubkey read enabled
        self.set_pubexport(status, 1, PUKb)
        self.clearpubrd = status

    def get_pubkey_clear(self, derivation, path_bin=b""):
        """Get the public key within clear channel"""
        # derivation
        # 0x00 = Current key
        # 0x01 = Derive
        # 0x10 added if R1
        SELe = [0x80, 0xC2, derivation, 1]
        if path_bin == b"":
            pubkeyl = self.send_apdu(SELe + [0])
        else:
            # Only for testing, should throw error
            pubkeyl = self.send_apdu(SELe + [len(path_bin)] + bin2list(path_bin))
        pubkey = bytes(pubkeyl)
        if pubkey[0] != 0x04:
            raise Exception("Bad data received during public key reading")
        return pubkey

    def get_pubkey(self, curve, path_bin=b""):
        # derivation
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
            raise Exception("Bad data received during public key reading")
        return pubkey

    def get_xpub(self):
        SELe = [0x80, 0xC2, 0, 2]
        xpubkey = self.send_enc_apdu(SELe, b"")
        return xpubkey

    def get_path(self, curvetype="K1", path=b""):
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
        """Like DECipher / SLIP17 / ECDH"""
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        bytes_result = self.send_enc_apdu([0x80, 0xC4, 0x00, 0x00], PINb + pub_key)
        if len(bytes_result) != 32:
            raise Exception("Bad data received during encrypt")
        return bytes_result

    def decrypt_with_data(self, pub_key, data, PIN=""):
        """Onchip decrypt AES from ECDH"""
        PINb = b""
        if PIN:
            PINb = PIN.encode("ascii")
            while len(PINb) < 9:
                PINb += b"\0"
        bytes_result = self.send_enc_apdu([0x80, 0xC4, 0x01, 0x00], PINb + pub_key + data)
        return bytes_result

    def sign(self, hashdata, curve, path_bin=None, sigtype=0, pin=""):
        # Derivation
        #  0x00 = Current key (k1)
        #  0x10 = Current key (r1)
        #  0x01 = Derive (k1)
        #  0x11 = Derive (r1)
        #  0x03 = PIN-less path
        # Sig type
        #  0x00 ECDSA
        #  0x01 ECDSA with EOSIO filtering
        #  0x02 Schnorr BIP340 (hash is 32 B message)
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
            raise Exception("Bad data received during signature")
        return data

    def sign_pinless(self, hash):
        COMMsig = [0x80, 0xC0, 3, 0x00]
        data = bytes(self.send_apdu(COMMsig + [32] + bin2list(hash)))
        if data[0] != 0x30:
            raise Exception("Bad data received during signature")
        signature_raw = data
        return signature_raw

    def reset(self, PUK):
        # Reset the card
        sigder = self.send_enc_apdu([0x80, 0xFD, 0, 0], PUK)
        if sigder != b"":
            raise Exception("Card not reset")
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

    def send_auth_pubkey(self, EC_auth_pub_key, DataKey, idx, PUK=b""):
        # D5 instruction, add user auth pubkey, EC_auth_pub_key is int list
        DataKeybytes = bytes(DataKey, "utf8")
        datalen = 30
        if self.cardtype == 66:  # Basic
            datalen = 64
            EC_auth_pub_key += PUK
        if len(DataKeybytes) > datalen:
            raise Exception(f"DataKey can't be longer than {datalen} chars")
        DataKeybytespad = DataKeybytes.ljust(datalen, b"\0")
        bytes_result = self.send_enc_apdu(
            [0x80, 0xD5, 0x00, 0x00], bytes([idx]) + DataKeybytespad + EC_auth_pub_key
        )
        return bytes_result

    def check_auth_sign(self, sig, msg, idx):
        # D6 instruction, over a secure channel
        # check a signature for sign auth
        bytes_result = self.send_enc_apdu([0x80, 0xD6, 0x00, 0x00], bytes([idx]) + msg + sig)
        return bytes_result

    def check_auth_challenge(self, sig, idx):
        # D6 instruction, over a secure channel
        # check a signature reponse for challenge auth
        bytes_result = self.send_enc_apdu([0x80, 0xD6, 0x02, 0x00], bytes([idx]) + sig)
        return bytes_result

    def get_challenge(self):
        # Auth User Get "Pin" challenge
        bytes_result = self.send_enc_apdu([0x80, 0xD6, 0x01, 0x00], b"")
        return bytes_result

    def get_credID(self):
        # Auth User : Get credential id of the FIDO slot
        bytes_result = self.send_enc_apdu([0x80, 0xD6, 0x03, 0x01], b"")
        return bytes_result

    def check_response(self, sig, idx):
        # Auth User Get "Pin" challenge response
        # send the signature of the challenge
        #  counter must be prepended if FIDO signature
        # 0x6985 means challenge was reset (e.g. card power cycle)
        bytes_result = self.send_enc_apdu([0x80, 0xD6, 0x02, 0x00], bytes([idx]) + sig)
        assert len(bytes_result) == 1
        return bytes_result[0]

    def del_auth(self, idx, PUK):
        # D7 instruction, over a secure channel, delete a user key for auth
        bytes_result = self.send_enc_apdu([0x80, 0xD7, 0x00, 0x00], bytes([idx]) + PUK)
        return bytes_result


def hex2list(hexstr):
    groups = re.findall("..", hexstr)
    return [int(x, 16) for x in groups]


def bin2list(binstr):
    return hex2list(binstr.hex())


def list2hex(data, sep=""):
    return sep.join(["%0.2x" % x for x in data])


def list2bytes(datalist):
    return bytes(datalist)


def read_TLV(datain, offset, flag, length):
    if datain[offset] != flag or datain[offset + 1] != length:
        raise Exception("Bad data")
    datastart = offset + 2
    return datain[datastart : datastart + length]


# generate 256b/32B random
def gen32Brandom():
    return secrets.token_bytes(nbytes=32)


# generate 128b/16B random
def gen16Brandom():
    return secrets.token_bytes(nbytes=16)


# gen key
def gen_EC_pv_key():
    # Gererates a secp 256r1 private key
    N = 115792089210356248762697446949407573529996955224135760342422259061068512044369
    d = 0
    while not 0 < d < N - 1:
        d = secrets.randbits(256)
    return d


def privkey_to_der(pvkey):
    # X962 = 1.2.840.10045.2.1, SECP256k1 = 1.3.132.0.10 = 06052B8104000A
    datahex = "303E020100301006072A8648CE3D020106052B8104000A042730250201010420" + "%064X" % pvkey
    return bytes.fromhex(datahex)


def privkey_to_der_r1(pvkey):
    # X962 = 1.2.840.10045.2.1, SECP256k1 = 1.2.840.10045.3.1.7 = 06082A8648CE3D030107
    datahex = (
        "3041020100301306072A8648CE3D020106082A8648CE3D030107042730250201010420" + "%064X" % pvkey
    )
    return bytes.fromhex(datahex)


def pubkeyhex_to_der(pubkey):
    datahex = "3056301006072A8648CE3D020106052B8104000A034200" + pubkey
    return bytes.fromhex(datahex)


def pubkeyhex_to_der_r1(pubkey):
    datahex = "3059301306072A8648CE3D020106082A8648CE3D030107034200" + pubkey
    return bytes.fromhex(datahex)


def pubkeyhex_to_pem_r1(pubkey):
    datahex = "3059301306072A8648CE3D020106082A8648CE3D030107034200" + pubkey
    data64 = base64.b64encode(bytes.fromhex(datahex))
    dataout = b"-----BEGIN PUBLIC KEY-----\n"
    dataout += data64
    dataout += b"\n-----END PUBLIC KEY-----\n"
    return dataout


def privkey_to_pubkey(priv, curve="R1"):
    if curve[-2:].upper() == "K1":
        curvo = ec.SECP256K1()
    else:
        curvo = ec.SECP256R1()
    datapk = (
        ec.derive_private_key(priv, curvo)
        .public_key()
        .public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    )
    return datapk.hex()


# Compute DH and get X for secret
def derive_secret(priv, pubhex):
    # With 256r1
    public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), bytes.fromhex(pubhex))
    private_key = ec.derive_private_key(priv, ec.SECP256R1())
    shared_key = private_key.exchange(ec.ECDH(), public_key)
    return shared_key


# sha256
def sha2(binary_data):
    return hashlib.sha256(binary_data).digest()


# sha512
def sha512(binary_data):
    return hashlib.sha512(binary_data).digest()


def aes_encrypt(key, iv, data):
    aes_cbc = Cipher(algorithms.AES(key), modes.CBC(iv))
    aese = aes_cbc.encryptor()
    e = aese.update(data) + aese.finalize()
    return e


def aes_decrypt(key, iv, datae):
    aes_cbc = Cipher(algorithms.AES(key), modes.CBC(iv))
    aesd = aes_cbc.decryptor()
    datad = aesd.update(datae) + aesd.finalize()
    return datad


def pad_data(data):
    dataarr = bytearray(data)
    dataarr.append(128)
    while len(dataarr) % 16 > 0:
        dataarr.append(0)
    return bytes(dataarr)


def unpad_data(data):
    i = len(data) - 1
    while data[i] == 0:
        i -= 1
    if data[i] != 128:
        raise Exception("Bad padding in received data")
    return data[:i]


def stripzero(databin):
    print(databin)
    return databin.rstrip(b"\00").decode("utf8")


def verify_pair_challenge(pairing_secret, challenge, challenge_response):
    return sha2(pairing_secret + challenge) == challenge_response


def compute_pair_challenge(pairing_secret, challenge):
    return sha2(pairing_secret + challenge)


def checksignature(msg, pubkey_hex, signature_hex):
    pubkey_pem = pubkeyhex_to_pem_r1(pubkey_hex)
    signature = bytes.fromhex(signature_hex)
    pubkey = serialization.load_pem_public_key(pubkey_pem)
    sigOK = False
    try:
        pubkey.verify(signature, msg, ec.ECDSA(hashes.SHA256()))
        sigOK = True
    except Exception:
        sigOK = False
    return sigOK
