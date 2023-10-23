#!/usr/bin/python3
# -*- coding: utf8 -*-

# Satochip smartcard applet commands
# Copyright (C) 2023  BitLogiK & Satochip

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from smartcard.System import readers
from smartcard.CardConnection import CardConnection
from smartcard.util import toHexString
from smartcard.Exceptions import CardConnectionException

from cryptolib.cryptography import Hash160, compress_pubkey
from cryptolib.base58 import encode_base58

from .JCconstants import JCconstants
from .CardDataParser import CardDataParser
from .SecureChannel import SecureChannel
from .version import (
    SATOCHIP_PROTOCOL_MAJOR_VERSION,
    SATOCHIP_PROTOCOL_MINOR_VERSION,
    SATOCHIP_PROTOCOL_VERSION,
    PYSATOCHIP_VERSION,
)
from .CertificateValidator import CertificateValidator

import hashlib
import hmac
import base64
import logging
from os import urandom

# debug
import sys
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MSG_WARNING = (
    "Before you request coins to be sent to addresses in this "
    "wallet, ensure you can pair with your device, or that you have "
    "its seed (and passphrase, if any).  Otherwise all coins you "
    "receive will be unspendable."
)

MSG_USE_2FA = (
    "Do you want to use 2-Factor-Authentication (2FA)?\n\n"
    "With 2FA, any transaction must be confirmed on a second device such as \n"
    "your smartphone. First you have to install the Satochip-2FA android app on \n"
    "google play. Then you have to pair your 2FA device with your Satochip \n"
    "by scanning the qr-code on the next screen. \n"
    "Warning: be sure to backup a copy of the qr-code in a safe place, \n"
    "in case you have to reinstall the app!"
)

SUPPORTED_XTYPES = ("standard", "p2wpkh-p2sh", "p2wpkh", "p2wsh-p2sh", "p2wsh")
XPUB_HEADERS_MAINNET = {
    "standard": "0488b21e",  # xpub
    "p2wpkh-p2sh": "049d7cb2",  # ypub
    "p2wsh-p2sh": "0295b43f",  # Ypub
    "p2wpkh": "04b24746",  # zpub
    "p2wsh": "02aa7ed3",  # Zpub
}
XPUB_HEADERS_TESTNET = {
    "standard": "043587cf",  # tpub
    "p2wpkh-p2sh": "044a5262",  # upub
    "p2wsh-p2sh": "024289ef",  # Upub
    "p2wpkh": "045f1cf6",  # vpub
    "p2wsh": "02575483",  # Vpub
}


class SatochipException(Exception):
    """Satochip generic exception."""

    pass


class SatochipPinException(Exception):
    """Satochip PIN exception."""

    def __init__(self, msg, pin_left):
        self.msg = msg
        self.pin_left = pin_left


class CardConnector:
    # Satochip supported version tuple
    # v0.4: getBIP32ExtendedKey also returns chaincode
    # v0.5: Support for Segwit transaction
    # v0.6: bip32 optimization: speed up computation during derivation of non-hardened child
    # v0.7: add 2-Factor-Authentication (2FA) support
    # v0.8: support seed reset and pin change
    # v0.9: patch message signing for alts
    # v0.10: sign tx hash
    # v0.11: support for (mandatory) secure channel
    # v0.12: support for SeedKeeper &  factory-reset & Perso certificate & card label
    # define the apdus used in this script
    SATOCHIP_AID = [0x53, 0x61, 0x74, 0x6F, 0x43, 0x68, 0x69, 0x70]  # SatoChip

    def __init__(self, client=None, loglevel=logging.WARNING):
        logger.setLevel(loglevel)
        logger.info(f"Logging set to level: {str(loglevel)}")
        logger.debug("In __init__")
        self.logger = logger
        self.parser = CardDataParser(loglevel)
        self.validator = CertificateValidator(loglevel)
        self.client = client
        if self.client is not None:
            self.client.cc = self
        self.status = None
        self.needs_2FA = None
        self.is_seeded = None
        self.setup_done = None
        self.needs_secure_channel = None
        self.sc = None
        # cache PIN
        self.pin_nbr = None
        self.pin = None
        # SeedKeeper or Satochip?
        self.card_type = "card"
        self.cert_pem = None  # PEM certificate of device, if any

        # Search for a Satochip and connect to it
        card_present = False
        readers_list = readers()
        if len(readers_list) > 0:
            logger.debug("Available smartcard readers : %s", readers_list)
            for r in readers_list:
                if not str(r).startswith("Yubico") and "hello" not in str(r).lower():
                    try:
                        logger.debug("Trying with reader : %s", r)
                        self.connection = r.createConnection()
                        self.connection.connect(CardConnection.T1_protocol)
                        logger.debug("Before card_Select...")
                        self.card_select()
                        logger.debug("After card_Select...")
                        card_present = hasattr(self, "connection")
                    except Exception as ex:
                        logger.debug(f"Failed with this reader: {ex}")
                        pass
                if card_present:
                    logger.debug("A Satochip was detected, using %s", r)
                    (response, sw1, sw2, self.status) = self.card_get_status()
                    if (sw1 != 0x90 or sw2 != 0x00) and (sw1 != 0x9C or sw2 != 0x04):
                        self.card_disconnect()
                        raise Exception("Failed to get Satochip card status")
                    if self.needs_secure_channel:
                        self.card_initiate_secure_channel()
                    break
        if not card_present:
            raise Exception("Can't find any Satochip connected.")

    ###########################################
    #           Applet management             #
    ###########################################

    def card_transmit(self, plain_apdu):
        logger.debug("In card_transmit")

        # encrypt apdu
        ins = plain_apdu[1]
        if (self.needs_secure_channel) and (
            ins not in [0xA4, 0x81, 0x82, JCconstants.INS_GET_STATUS]
        ):
            apdu = self.card_encrypt_secure_channel(plain_apdu)
        else:
            apdu = plain_apdu

        # transmit apdu
        try:
            (response, sw1, sw2) = self.connection.transmit(apdu)
        except CardConnectionException as exc:
            logger.warning(f"Error during connection: {repr(exc)}")
            raise SatochipException("Satochip card was disconnected.")

        if (sw1 == 0x90) and (sw2 == 0x00):
            if (self.needs_secure_channel) and (
                ins not in [0xA4, 0x81, 0x82, JCconstants.INS_GET_STATUS]
            ):
                response = self.card_decrypt_secure_channel(response)
            return (response, sw1, sw2)
        else:
            return (response, sw1, sw2)

    def card_get_ATR(self):
        logger.debug("In card_get_ATR()")
        return self.connection.getATR()

    def card_disconnect(self):
        logger.debug("In card_disconnect()")
        self.pin = None  # reset PIN
        self.pin_nbr = None
        self.is_seeded = None
        self.needs_2FA = None
        self.setup_done = None
        self.needs_secure_channel = None
        self.card_type = "card"
        self.connection.disconnect()
        # reset authentikey
        self.parser.authentikey = None
        self.parser.authentikey_coordx = None
        self.parser.authentikey_from_storage = None

    def card_select(self):
        logger.debug("In card_select")
        SELECT = [0x00, 0xA4, 0x04, 0x00, 0x08]
        apdu = SELECT + CardConnector.SATOCHIP_AID
        (response, sw1, sw2) = self.connection.transmit(apdu)

        if sw1 == 0x90 and sw2 == 0x00:
            self.card_type = "Satochip"
            logger.debug("Found a Satochip!")
            return (response, sw1, sw2)
        else:
            logger.debug("No Satochip found!")
            raise SatochipException("No Satochip found!")

    def card_get_status(self):
        logger.debug("In card_get_status")
        cla = JCconstants.CardEdge_CLA
        ins = JCconstants.INS_GET_STATUS
        p1 = 0x00
        p2 = 0x00
        apdu = [cla, ins, p1, p2]
        (response, sw1, sw2) = self.card_transmit(apdu)
        d = {}
        if (sw1 == 0x90) and (sw2 == 0x00):
            d["protocol_major_version"] = response[0]
            d["protocol_minor_version"] = response[1]
            d["applet_major_version"] = response[2]
            d["applet_minor_version"] = response[3]
            d["protocol_version"] = (d["protocol_major_version"] << 8) + d["protocol_minor_version"]
            if len(response) >= 8:
                d["PIN0_remaining_tries"] = response[4]
                d["PUK0_remaining_tries"] = response[5]
                d["PIN1_remaining_tries"] = response[6]
                d["PUK1_remaining_tries"] = response[7]
                self.needs_2FA = d["needs2FA"] = False  # default value
            if len(response) >= 9:
                self.needs_2FA = d["needs2FA"] = False if response[8] == 0x00 else True
            if len(response) >= 10:
                self.is_seeded = d["is_seeded"] = False if response[9] == 0x00 else True
            if len(response) >= 11:
                self.setup_done = d["setup_done"] = False if response[10] == 0x00 else True
            else:
                self.setup_done = d["setup_done"] = True
            if len(response) >= 12:
                self.needs_secure_channel = d["needs_secure_channel"] = (
                    False if response[11] == 0x00 else True
                )
            else:
                self.needs_secure_channel = d["needs_secure_channel"] = False

        elif (sw1 == 0x9C) and (sw2 == 0x04):
            self.setup_done = d["setup_done"] = False
            self.is_seeded = d["is_seeded"] = False
            self.needs_secure_channel = d["needs_secure_channel"] = False

        else:
            logger.warning(f"Unknown error in get_status() (error code {hex(256*sw1+sw2)})")
            # raise RuntimeError(f"Unknown error in get_status() (error code {hex(256*sw1+sw2)})")

        return (response, sw1, sw2, d)

    def card_get_label(self):
        logger.debug("In card_get_label")
        cla = JCconstants.CardEdge_CLA
        ins = 0x3D
        p1 = 0x00
        p2 = 0x01  # get
        apdu = [cla, ins, p1, p2]
        (response, sw1, sw2) = self.card_transmit(apdu)

        if sw1 == 0x90 and sw2 == 0x00:
            label_size = response[0]
            try:
                label = bytes(response[1:]).decode("utf8")
            except UnicodeDecodeError as e:
                logger.warning("UnicodeDecodeError while decoding card label !")
                label = str(bytes(response[1:]))
        elif sw1 == 0x6D and sw2 == 0x00:  # unsupported by the card
            label = "(none)"
        else:
            logger.warning(f"Error while recovering card label: {sw1} {sw2}")
            label = "(unknown)"

        return (response, sw1, sw2, label)

    def card_set_label(self, label):
        logger.debug("In card_set_label")
        cla = JCconstants.CardEdge_CLA
        ins = 0x3D
        p1 = 0x00
        p2 = 0x00  # set

        label_list = list(label.encode("utf8"))
        data = [len(label_list)] + label_list
        lc = len(data)
        apdu = [cla, ins, p1, p2, lc] + data
        (response, sw1, sw2) = self.card_transmit(apdu)

        return (response, sw1, sw2)

    def card_setup(
        self,
        pin_tries0,
        ublk_tries0,
        pin0,
        ublk0,
        pin_tries1,
        ublk_tries1,
        pin1,
        ublk1,
        memsize,
        memsize2,
        create_object_ACL,
        create_key_ACL,
        create_pin_ACL,
        option_flags=0,
        hmacsha160_key=None,
        amount_limit=0,
    ):
        logger.debug("In card_setup")
        # to do: check pin sizes < 256
        pin = [0x4D, 0x75, 0x73, 0x63, 0x6C, 0x65, 0x30, 0x30]  # default pin
        cla = JCconstants.CardEdge_CLA
        ins = JCconstants.INS_SETUP
        p1 = 0
        p2 = 0
        apdu = [cla, ins, p1, p2]

        # data=[pin_length(1) | pin |
        #       pin_tries0(1) | ublk_tries0(1) | pin0_length(1) | pin0 | ublk0_length(1) | ublk0 |
        #       pin_tries1(1) | ublk_tries1(1) | pin1_length(1) | pin1 | ublk1_length(1) | ublk1 |
        #       memsize(2) | memsize2(2) | ACL(3) |
        #       option_flags(2) | hmacsha160_key(20) | amount_limit(8)]
        if option_flags == 0:
            optionsize = 0
        elif option_flags & 0x8000 == 0x8000:
            optionsize = 30
        else:
            optionsize = 2
        lc = 16 + len(pin) + len(pin0) + len(pin1) + len(ublk0) + len(ublk1) + optionsize

        apdu += [lc]
        apdu += [len(pin)] + pin
        apdu += [pin_tries0, ublk_tries0, len(pin0)] + pin0 + [len(ublk0)] + ublk0
        apdu += [pin_tries1, ublk_tries1, len(pin1)] + pin1 + [len(ublk1)] + ublk1
        apdu += [memsize >> 8, memsize & 0x00FF, memsize2 >> 8, memsize2 & 0x00FF]
        apdu += [create_object_ACL, create_key_ACL, create_pin_ACL]
        if option_flags != 0:
            apdu += [option_flags >> 8, option_flags & 0x00FF]
            apdu += hmacsha160_key
            for i in reversed(range(8)):
                apdu += [(amount_limit >> (8 * i)) & 0xFF]

        # send apdu (contains sensitive data!)
        (response, sw1, sw2) = self.card_transmit(apdu)
        if (sw1 == 0x90) and (sw2 == 0x00):
            self.set_pin(0, pin0)  # cache PIN value
            self.setup_done = True
        return (response, sw1, sw2)

    ###########################################
    #                        BIP32 commands                      #
    ###########################################

    def card_bip32_import_seed(self, seed):
        """Import a seed into the device

        Parameters:
        seed (str | bytes | list): the seed as a hex_string or bytes or list of int

        Returns:
        authentikey: ECPubkey object that identifies the  device
        """
        if type(seed) is str:
            seed = list(bytes.fromhex(seed))
        elif type(seed) is bytes:
            seed = list(seed)

        logger.debug("In card_bip32_import_seed")
        cla = JCconstants.CardEdge_CLA
        ins = JCconstants.INS_BIP32_IMPORT_SEED
        p1 = len(seed)
        p2 = 0x00
        lc = len(seed)
        apdu = [cla, ins, p1, p2, lc] + seed

        # send apdu (contains sensitive data!)
        response, sw1, sw2 = self.card_transmit(apdu)

        # compute authentikey pubkey and send to chip for future use
        authentikey = None
        if (sw1 == 0x90) and (sw2 == 0x00):
            authentikey = self.card_bip32_set_authentikey_pubkey(response)
            authentikey_hex = authentikey.hex()
            logger.debug("[card_bip32_import_seed] authentikey_card= " + authentikey_hex)
            self.is_seeded = True
        elif sw1 == 0x9C and sw2 == 0x17:
            logger.error(f"Error during secret import: card is already seeded (0x9C17)")
            raise CardError("Secure import failed: card is already seeded (0x9C17)!")
        elif sw1 == 0x9C and sw2 == 0x0F:
            logger.error(f"Error during secret import: invalid parameter (0x9C0F)")
            raise CardError(f"Error during secret import: invalid parameter (0x9C0F)")

        return authentikey

    def card_reset_seed(self, pin, hmac=[]):
        """Reset the seed

        Parameters:
        pin  (hex-string | bytes | list): the pin required to unlock the device
        hmac (hex-string | bytes | list): the 20-byte code required if 2FA is enabled

        Returns:
        (response, sw1, sw2): (list, int, int)
        """
        logger.debug("In card_reset_seed")
        if type(pin) is str:
            pin = list(pin.encode("utf-8"))
        elif type(pin) is bytes:
            pin = list(pin)

        if type(hmac) is str:
            hmac = list(bytes.fromhex(hmac))
        elif type(hmac) is bytes:
            hmac = list(hmac)

        cla = JCconstants.CardEdge_CLA
        ins = 0x77
        p1 = len(pin)
        p2 = 0x00
        lc = len(pin) + len(hmac)
        apdu = [cla, ins, p1, p2, lc] + pin + hmac

        response, sw1, sw2 = self.card_transmit(apdu)
        if (sw1 == 0x90) and (sw2 == 0x00):
            self.is_seeded = False
        return (response, sw1, sw2)

    def card_bip32_get_authentikey(self):
        """Return the authentikey

        Compared to card_export_authentikey(), this method raise UninitializedSeedError if no seed is configured in the device

        Returns:
        authentikey: an ECPubkey
        """
        logger.debug("In card_bip32_get_authentikey")
        cla = JCconstants.CardEdge_CLA
        ins = JCconstants.INS_BIP32_GET_AUTHENTIKEY
        p1 = 0x00
        p2 = 0x00
        apdu = [cla, ins, p1, p2]

        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)
        if sw1 == 0x9C and sw2 == 0x14:
            logger.info("card_bip32_get_authentikey(): Seed is not initialized => Raising error!")
            raise UninitializedSeedError("Satochip seed is not initialized!\n\n " + MSG_WARNING)
        if sw1 == 0x9C and sw2 == 0x04:
            logger.info(
                "card_bip32_get_authentikey(): Satochip is not initialized => Raising error!"
            )
            raise UninitializedSeedError(
                "Satochip is not initialized! You should create a new wallet!\n\n" + MSG_WARNING
            )
        # compute corresponding pubkey and send to chip for future use
        authentikey = None
        if (sw1 == 0x90) and (sw2 == 0x00):
            authentikey = self.card_bip32_set_authentikey_pubkey(response)
            self.is_seeded = True
        return authentikey

    def card_bip32_set_authentikey_pubkey(self, response):
        """Allows to compute coordy of authentikey externally to optimize computation time
        coordy value is verified by the chip before being accepted"""
        logger.debug("In card_bip32_set_authentikey_pubkey")
        cla = JCconstants.CardEdge_CLA
        ins = 0x75
        p1 = 0x00
        p2 = 0x00

        authentikey = self.parser.parse_bip32_get_authentikey(response)
        if authentikey:
            coordy = list(authentikey[33:])  # authentikey in bytes (uncompressed)
            # coordy= authentikey.get_public_key_bytes(compressed=False)
            # coordy= list(coordy[33:])
            data = response + [len(coordy) & 0xFF00, len(coordy) & 0x00FF] + coordy
            lc = len(data)
            apdu = [cla, ins, p1, p2, lc] + data
            (response, sw1, sw2) = self.card_transmit(apdu)
        return authentikey

    def card_bip32_get_extendedkey(self, path):
        """Get the BIP32 extended key for given path

        Parameters:
        path (str | bytes): the path; if given as a string, it will be converted to bytes (4 bytes for each path index)

        Returns:
        pubkey: ECPubkey object
        chaincode: bytearray
        """
        if type(path) == str:
            (depth, path) = self.parser.bip32path2bytes(path)

        logger.debug("In card_bip32_get_extendedkey")
        cla = JCconstants.CardEdge_CLA
        ins = JCconstants.INS_BIP32_GET_EXTENDED_KEY
        p1 = len(path) // 4
        p2 = 0x40  # option flags: 0x80:erase cache memory - 0x40: optimization for non-hardened child derivation
        lc = len(path)
        apdu = [cla, ins, p1, p2, lc]
        apdu += path

        if self.parser.authentikey is None:
            self.card_bip32_get_authentikey()

        # send apdu
        while True:
            (response, sw1, sw2) = self.card_transmit(apdu)

            # if there is no more memory available, erase cache...
            # if self.get_sw12(sw1,sw2)==JCconstants.SW_NO_MEMORY_LEFT:
            if (sw1 == 0x9C) and (sw2 == 0x01):
                logger.info("[card_bip32_get_extendedkey] Reset memory...")  # debugSatochip
                apdu[3] = apdu[3] ^ 0x80
                response, sw1, sw2 = self.card_transmit(apdu)
                apdu[3] = apdu[3] & 0x7F  # reset the flag
            # other (unexpected) error
            if (sw1 != 0x90) or (sw2 != 0x00):
                raise UnexpectedSW12Error(f"Unexpected error  (error code {hex(256*sw1+sw2)})")
            # check for non-hardened child derivation optimization
            elif (response[32] & 0x80) == 0x80:
                logger.info(
                    "[card_bip32_get_extendedkey] Child Derivation optimization..."
                )  # debugSatochip
                (pubkey, chaincode) = self.parser.parse_bip32_get_extendedkey(response)
                coordy = pubkey
                coordy = list(coordy[33:])
                authcoordy = self.parser.authentikey
                authcoordy = list(authcoordy[33:])
                data = response + [len(coordy) & 0xFF00, len(coordy) & 0x00FF] + coordy
                apdu_opt = [cla, 0x74, 0x00, 0x00, len(data)]
                apdu_opt = apdu_opt + data
                response_opt, sw1_opt, sw2_opt = self.card_transmit(apdu_opt)
            # at this point, we have successfully received a response from the card
            else:
                (key, chaincode) = self.parser.parse_bip32_get_extendedkey(response)
                return (key, chaincode)

    def card_bip32_get_xpub(self, path, xtype, is_mainnet):
        """Get the BIP32 xpub for given path.

        Parameters:
        path (str | bytes): the path; if given as a string, it will be converted to bytes (4 bytes for each path index)
        xtype (str): the type of transaction such as  'standard', 'p2wpkh-p2sh', 'p2wpkh', 'p2wsh-p2sh', 'p2wsh'
        is_mainnet (bool): is mainnet or testnet

        Returns:
        xpub (str): the corresponding xpub value
        """
        assert xtype in SUPPORTED_XTYPES

        # path is of the form 44'/0'/1'
        logger.info(f"card_bip32_get_xpub(): path={str(path)}")  # debugSatochip
        if type(path) == str:
            (depth, bytepath) = self.parser.bip32path2bytes(path)

        (childkey, childchaincode) = self.card_bip32_get_extendedkey(bytepath)
        if depth == 0:  # masterkey
            fingerprint = bytes([0, 0, 0, 0])
            child_number = bytes([0, 0, 0, 0])
        else:  # get parent info
            (parentkey, parentchaincode) = self.card_bip32_get_extendedkey(bytepath[0:-4])
            fingerprint = Hash160(parentkey)[0:4]
            child_number = bytepath[-4:]

        xpub_header = XPUB_HEADERS_MAINNET[xtype] if is_mainnet else XPUB_HEADERS_TESTNET[xtype]
        xpub = (
            bytes.fromhex(xpub_header)
            + bytes([depth])
            + fingerprint
            + child_number
            + childchaincode
            + compress_pubkey(childkey)
        )
        assert len(xpub) == 78
        xpub = encode_base58(xpub)
        logger.info(f"card_bip32_get_xpub(): xpub={str(xpub)}")  # debugSatochip
        return xpub

    ###########################################
    #           Signing commands              #
    ###########################################

    def card_sign_transaction_hash(self, keynbr, txhash, chalresponse):
        """Sign the transaction hash in the device

        Parameters:
        keynbr (int): the key to use (0xFF for bip32 key)
        txhash (list): the transaction hash
        chalresponse (list): the hmac code if 2FA is enabled

        Returns:
        (response, sw1, sw2)
        response (list): the signature in DER format
        """
        logger.debug("In card_sign_transaction_hash")
        # if (type(chalresponse)==str):
        #    chalresponse = list(bytes.fromhex(chalresponse))
        cla = JCconstants.CardEdge_CLA
        ins = 0x7A
        p1 = keynbr
        p2 = 0x00

        if len(txhash) != 32:
            raise ValueError("Wrong txhash length: " + str(len(txhash)) + "(should be 32)")
        elif chalresponse == None:
            data = txhash
        else:
            if len(chalresponse) != 20:
                raise ValueError(
                    "Wrong Challenge response length:" + str(len(chalresponse)) + "(should be 20)"
                )
            data = (
                txhash + list(bytes.fromhex("8000")) + chalresponse
            )  # 2 middle bytes for 2FA flag
        lc = len(data)
        apdu = [cla, ins, p1, p2, lc] + data

        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)
        return (response, sw1, sw2)

    ###########################################
    #                         2FA commands                        #
    ###########################################

    def card_set_2FA_key(self, hmacsha160_key, amount_limit):
        """Enable and import 2FA in the device

        Parameters:
        hmacsha160_key (bytes | list): the 20-bytes secret
        amount_limit (int): the amount

        Returns:
        (response, sw1, sw2)
        """
        if type(hmacsha160_key) is str:
            hmacsha160_key = list(bytes.fromhex(hmacsha160_key))
        elif type(hmacsha160_key) is bytes:
            hmacsha160_key = list(hmacsha160_key)

        logger.debug("In card_set_2FA_key")
        cla = JCconstants.CardEdge_CLA
        ins = 0x79
        p1 = 0x00
        p2 = 0x00
        lc = 28  # data=[ hmacsha160_key(20) | amount_limit(8) ]
        apdu = [cla, ins, p1, p2, lc]

        apdu += hmacsha160_key
        for i in reversed(range(8)):
            apdu += [(amount_limit >> (8 * i)) & 0xFF]

        # send apdu (contains sensitive data!)
        (response, sw1, sw2) = self.card_transmit(apdu)
        if (sw1 == 0x90) and (sw2 == 0x00):
            self.needs_2FA = True
        return (response, sw1, sw2)

    def card_reset_2FA_key(self, chalresponse):
        """Disable 2FA.

        Parameters:
        chalresponse (list | bytes | hex_str): the 20-bytes code to confirm

        Returns:
        (response, sw1, sw2)
        """
        logger.debug("In card_reset_2FA_key")
        if type(chalresponse) is str:
            chalresponse = list(bytes.fromhex(chalresponse))
        elif type(chalresponse) is bytes:
            chalresponse = list(chalresponse)

        cla = JCconstants.CardEdge_CLA
        ins = 0x78
        p1 = 0x00
        p2 = 0x00
        lc = 20  # data=[ hmacsha160_key(20) ]
        apdu = [cla, ins, p1, p2, lc]
        apdu += chalresponse

        # send apdu
        (response, sw1, sw2) = self.card_transmit(apdu)
        if (sw1 == 0x90) and (sw2 == 0x00):
            self.needs_2FA = False
        return (response, sw1, sw2)

    def card_crypt_transaction_2FA(self, msg, is_encrypt=True):
        logger.debug("In card_crypt_transaction_2FA")
        if type(msg) == str:
            msg = msg.encode("utf8")
        msg = list(msg)
        msg_out = []

        # CIPHER_INIT - no data processed
        cla = JCconstants.CardEdge_CLA
        ins = 0x76
        p2 = JCconstants.OP_INIT
        blocksize = 16
        if is_encrypt:
            p1 = 0x02
            lc = 0x00
            apdu = [cla, ins, p1, p2, lc]
            # for encryption, the data is padded with PKCS#7
            size = len(msg)
            padsize = blocksize - (size % blocksize)
            msg = msg + [padsize] * padsize
            # send apdu
            (response, sw1, sw2) = self.card_transmit(apdu)
            if sw1 == 0x90 and sw2 == 0x00:
                # extract IV & id_2FA
                IV = response[0:16]
                id_2FA = response[16:36]
                msg_out = IV
                # id_2FA is 20 bytes, should be 32 => use sha256
                from hashlib import sha256

                id_2FA = sha256(bytes(id_2FA)).hexdigest()
            elif sw1 == 0x9C and sw2 == 0x19:
                raise RuntimeError(f"Error: 2FA is not enabled (error code: {hex(256*sw1+sw2)}")
            else:
                raise UnexpectedSW12Error(f"Unexpected error code: {hex(256*sw1+sw2)}")
        else:
            p1 = 0x01
            lc = 0x10
            apdu = [cla, ins, p1, p2, lc]
            # for decryption, the IV must be provided as part of the msg
            IV = msg[0:16]
            msg = msg[16:]
            apdu = apdu + IV
            if len(msg) % blocksize != 0:
                logger.info("Padding error!")
            # send apdu
            (response, sw1, sw2) = self.card_transmit(apdu)
            if sw1 == 0x90 and sw2 == 0x00:
                pass
            elif sw1 == 0x9C and sw2 == 0x19:
                raise RuntimeError(f"Error: 2FA is not enabled (error code: {hex(256*sw1+sw2)}")
            else:
                raise UnexpectedSW12Error(f"Unexpected error code: {hex(256*sw1+sw2)}")

        # msg is cut in chunks and each chunk is sent to the card for encryption/decryption
        # given the protocol overhead, size of each chunk is limited in size:
        # without secure channel, an APDU command is max 255 byte, so chunk<=255-(5+2)
        # with secure channel, data is encrypted and HMACed, the max size is then 152 bytes
        # (overhead: 20b mac, padding, iv, byte_size)
        chunk = 128  # 152
        buffer_offset = 0
        buffer_left = len(msg)
        # CIPHER PROCESS/UPDATE (optionnal)
        while buffer_left > chunk:
            p2 = JCconstants.OP_PROCESS
            lc = 2 + chunk
            apdu = [cla, ins, p1, p2, lc]
            apdu += [((chunk >> 8) & 0xFF), (chunk & 0xFF)]
            apdu += msg[buffer_offset : (buffer_offset + chunk)]
            buffer_offset += chunk
            buffer_left -= chunk
            # send apdu
            response, sw1, sw2 = self.card_transmit(apdu)
            # extract msg
            out_size = (response[0] << 8) + response[1]
            msg_out += response[2 : 2 + out_size]

        # CIPHER FINAL/SIGN (last chunk)
        chunk = buffer_left  # following while condition, buffer_left<=chunk
        p2 = JCconstants.OP_FINALIZE
        lc = 2 + chunk
        apdu = [cla, ins, p1, p2, lc]
        apdu += [((chunk >> 8) & 0xFF), (chunk & 0xFF)]
        apdu += msg[buffer_offset : (buffer_offset + chunk)]
        buffer_offset += chunk
        buffer_left -= chunk
        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)
        # extract msg
        out_size = (response[0] << 8) + response[1]
        msg_out += response[2 : 2 + out_size]

        if is_encrypt:
            # convert from list to string
            msg_out = base64.b64encode(bytes(msg_out)).decode("ascii")
            return (id_2FA, msg_out)
        else:
            # remove padding
            pad = msg_out[-1]
            msg_out = msg_out[0:-pad]
            msg_out = bytes(msg_out).decode(
                "latin-1"
            )  #''.join(chr(i) for i in msg_out) #bytes(msg_out).decode('latin-1')
            return msg_out

    ###########################################
    #             PIN commands                #
    ###########################################

    def card_verify_PIN(self, pin=None):
        """Verify card PIN using pin provided as list(bytes)
        If PIN is None, use cached value
        """
        logger.debug("In card_verify_PIN")

        if pin is None:
            if self.pin is None:
                raise RuntimeError(("Device cannot be unlocked without PIN code!"))
            else:
                pin = self.pin

        cla = JCconstants.CardEdge_CLA
        ins = JCconstants.INS_VERIFY_PIN
        apdu = [cla, ins, 0x00, 0x00, len(pin)] + pin

        if self.needs_secure_channel:
            apdu = self.card_encrypt_secure_channel(apdu)
        response, sw1, sw2 = self.connection.transmit(apdu)

        # correct PIN: cache PIN value
        if sw1 == 0x90 and sw2 == 0x00:
            self.set_pin(0, pin)
            return (response, sw1, sw2)
        # wrong PIN, get remaining tries available (since v0.11)
        elif sw1 == 0x63 and (sw2 & 0xC0) == 0xC0:
            self.set_pin(0, None)  # reset cached PIN value
            pin_left = sw2 & ~0xC0
            raise SatochipPinException(f"Wrong PIN! {pin_left} tries remaining!", pin_left)
        # wrong PIN (legacy before v0.11)
        elif sw1 == 0x9C and sw2 == 0x02:
            self.set_pin(0, None)  # reset cached PIN value
            (
                response2,
                sw1b,
                sw2b,
                self.status,
            ) = self.card_get_status()  # get number of pin tries remaining
            pin_left = self.status.get("PIN0_remaining_tries", -1)
            raise SatochipPinException(f"Wrong PIN! {pin_left} tries remaining!", pin_left)
        # blocked PIN
        elif sw1 == 0x9C and sw2 == 0x0C:
            self.set_pin(0, None)  # reset cached PIN value
            msg = f"Too many failed attempts! Your device has been blocked! \n\nYou need your PUK code to unblock it (error code {hex(256*sw1+sw2)})"
            raise SatochipPinException(msg, 0)
        # any other edge case
        else:
            self.set_pin(0, None)  # reset cached PIN value
            msg = f"Please check your card! Unexpected error (error code {hex(256*sw1+sw2)})"
            raise SatochipPinException(msg, 0)

    def set_pin(self, pin_nbr, pin):
        self.pin_nbr = pin_nbr
        self.pin = pin
        return

    def card_change_PIN(self, pin_nbr, old_pin, new_pin):
        logger.debug("In card_change_PIN")
        cla = JCconstants.CardEdge_CLA
        ins = JCconstants.INS_CHANGE_PIN
        p1 = pin_nbr
        p2 = 0x00
        lc = 1 + len(old_pin) + 1 + len(new_pin)
        apdu = [cla, ins, p1, p2, lc] + [len(old_pin)] + old_pin + [len(new_pin)] + new_pin
        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)

        # correct PIN: cache PIN value
        if sw1 == 0x90 and sw2 == 0x00:
            self.set_pin(pin_nbr, new_pin)
        # wrong PIN, get remaining tries available (since v0.11)
        elif sw1 == 0x63 and (sw2 & 0xC0) == 0xC0:
            self.set_pin(pin_nbr, None)  # reset cached PIN value
            pin_left = sw2 & ~0xC0
            msg = ("Wrong PIN! {} tries remaining!").format(pin_left)
            raise SatochipPinException(msg, pin_left)
        # wrong PIN (legacy before v0.11)
        elif sw1 == 0x9C and sw2 == 0x02:
            self.set_pin(pin_nbr, None)  # reset cached PIN value
            (
                response2,
                sw1b,
                sw2b,
                self.status,
            ) = self.card_get_status()  # get number of pin tries remaining
            pin_left = self.status.get("PIN0_remaining_tries", -1)
            msg = ("Wrong PIN! {} tries remaining!").format(pin_left)
            raise SatochipPinException(msg, pin_left)
        # blocked PIN
        elif sw1 == 0x9C and sw2 == 0x0C:
            msg = f"Too many failed attempts! Your device has been blocked! \n\nYou need your PUK code to unblock it (error code {hex(256*sw1+sw2)})"
            raise SatochipPinException(msg, 0)

        return (response, sw1, sw2)

    def card_unblock_PIN(self, pin_nbr, ublk):
        logger.debug("In card_unblock_PIN")
        cla = JCconstants.CardEdge_CLA
        ins = JCconstants.INS_UNBLOCK_PIN
        p1 = pin_nbr
        p2 = 0x00
        lc = len(ublk)
        apdu = [cla, ins, p1, p2, lc] + ublk
        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)

        # wrong PUK, get remaining tries available (since v0.11)
        if sw1 == 0x63 and (sw2 & 0xC0) == 0xC0:
            self.set_pin(pin_nbr, None)  # reset cached PIN value
            pin_left = sw2 & ~0xC0
            msg = ("Wrong PUK! {} tries remaining!").format(pin_left)
            raise SatochipPinException(msg, pin_left)
        # wrong PUK (legacy before v0.11)
        elif sw1 == 0x9C and sw2 == 0x02:
            self.set_pin(pin_nbr, None)  # reset cached PIN value
            (
                response2,
                sw1b,
                sw2b,
                self.status,
            ) = self.card_get_status()  # get number of pin tries remaining
            pin_left = self.status.get("PUK0_remaining_tries", -1)
            msg = ("Wrong PUK! {} tries remaining!").format(pin_left)
            raise SatochipPinException(msg, pin_left)
        # blocked PUK
        elif sw1 == 0x9C and sw2 == 0x0C:
            msg = f"Too many failed attempts! Your device has been bricked! \n\nYou need to reset your card to factory settings."
            raise SatochipPinException(msg, 0)

        return (response, sw1, sw2)

    def card_logout_all(self):
        logger.debug("In card_logout_all")
        cla = JCconstants.CardEdge_CLA
        ins = JCconstants.INS_LOGOUT_ALL
        p1 = 0x00
        p2 = 0x00
        lc = 0
        apdu = [cla, ins, p1, p2, lc]
        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)
        self.set_pin(0, None)
        return (response, sw1, sw2)

    ###########################################
    #             Secure Channel              #
    ###########################################

    def card_initiate_secure_channel(self):
        logger.debug("In card_initiate_secure_channel()")
        cla = JCconstants.CardEdge_CLA
        ins = 0x81
        p1 = 0x00
        p2 = 0x00

        # get sc
        self.sc = SecureChannel(logger.getEffectiveLevel())
        pubkey = list(self.sc.sc_pubkey_serialized)
        lc = len(pubkey)  # 65
        apdu = [cla, ins, p1, p2, lc] + pubkey

        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)

        # parse response and extract pubkey...
        peer_pubkey = self.parser.parse_initiate_secure_channel(response)
        peer_pubkey_bytes = peer_pubkey
        self.sc.initiate_secure_channel(peer_pubkey_bytes)

        return peer_pubkey

    def card_encrypt_secure_channel(self, apdu):
        logger.debug("In card_encrypt_secure_channel()")
        cla = JCconstants.CardEdge_CLA
        ins = 0x82
        p1 = 0x00
        p2 = 0x00

        # log plaintext apdu
        if apdu[1] in (
            JCconstants.INS_SETUP,
            JCconstants.INS_SET_2FA_KEY,
            JCconstants.INS_BIP32_IMPORT_SEED,
            JCconstants.INS_BIP32_RESET_SEED,
            JCconstants.INS_CREATE_PIN,
            JCconstants.INS_VERIFY_PIN,
            JCconstants.INS_CHANGE_PIN,
            JCconstants.INS_UNBLOCK_PIN,
        ):
            logger.debug(f"Plaintext C-APDU: {toHexString(apdu[0:5])}{(len(apdu)-5)*' *'}")
        else:
            logger.debug(f"Plaintext C-APDU: {toHexString(apdu)}")

        (iv, ciphertext, mac) = self.sc.encrypt_secure_channel(bytes(apdu))
        data = (
            list(iv)
            + [len(ciphertext) >> 8, len(ciphertext) & 0xFF]
            + list(ciphertext)
            + [len(mac) >> 8, len(mac) & 0xFF]
            + list(mac)
        )
        lc = len(data)

        encrypted_apdu = [cla, ins, p1, p2, lc] + data

        return encrypted_apdu

    def card_decrypt_secure_channel(self, response):
        logger.debug("In card_decrypt_secure_channel")

        if len(response) == 0:
            return response
        elif len(response) < 18:
            raise RuntimeError("Encrypted response has wrong lenght!")

        iv = bytes(response[0:16])
        size = ((response[16] & 0xFF) << 8) + (response[17] & 0xFF)
        ciphertext = bytes(response[18:])
        if len(ciphertext) != size:
            logger.warning(
                f"In card_decrypt_secure_channel: ciphertext has wrong length: expected {str(size)} got {str(len(ciphertext))}"
            )
            raise RuntimeError("Ciphertext has wrong lenght!")

        plaintext = self.sc.decrypt_secure_channel(iv, ciphertext)

        # log response
        logger.debug(f"Plaintext R-APDU: {toHexString(plaintext)}")

        return plaintext

    #################################
    #          PERSO PKI            #
    #################################
    def card_export_perso_pubkey(self):
        logger.debug("In card_export_perso_pubkey")
        cla = JCconstants.CardEdge_CLA
        ins = JCconstants.INS_EXPORT_PKI_PUBKEY
        p1 = 0x00
        p2 = 0x00
        apdu = [cla, ins, p1, p2]
        response, sw1, sw2 = self.card_transmit(apdu)
        if sw1 == 0x90 and sw2 == 0x00:
            pass
        elif sw1 == 0x6D and sw2 == 0x00:
            logger.error(f"Error during personalization pubkey export: command unsupported(0x6D00")
            raise CardError(
                f"Error during personalization pubkey export: command unsupported (0x6D00)"
            )
        else:
            logger.error(
                f"Error during personalization pubkey export (error code {hex(256*sw1+sw2)})"
            )
            raise UnexpectedSW12Error(
                f"Error during personalization pubkey export (error code {hex(256*sw1+sw2)})"
            )
        return response

    def card_export_perso_certificate(self):
        logger.debug("In card_export_perso_certificate")
        cla = JCconstants.CardEdge_CLA
        ins = JCconstants.INS_EXPORT_PKI_CERTIFICATE
        p1 = 0x00
        p2 = 0x01  # init

        # init
        apdu = [cla, ins, p1, p2]
        response, sw1, sw2 = self.card_transmit(apdu)
        if sw1 == 0x90 and sw2 == 0x00:
            pass
        elif sw1 == 0x6D and sw2 == 0x00:
            logger.error(
                f"Error during personalization certificate export: command unsupported(0x6D00)"
            )
            raise CardError(
                f"Error during personalization certificate export: command unsupported (0x6D00)"
            )
        elif sw1 == 0x00 and sw2 == 0x00:
            logger.error(
                f"Error during personalization certificate export: no card present(0x0000)"
            )
            raise CardNotPresentError(
                f"Error during personalization certificate export: no card present (0x0000)"
            )
        else:
            logger.error(
                f"Error during personalization certificate export: (error code {hex(256*sw1+sw2)})"
            )
            raise UnexpectedSW12Error(
                f"Error during personalization certificate export: (error code {hex(256*sw1+sw2)})"
            )

        certificate_size = (response[0] & 0xFF) * 256 + (response[1] & 0xFF)
        if certificate_size == 0:
            return "(empty)"

        # UPDATE apdu: certificate data in chunks
        p2 = 0x02  # update
        certificate = certificate_size * [0]
        chunk_size = 128
        chunk = []
        remaining_size = certificate_size
        cert_offset = 0
        while remaining_size > 128:
            # data=[ chunk_offset(2b) | chunk_size(2b) ]
            data = [((cert_offset >> 8) & 0xFF), (cert_offset & 0xFF)]
            data += [0, (chunk_size & 0xFF)]
            apdu = [cla, ins, p1, p2, len(data)] + data
            response, sw1, sw2 = self.card_transmit(apdu)
            certificate[cert_offset : (cert_offset + chunk_size)] = response[0:chunk_size]
            remaining_size -= chunk_size
            cert_offset += chunk_size

        # last chunk
        data = [((cert_offset >> 8) & 0xFF), (cert_offset & 0xFF)]
        data += [0, (remaining_size & 0xFF)]
        apdu = [cla, ins, p1, p2, len(data)] + data
        response, sw1, sw2 = self.card_transmit(apdu)
        certificate[cert_offset : (cert_offset + remaining_size)] = response[0:remaining_size]

        # parse and return raw certificate
        self.cert_pem = self.parser.convert_bytes_to_string_pem(certificate)
        return self.cert_pem

    def card_challenge_response_pki(self, pubkey):
        logger.debug("In card_challenge_response_pki")
        cla = JCconstants.CardEdge_CLA
        ins = JCconstants.INS_CHALLENGE_RESPONSE_PKI
        p1 = 0x00
        p2 = 0x00

        challenge_from_host = urandom(32)

        apdu = [cla, ins, p1, p2, len(challenge_from_host)] + list(challenge_from_host)
        response, sw1, sw2 = self.card_transmit(apdu)

        # verify challenge-response
        verif = self.parser.verify_challenge_response_pki(response, challenge_from_host, pubkey)

        return verif

    def card_verify_authenticity(self):
        logger.debug("In card_verify_authenticity")
        cert_pem = txt_error = ""
        try:
            cert_pem = self.card_export_perso_certificate()
            logger.debug("Cert PEM: " + str(cert_pem))
        except CardError as ex:
            txt_error = "".join(
                [
                    "Unable to get device certificate: feature unsupported! \n",
                    "Authenticity validation is only available starting with Satochip v0.12 and higher",
                ]
            )
        except CardNotPresentError as ex:
            txt_error = "No card found! Please insert card."
        except UnexpectedSW12Error as ex:
            txt_error = "Exception during device certificate export: " + str(ex)

        if cert_pem == "(empty)":
            txt_error = "Device certificate is empty: the card has not been personalized!"

        if txt_error != "":
            return False, "(empty)", "(empty)", "(empty)", txt_error

        # check the certificate chain from root CA to device
        (
            is_valid_chain,
            device_pubkey,
            txt_ca,
            txt_subca,
            txt_device,
            txt_error,
        ) = self.validator.validate_certificate_chain(cert_pem, self.card_type)
        if not is_valid_chain:
            return False, txt_ca, txt_subca, txt_device, txt_error

        # perform challenge-response with the card to ensure that the key is correctly loaded in the device
        is_valid_chalresp, txt_error = self.card_challenge_response_pki(device_pubkey)

        return is_valid_chalresp, txt_ca, txt_subca, txt_device, txt_error

    #################################
    #           HELPERS             #
    #################################


class UninitializedSeedError(Exception):
    """Raised when the device is not yet seeded"""

    pass


class UnexpectedSW12Error(Exception):
    """Raised when the device returns an unexpected error code"""

    pass


class CardError(Exception):
    """Raised when the device returns an error code"""

    pass


class CardNotPresentError(Exception):
    """Raised when the device returns an error code"""

    pass
