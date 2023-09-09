from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.CardConnectionObserver import CardConnectionObserver
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.Exceptions import CardConnectionException, CardRequestTimeoutException
from smartcard.util import toHexString, toBytes
from smartcard.sw.SWExceptions import SWException

from .JCconstants import JCconstants
from .CardDataParser import CardDataParser
#from .TxParser import TxParser
from .ecc import ECPubkey, ECPrivkey
from .SecureChannel import SecureChannel
from .util import msg_magic, sha256d, hash_160, EncodeBase58Check
from .version import SATOCHIP_PROTOCOL_MAJOR_VERSION, SATOCHIP_PROTOCOL_MINOR_VERSION, SATOCHIP_PROTOCOL_VERSION, PYSATOCHIP_VERSION
from .certificate_validator import CertificateValidator

import hashlib
import hmac
import base64
import logging 
from os import urandom

#debug
import sys
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MSG_WARNING= ("Before you request coins to be sent to addresses in this "
                    "wallet, ensure you can pair with your device, or that you have "
                    "its seed (and passphrase, if any).  Otherwise all coins you "
                    "receive will be unspendable.")
                    
MSG_USE_2FA= ("Do you want to use 2-Factor-Authentication (2FA)?\n\n"
                "With 2FA, any transaction must be confirmed on a second device such as \n"
               "your smartphone. First you have to install the Satochip-2FA android app on \n"
               "google play. Then you have to pair your 2FA device with your Satochip \n"
               "by scanning the qr-code on the next screen. \n"
               "Warning: be sure to backup a copy of the qr-code in a safe place, \n"
               "in case you have to reinstall the app!")

SUPPORTED_XTYPES = ('standard', 'p2wpkh-p2sh', 'p2wpkh', 'p2wsh-p2sh', 'p2wsh')
XPUB_HEADERS_MAINNET = {
        'standard':    '0488b21e',  # xpub
        'p2wpkh-p2sh': '049d7cb2',  # ypub
        'p2wsh-p2sh':  '0295b43f',  # Ypub
        'p2wpkh':      '04b24746',  # zpub
        'p2wsh':       '02aa7ed3',  # Zpub
    }
XPUB_HEADERS_TESTNET = {
        'standard':    '043587cf',  # tpub
        'p2wpkh-p2sh': '044a5262',  # upub
        'p2wsh-p2sh':  '024289ef',  # Upub
        'p2wpkh':      '045f1cf6',  # vpub
        'p2wsh':       '02575483',  # Vpub
    }

# simple observer that will print on the console the card connection events.
class LogCardConnectionObserver(CardConnectionObserver):
    def update( self, cardconnection, ccevent ):
        if 'connect'==ccevent.type:
            logger.info( 'connecting to' + repr(cardconnection.getReader()) )
        elif 'disconnect'==ccevent.type:
            logger.info( 'disconnecting from' + repr(cardconnection.getReader()) )
        elif 'command'==ccevent.type:
            if (ccevent.args[0][1] in (JCconstants.INS_SETUP, JCconstants.INS_SET_2FA_KEY,
                                        JCconstants.INS_BIP32_IMPORT_SEED, JCconstants.INS_BIP32_RESET_SEED,
                                        JCconstants.INS_CREATE_PIN, JCconstants.INS_VERIFY_PIN,
                                        JCconstants.INS_CHANGE_PIN, JCconstants.INS_UNBLOCK_PIN)):
                logger.debug(f"> {toHexString(ccevent.args[0][0:5])}{(len(ccevent.args[0])-5)*' *'}")
            else:
                logger.debug(f"> {toHexString(ccevent.args[0])}")
        elif 'response'==ccevent.type:
            if []==ccevent.args[0]:
                logger.debug( f'< [] {toHexString(ccevent.args[-2:])}')
            else:
                logger.debug( f'< {toHexString(ccevent.args[0])} {toHexString(ccevent.args[-2:])}')

# a card observer that detects inserted/removed cards and initiate connection
class RemovalObserver(CardObserver):
    """A simple card observer that is notified
    when cards are inserted/removed from the system and
    prints the list of cards
    """
    def __init__(self, cc):
        self.cc=cc
        self.observer = LogCardConnectionObserver() #ConsoleCardConnectionObserver()
            
    def update(self, observable, actions):
        (addedcards, removedcards) = actions
        for card in addedcards:
            #TODO check ATR and check if more than 1 card?
            logger.info(f"+Inserted: {toHexString(card.atr)}")
            self.cc.card_present= True
            self.cc.cardservice= card
            self.cc.cardservice.connection = card.createConnection()
            self.cc.cardservice.connection.connect()
            self.cc.cardservice.connection.addObserver(self.observer)
            try:
                (response, sw1, sw2) = self.cc.card_select()
                if sw1!=0x90 or sw2!=0x00:
                    self.cc.card_disconnect()
                    break
                (response, sw1, sw2, status)= self.cc.card_get_status()
                if (sw1!=0x90 or sw2!=0x00) and (sw1!=0x9C or sw2!=0x04):
                    self.cc.card_disconnect()
                    break

                if (self.cc.needs_secure_channel):
                    self.cc.card_initiate_secure_channel()
                    
            except Exception as exc:
                logger.warning(f"Error during connection: {repr(exc)}")
            if self.cc.client is not None:
                self.cc.client.request('update_status',True)                
                
        for card in removedcards:
            logger.info(f"-Removed: {toHexString(card.atr)}")
            self.cc.card_disconnect()
                

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
    SATOCHIP_AID= [0x53,0x61,0x74,0x6f,0x43,0x68,0x69,0x70] #SatoChip
    SEEDKEEPER_AID= [0x53,0x65,0x65,0x64,0x4b,0x65,0x65,0x70,0x65,0x72]  #SatoChip

    def __init__(self, client=None, loglevel= logging.WARNING):
        logger.setLevel(loglevel)
        logger.info(f"Logging set to level: {str(loglevel)}")
        logger.debug("In __init__")
        self.logger= logger
        self.parser=CardDataParser(loglevel)
        self.client=client
        if self.client is not None:
            self.client.cc=self
        self.cardtype = AnyCardType() #TODO: specify ATR to ignore connection to wrong card types?
        self.needs_2FA = None
        self.is_seeded= None
        self.setup_done= None
        self.needs_secure_channel= None
        self.sc = None
        # cache PIN
        self.pin_nbr=None
        self.pin=None
        # SeedKeeper or Satochip?
        self.card_type= "card"
        self.cert_pem=None # PEM certificate of device, if any
        # cardservice
        self.cardservice= None #will be instantiated when a card is inserted
        try:
            self.cardrequest = CardRequest(timeout=0, cardType=self.cardtype)
            self.cardservice = self.cardrequest.waitforcard()
            #TODO check ATR and check if more than 1 card?
            self.card_present= True
        except CardRequestTimeoutException:
            self.card_present= False
        # monitor if a card is inserted or removed
        self.cardmonitor = CardMonitor()
        self.cardobserver = RemovalObserver(self)
        self.cardmonitor.addObserver(self.cardobserver)
     
    ###########################################
    #                   Applet management                        #
    ###########################################

    def card_transmit(self, plain_apdu):
        logger.debug("In card_transmit")
        while(self.card_present):
            try:
                #encrypt apdu
                ins= plain_apdu[1]
                if (self.needs_secure_channel) and (ins not in [0xA4, 0x81, 0x82, JCconstants.INS_GET_STATUS]):
                    apdu = self.card_encrypt_secure_channel(plain_apdu)
                else:
                    apdu= plain_apdu
                    
                # transmit apdu
                (response, sw1, sw2) = self.cardservice.connection.transmit(apdu)
                
                # PIN authentication is required
                if (sw1==0x9C) and (sw2==0x06):
                    (response, sw1, sw2)= self.card_verify_PIN()
                #decrypt response
                elif (sw1==0x90) and (sw2==0x00):
                    if (self.needs_secure_channel) and (ins not in [0xA4, 0x81, 0x82, JCconstants.INS_GET_STATUS]):
                        response= self.card_decrypt_secure_channel(response)
                    return (response, sw1, sw2)
                else:
                    return (response, sw1, sw2)
                
            except Exception as exc:
                logger.warning(f"Error during connection: {repr(exc)}")
                traceback.print_exc() #debug
                if self.client is not None:
                    self.client.request('show_error',"Error during connection:"+repr(exc))
                return ([], 0x00, 0x00)
        
        # no card present
        if self.client is not None:
            self.client.request('show_error','No card found! Please insert card!')
        return ([], 0x00, 0x00)
        #TODO return errror or throw exception?
            
    def card_get_ATR(self):
        logger.debug('In card_get_ATR()')
        return self.cardservice.connection.getATR()
    
    def card_disconnect(self):
        logger.debug('In card_disconnect()')
        self.pin= None #reset PIN
        self.pin_nbr= None
        self.is_seeded= None
        self.needs_2FA = None
        self.setup_done= None
        self.needs_secure_channel= None
        self.card_present= False
        self.card_type= "card"
        if self.cardservice:
            self.cardservice.connection.disconnect()
            self.cardservice= None
        if self.client is not None:
            self.client.request('update_status',False)
        # reset authentikey
        self.parser.authentikey=None
        self.parser.authentikey_coordx= None
        self.parser.authentikey_from_storage=None
        
        
    def get_sw12(self, sw1, sw2):
        return 16*sw1+sw2

    def card_select(self):
        logger.debug("In card_select")
        SELECT = [0x00, 0xA4, 0x04, 0x00, 0x08]
        apdu = SELECT + CardConnector.SATOCHIP_AID
        (response, sw1, sw2) = self.card_transmit(apdu)
        
        if sw1==0x90 and sw2==0x00:
            self.card_type="Satochip"
            logger.debug("Found a Satochip!")
        else:
            SELECT = [0x00, 0xA4, 0x04, 0x00, 0x0A]
            apdu = SELECT + CardConnector.SEEDKEEPER_AID
            (response, sw1, sw2) = self.card_transmit(apdu)
            if sw1==0x90 and sw2==0x00:
                self.card_type="SeedKeeper"
                logger.debug("Found a SeedKeeper!")
        
        return (response, sw1, sw2)

    def card_get_status(self):
        logger.debug("In card_get_status")
        cla= JCconstants.CardEdge_CLA
        ins= JCconstants.INS_GET_STATUS
        p1= 0x00
        p2= 0x00
        apdu=[cla, ins, p1, p2]
        (response, sw1, sw2)= self.card_transmit(apdu)
        d={}
        if (sw1==0x90) and (sw2==0x00):
            d["protocol_major_version"]= response[0]
            d["protocol_minor_version"]= response[1]
            d["applet_major_version"]= response[2]
            d["applet_minor_version"]= response[3]
            d["protocol_version"]= (d["protocol_major_version"]<<8)+d["protocol_minor_version"] 
            if len(response) >=8:
                d["PIN0_remaining_tries"]= response[4]
                d["PUK0_remaining_tries"]= response[5]
                d["PIN1_remaining_tries"]= response[6]
                d["PUK1_remaining_tries"]= response[7]
                self.needs_2FA= d["needs2FA"]= False #default value
            if len(response) >=9:
                self.needs_2FA= d["needs2FA"]= False if response[8]==0X00 else True
            if len(response) >=10:
                self.is_seeded= d["is_seeded"]= False if response[9]==0X00 else True
            if len(response) >=11:
	                self.setup_done= d["setup_done"]= False if response[10]==0X00 else True    
            else:
                self.setup_done= d["setup_done"]= True    
            if len(response) >=12:
                self.needs_secure_channel= d["needs_secure_channel"]= False if response[11]==0X00 else True    
            else:
                self.needs_secure_channel= d["needs_secure_channel"]= False
        
        elif (sw1==0x9c) and (sw2==0x04):
            self.setup_done= d["setup_done"]= False  
            self.is_seeded= d["is_seeded"]= False
            self.needs_secure_channel= d["needs_secure_channel"]= False
            
        else:
            logger.warning(f"Unknown error in get_status() (error code {hex(256*sw1+sw2)})")
            #raise RuntimeError(f"Unknown error in get_status() (error code {hex(256*sw1+sw2)})")
            
        return (response, sw1, sw2, d)
    
    def card_get_label(self):
    
        logger.debug("In card_get_label")
        cla= JCconstants.CardEdge_CLA
        ins= 0x3D
        p1= 0x00
        p2= 0x01 #get
        apdu=[cla, ins, p1, p2]
        (response, sw1, sw2)= self.card_transmit(apdu)
        
        if (sw1==0x90 and sw2==0x00):
            label_size= response[0]
            try:
                label= bytes(response[1:]).decode('utf8')
            except UnicodeDecodeError as e:
                logger.warning("UnicodeDecodeError while decoding card label !")
                label=  str(bytes(response[1:]))
        elif (sw1==0x6d and sw2==0x00):  # unsupported by the card  
            label= '(none)'
        else:
            logger.warning(f"Error while recovering card label: {sw1} {sw2}")
            label= '(unknown)'
        
        return (response, sw1, sw2, label)
        
    def card_set_label(self, label):
        logger.debug("In card_set_label")
        cla= JCconstants.CardEdge_CLA
        ins= 0x3D
        p1= 0x00
        p2= 0x00 #set
        
        label_list= list(label.encode('utf8'))
        data= [len(label_list)]+label_list
        lc=len(data)
        apdu=[cla, ins, p1, p2, lc]+data
        (response, sw1, sw2)= self.card_transmit(apdu)
        
        return (response, sw1, sw2)
    
    def card_setup(self,
                    pin_tries0, ublk_tries0, pin0, ublk0,
                    pin_tries1, ublk_tries1, pin1, ublk1,
                    memsize, memsize2,
                    create_object_ACL, create_key_ACL, create_pin_ACL,
                    option_flags=0, hmacsha160_key=None, amount_limit=0):
        
        logger.debug("In card_setup")
        # to do: check pin sizes < 256
        pin=[0x4D, 0x75, 0x73, 0x63, 0x6C, 0x65, 0x30, 0x30] # default pin
        cla= JCconstants.CardEdge_CLA
        ins= JCconstants.INS_SETUP
        p1=0
        p2=0
        apdu=[cla, ins, p1, p2]

        # data=[pin_length(1) | pin |
        #       pin_tries0(1) | ublk_tries0(1) | pin0_length(1) | pin0 | ublk0_length(1) | ublk0 |
        #       pin_tries1(1) | ublk_tries1(1) | pin1_length(1) | pin1 | ublk1_length(1) | ublk1 |
        #       memsize(2) | memsize2(2) | ACL(3) |
        #       option_flags(2) | hmacsha160_key(20) | amount_limit(8)]
        if option_flags==0:
            optionsize= 0
        elif option_flags&0x8000==0x8000:
            optionsize= 30
        else:
            optionsize= 2
        lc= 16+len(pin)+len(pin0)+len(pin1)+len(ublk0)+len(ublk1)+optionsize

        apdu+=[lc]
        apdu+=[len(pin)]+pin
        apdu+=[pin_tries0,  ublk_tries0, len(pin0)] + pin0 + [len(ublk0)] + ublk0
        apdu+=[pin_tries1,  ublk_tries1, len(pin1)] + pin1 + [len(ublk1)] + ublk1
        apdu+=[memsize>>8, memsize&0x00ff, memsize2>>8, memsize2&0x00ff]
        apdu+=[create_object_ACL, create_key_ACL, create_pin_ACL]
        if option_flags!=0:
            apdu+=[option_flags>>8, option_flags&0x00ff]
            apdu+= hmacsha160_key
            for i in reversed(range(8)):
                apdu+=[(amount_limit>>(8*i))&0xff]

        # send apdu (contains sensitive data!)
        (response, sw1, sw2) = self.card_transmit(apdu)
        if (sw1==0x90) and (sw2== 0x00):
            self.set_pin(0, pin0) #cache PIN value
        return (response, sw1, sw2)

    ###########################################
    #                        BIP32 commands                      #
    ###########################################

    def card_bip32_import_seed(self, seed):
        ''' Import a seed into the device
        
        Parameters: 
        seed (str | bytes | list): the seed as a hex_string or bytes or list of int

        Returns: 
        authentikey: ECPubkey object that identifies the  device
        '''
        if type(seed) is str:
            seed= list(bytes.fromhex(seed))
        elif type(seed) is bytes:
            seed= list(seed)
        
        logger.debug("In card_bip32_import_seed")
        cla= JCconstants.CardEdge_CLA
        ins= JCconstants.INS_BIP32_IMPORT_SEED
        p1= len(seed)
        p2= 0x00
        lc= len(seed)
        apdu=[cla, ins, p1, p2, lc]+seed
        
        # send apdu (contains sensitive data!)
        response, sw1, sw2 = self.card_transmit(apdu)
        
        # compute authentikey pubkey and send to chip for future use
        authentikey= None
        if (sw1==0x90) and (sw2==0x00):
            authentikey= self.card_bip32_set_authentikey_pubkey(response)
            authentikey_hex= authentikey.hex()
            logger.debug('[card_bip32_import_seed] authentikey_card= ' + authentikey_hex)
            
            # compute authentikey locally from seed 
            # TODO: remove check if authentikey is not derived from seed
            #pub_hex= self.get_authentikey_from_masterseed(seed)
            # if (pub_hex != authentikey_hex):
                # raise RuntimeError('Authentikey mismatch: local value differs from card value!')
                
            self.is_seeded= True
        elif (sw1==0x9C and sw2==0x17):
            logger.error(f"Error during secret import: card is already seeded (0x9C17)")
            raise CardError('Secure import failed: card is already seeded (0x9C17)!')
        elif (sw1==0x9C and sw2==0x0F):
            logger.error(f"Error during secret import: invalid parameter (0x9C0F)")
            raise CardError(f"Error during secret import: invalid parameter (0x9C0F)")
        
        return authentikey
    
    # def card_import_encrypted_secret(self, secret_dic):
    #     '''Import an encrypted secret (BIP32 masterseed or 2FA secret) exported from a SeedKeeper.
        
    #     The secret is encrypted using a shared key generated using ECDH with the 2 devices authentikeys.
    #     Before import can be done, the two device should be paired by importing the 
    #     Satochip-authentikey in the SeedKeeper with seedkeeper_import_secret(), 
    #     and the SeedKeeper-authentikey in the Satochip with card_import_trusted_pubkey().
         
    #     Parameters: 
    #     secret_dic: a dictionnary that defines the secret, as returned by seedkeeper_export_secret()

    #     Returns: 
    #     authentikey: ECPubkey object that identifies the  device
    #     '''
    #     logger.debug("In card_import_encrypted_secret")
        
    #     cla= JCconstants.CardEdge_CLA
    #     ins= 0xAC
    #     p1= 0x00
    #     p2= 0x00        
    #     header= list(bytes.fromhex(secret_dic['header']))[2:(2+12)]  #header= list(bytes.fromhex(secret_dic['header'][4:])) # first 2 bytes are sid
    #     iv= list(bytes.fromhex(secret_dic['iv']))
    #     secret_list= list(bytes.fromhex(secret_dic['secret_encrypted']))
    #     hmac= list(bytes.fromhex(secret_dic['hmac']))
    #     data= header + iv + [(len(secret_list)>>8), (len(secret_list)%256)] + secret_list + [len(hmac)] + hmac
    #     lc=len(data)
    #     apdu=[cla, ins, p1, p2, lc]+data
    #     response, sw1, sw2 = self.card_transmit(apdu)
    #     if (sw1==0x90 and sw2==0x00):
    #         pass 
    #     elif (sw1==0x6d and sw2==0x00):
    #         logger.error(f"Error during secret import: operation not supported by the card (0x6D00)")
    #         raise CardError(f"Error during secret import: operation not supported by the card (0x6D00)")
    #     elif (sw1==0x9C and sw2==0x17):
    #         logger.error(f"Error during secret import: card is already seeded (0x9C17)")
    #         raise CardError('Secure import failed: card is already seeded (0x9C17)!')
    #     elif (sw1==0x9C and sw2==0x18):
    #         logger.error(f"Error during secret import: card already requires 2FA (0x9C18)")
    #         raise CardError('Secure import failed: card already requires 2FA (0x9C18)!')
    #     elif (sw1==0x9C and sw2==0x0F):
    #         logger.error(f"Error during secret import: invalid parameter (0x9C0F)")
    #         raise CardError(f"Error during secret import: invalid parameter (0x9C0F)")
    #     elif (sw1==0x9C and sw2==0x33):
    #         logger.error(f"Error during secret import: wrong MAC (0x9C33)")
    #         raise CardError('Secure import failed: wrong MAC (0x9C33)!')
    #     elif (sw1==0x9C and sw2==0x34):
    #         logger.error(f"Error during secret import: wrong fingerprint (0x9C34)")
    #         raise CardError('Secure import failed: wrong fingerprint (0x9C34)!')
    #     elif (sw1==0x9C and sw2==0x35):
    #         logger.error(f"Error during secret import: no TrustedPubkey (0x9C35)")
    #         raise CardError('Secure import failed: TrustedPubkey (0x9C35)!')
    #     else:
    #         logger.error(f"Error during secret import (error code {hex(256*sw1+sw2)})")
    #         raise UnexpectedSW12Error(f"Unexpected error during secure secret import (error code {hex(256*sw1+sw2)})")
        
    #     secret_type= header[0]
    #     if  secret_type==0x10:
    #         authentikey= self.parser.parse_bip32_get_authentikey(response)
    #         authentikey_hex= authentikey.get_public_key_bytes(True).hex()
    #         logger.debug('authentikey_card= ' + authentikey_hex)
    #         return authentikey
    #     elif  secret_type==0xB0:
    #         return None
            
    # def card_import_trusted_pubkey(self, pubkey_list):
    #     ''' Import a trusted ec pubkey into the device. This pubkey will be used for the secure import of a secret
        
    #     Parameters: 
    #     pubkey_list: the pubkey in uncompressed form (65 bytes) as a hex_string or bytes or list of int

    #     Returns: 
    #     pubkey_hex: the pubkey as a hex string (65*2 hex chars)
    #     '''
    #     logger.debug("In card_import_trusted_pubkey")
    #     if type(pubkey_list) is str:
    #         pubkey_list= list(bytes.fromhex(pubkey_list))
    #     elif type(pubkey_list) is bytes:
    #         pubkey_list= list(pubkey_list)
        
    #     cla= JCconstants.CardEdge_CLA
    #     ins= 0xAA
    #     p1= 0x00
    #     p2= 0x00    
    #     pubkey_size= len(pubkey_list)
    #     if (pubkey_size !=65):
    #         raise RuntimeError(f'Error during trusted pubkey import: wrong pubkey size, expected 65 but received {pubkey_size}')
    #     data= [pubkey_size>>8, pubkey_size%256] + pubkey_list
    #     lc=len(data)
    #     apdu=[cla, ins, p1, p2, lc]+data
    #     response, sw1, sw2 = self.card_transmit(apdu)
    #     if (sw1==0x6D and sw2==0x00): 
    #         logger.error(f"Error during secret import: operation not supported by the card (0x6D00)")
    #         raise CardError(f"Error during secret import: operation not supported by the card (0x6D00)")
    #     elif (sw1==0x9C and sw2==0x17):
    #         logger.error(f"Error during secret import: card is already seeded (0x9C17)")
    #         raise CardError('Secure import failed: card is already seeded (0x9C17)!')
    #     elif (sw1==0x9C and sw2==0x0F):
    #         logger.error(f"Error during secret import: invalid parameter (0x9C0F)")
    #         raise CardError(f"Error during secret import: invalid parameter (0x9C0F)")
        
    #     pubkey_hex=self.parser.get_trusted_pubkey(response)
    #     return pubkey_hex
        
    # def card_export_trusted_pubkey(self):
    #     ''' Export the trusted ec pubkey from the device. This pubkey is used for the secure import of a secret
        
    #     Returns: 
    #     pubkey_hex: the pubkey as a hex string (65*2 hex chars)
    #     '''
    #     logger.debug("In card_export_trusted_pubkey")
    #     cla= JCconstants.CardEdge_CLA
    #     ins= 0xAB
    #     p1= 0x00
    #     p2= 0x00    
    #     apdu=[cla, ins, p1, p2]
    #     response, sw1, sw2 = self.card_transmit(apdu)
    #     if (sw1==0x9C and sw2==0x35):
    #         return 65*'00'
    #     if (sw1==0x6D and sw2==0x00): # instruction not supported
    #         return 65*'FF'
        
    #     pubkey_hex=self.parser.get_trusted_pubkey(response)
    #     return pubkey_hex
    
    # def card_export_authentikey(self):        
    #     ''' Export the device authentikey.
        
    #     The authentikey identifies uniquely the device and is also used for setting a
    #     secure channel when doing a secure import with card_import_encrypted_secret().
        
    #     Returns: 
    #     authentikey: ECPubkey object that identifies the  device
    #     '''
    #     logger.debug("In card_export_authentikey")
    #     cla= JCconstants.CardEdge_CLA
    #     ins= 0xAD
    #     p1= 0x00
    #     p2= 0x00
    #     apdu=[cla, ins, p1, p2]

    #     # send apdu
    #     response, sw1, sw2 = self.card_transmit(apdu)
    #     if (sw1==0x90) and (sw2==0x00):
    #         # compute corresponding pubkey and send to chip for future use
    #         authentikey = self.parser.parse_bip32_get_authentikey(response)
    #         return authentikey
    #     elif (sw1==0x9c and sw2==0x04):
    #         logger.info("card_bip32_get_authentikey(): Satochip is not initialized => Raising error!")
    #         raise UninitializedSeedError('Satochip is not initialized! You should create a new wallet!\n\n'+MSG_WARNING)
    #     else:
    #         logger.warning(f"Unexpected error during authentikey export (error code {hex(256*sw1+sw2)})")
    #         raise UnexpectedSW12Error(f"Unexpected error during authentikey export (error code {hex(256*sw1+sw2)})")

    
    def card_reset_seed(self, pin, hmac=[]):
        ''' Reset the seed
        
        Parameters: 
        pin  (hex-string | bytes | list): the pin required to unlock the device
        hmac (hex-string | bytes | list): the 20-byte code required if 2FA is enabled
        
        Returns: 
        (response, sw1, sw2): (list, int, int)
        '''
        logger.debug("In card_reset_seed")
        if type(pin) is str:
            pin= list(pin.encode('utf-8'))
        elif type(pin) is bytes:
            seed= list(seed)
        
        if type(hmac) is str:
            hmac= list(bytes.fromhex(hmac))
        elif type(hmac) is bytes:
            hmac= list(hmac)
        
        cla= JCconstants.CardEdge_CLA
        ins= 0x77
        p1= len(pin)
        p2= 0x00
        lc= len(pin)+len(hmac)
        apdu=[cla, ins, p1, p2, lc]+pin+hmac

        response, sw1, sw2 = self.card_transmit(apdu)
        if (sw1==0x90) and (sw2==0x00):
            self.is_seeded= False
        return (response, sw1, sw2)

    def card_bip32_get_authentikey(self):
        ''' Return the authentikey      
        
        Compared to card_export_authentikey(), this method raise UninitializedSeedError if no seed is configured in the device
        
        Returns: 
        authentikey: an ECPubkey
        '''
        logger.debug("In card_bip32_get_authentikey")
        cla= JCconstants.CardEdge_CLA
        ins= JCconstants.INS_BIP32_GET_AUTHENTIKEY
        p1= 0x00
        p2= 0x00
        apdu=[cla, ins, p1, p2]

        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)
        if sw1==0x9c and sw2==0x14:
            logger.info("card_bip32_get_authentikey(): Seed is not initialized => Raising error!")
            raise UninitializedSeedError("Satochip seed is not initialized!\n\n "+MSG_WARNING)
        if sw1==0x9c and sw2==0x04:
            logger.info("card_bip32_get_authentikey(): Satochip is not initialized => Raising error!")
            raise UninitializedSeedError('Satochip is not initialized! You should create a new wallet!\n\n'+MSG_WARNING)
        # compute corresponding pubkey and send to chip for future use
        authentikey= None
        if (sw1==0x90) and (sw2==0x00):
            authentikey = self.card_bip32_set_authentikey_pubkey(response)
            self.is_seeded=True
        return authentikey
        
    def card_bip32_set_authentikey_pubkey(self, response):
        ''' Allows to compute coordy of authentikey externally to optimize computation time
        coordy value is verified by the chip before being accepted '''
        logger.debug("In card_bip32_set_authentikey_pubkey")
        cla= JCconstants.CardEdge_CLA
        ins= 0x75
        p1= 0x00
        p2= 0x00

        authentikey= self.parser.parse_bip32_get_authentikey(response)
        if authentikey:
            coordy = list(authentikey[33:]) # authentikey in bytes (uncompressed)
            #coordy= authentikey.get_public_key_bytes(compressed=False)
            #coordy= list(coordy[33:])
            data= response + [len(coordy)&0xFF00, len(coordy)&0x00FF] + coordy
            lc= len(data)
            apdu=[cla, ins, p1, p2, lc]+data
            (response, sw1, sw2) = self.card_transmit(apdu)
        return authentikey
    
    def card_bip32_get_extendedkey(self, path):
        ''' Get the BIP32 extended key for given path
        
        Parameters: 
        path (str | bytes): the path; if given as a string, it will be converted to bytes (4 bytes for each path index)

        Returns: 
        pubkey: ECPubkey object
        chaincode: bytearray
        '''
        if (type(path)==str):
            (depth, path)= self.parser.bip32path2bytes(path)
    
        logger.debug("In card_bip32_get_extendedkey")
        cla= JCconstants.CardEdge_CLA
        ins= JCconstants.INS_BIP32_GET_EXTENDED_KEY
        p1= len(path)//4
        p2= 0x40 #option flags: 0x80:erase cache memory - 0x40: optimization for non-hardened child derivation
        lc= len(path)
        apdu=[cla, ins, p1, p2, lc]
        apdu+= path

        if self.parser.authentikey is None:
            self.card_bip32_get_authentikey()

        # send apdu
        while (True):
            (response, sw1, sw2) = self.card_transmit(apdu)

            # if there is no more memory available, erase cache...
            #if self.get_sw12(sw1,sw2)==JCconstants.SW_NO_MEMORY_LEFT:
            if (sw1==0x9C) and (sw2==0x01):
                logger.info("[card_bip32_get_extendedkey] Reset memory...")#debugSatochip
                apdu[3]=apdu[3]^0x80
                response, sw1, sw2 = self.card_transmit(apdu)
                apdu[3]=apdu[3]&0x7f # reset the flag
            # other (unexpected) error
            if (sw1!=0x90) or (sw2!=0x00):
                raise UnexpectedSW12Error(f'Unexpected error  (error code {hex(256*sw1+sw2)})')
            # check for non-hardened child derivation optimization
            elif ( (response[32]&0x80)== 0x80):
                logger.info("[card_bip32_get_extendedkey] Child Derivation optimization...")#debugSatochip
                (pubkey, chaincode)= self.parser.parse_bip32_get_extendedkey(response)
                coordy= pubkey
                coordy= list(coordy[33:])
                authcoordy= self.parser.authentikey
                authcoordy= list(authcoordy[33:])
                data= response+[len(coordy)&0xFF00, len(coordy)&0x00FF]+coordy
                apdu_opt= [cla, 0x74, 0x00, 0x00, len(data)]
                apdu_opt= apdu_opt+data
                response_opt, sw1_opt, sw2_opt = self.card_transmit(apdu_opt)
            #at this point, we have successfully received a response from the card
            else:
                (key, chaincode)= self.parser.parse_bip32_get_extendedkey(response)
                return (key, chaincode)

    def card_bip32_get_xpub(self, path, xtype, is_mainnet):
        ''' Get the BIP32 xpub for given path.
        
        Parameters: 
        path (str | bytes): the path; if given as a string, it will be converted to bytes (4 bytes for each path index)
        xtype (str): the type of transaction such as  'standard', 'p2wpkh-p2sh', 'p2wpkh', 'p2wsh-p2sh', 'p2wsh'
        is_mainnet (bool): is mainnet or testnet 
        
        Returns: 
        xpub (str): the corresponding xpub value
        '''
        assert xtype in SUPPORTED_XTYPES
        
        # path is of the form 44'/0'/1'
        logger.info(f"card_bip32_get_xpub(): path={str(path)}")#debugSatochip
        if (type(path)==str):
            (depth, bytepath)= self.parser.bip32path2bytes(path)
        
        (childkey, childchaincode)= self.card_bip32_get_extendedkey(bytepath)
        if depth == 0: #masterkey
            fingerprint= bytes([0,0,0,0])
            child_number= bytes([0,0,0,0])
        else: #get parent info
            (parentkey, parentchaincode)= self.card_bip32_get_extendedkey(bytepath[0:-4])
            fingerprint= hash_160(parentkey)[0:4]
            child_number= bytepath[-4:]
        
        xpub_header= XPUB_HEADERS_MAINNET[xtype] if is_mainnet else XPUB_HEADERS_TESTNET[xtype]
        xpub = bytes.fromhex(xpub_header) + bytes([depth]) + fingerprint + child_number + childchaincode + compress_pubkey(childkey)
        assert(len(xpub)==78)
        xpub= EncodeBase58Check(xpub)
        logger.info(f"card_bip32_get_xpub(): xpub={str(xpub)}")#debugSatochip
        return xpub
       
    ###########################################
    #           Signing commands              #
    ###########################################
    
    # def card_sign_message(self, keynbr, pubkey, message, hmac=b'', altcoin=None):
    #     ''' Sign the message with the device
        
    #     Message is prepended with a specific header as described here:
    #     https://bitcoin.stackexchange.com/questions/77324/how-are-bitcoin-signed-messages-generated
        
    #     Parameters: 
    #     keynbr (int): the key to use (0xFF for bip32 key)
    #     pubkey (ECPubkey): the pubkey used for signing; this is used for key recovery
    #     message (str | bytes): the message to sign
    #     hmac: the 20-byte hmac code required if 2FA is enabled
    #     altcoin (str | bytes): for altcoin signing
        
    #     Returns: 
    #     (response, sw1, sw2, compsig): (list, int, int, bytes)
    #     compsig is the signature in  compact 65-byte format 
    #     (https://bitcoin.stackexchange.com/questions/12554/why-the-signature-is-always-65-13232-bytes-long)
    #     '''
    #     logger.debug("In card_sign_message")
    #     if (type(message)==str):
    #         message = message.encode('utf8')
    #     if (type(altcoin)==str):
    #         altcoin = altcoin.encode('utf8')
            
    #     # return signature as byte array
    #     # data is cut into chunks, each processed in a different APDU call
    #     chunk= 128 # max APDU data=255 => chunk<=255-(4+2)
    #     buffer_offset=0
    #     buffer_left=len(message)

    #     # CIPHER_INIT - no data processed
    #     cla= JCconstants.CardEdge_CLA
    #     ins= JCconstants.INS_SIGN_MESSAGE
    #     p1= keynbr # 0xff=>BIP32 otherwise STD
    #     p2= JCconstants.OP_INIT
    #     lc= 0x4  if not altcoin else (0x4+0x1+len(altcoin))
    #     apdu=[cla, ins, p1, p2, lc]
    #     for i in reversed(range(4)):
    #         apdu+= [((buffer_left>>(8*i)) & 0xff)]
    #     if altcoin:
	#             apdu+= [len(altcoin)]
	#             apdu+=altcoin 
                
    #     # send apdu
    #     (response, sw1, sw2) = self.card_transmit(apdu)

    #     # CIPHER PROCESS/UPDATE (optionnal)
    #     while buffer_left>chunk:
    #         #cla= JCconstants.CardEdge_CLA
    #         #ins= INS_COMPUTE_CRYPT
    #         #p1= key_nbr
    #         p2= JCconstants.OP_PROCESS
    #         lc= 2+chunk
    #         apdu=[cla, ins, p1, p2, lc]
    #         apdu+=[((chunk>>8) & 0xFF), (chunk & 0xFF)]
    #         apdu+= message[buffer_offset:(buffer_offset+chunk)]
    #         buffer_offset+=chunk
    #         buffer_left-=chunk
    #         # send apdu
    #         response, sw1, sw2 = self.card_transmit(apdu)

    #     # CIPHER FINAL/SIGN (last chunk)
    #     chunk= buffer_left #following while condition, buffer_left<=chunk
    #     #cla= JCconstants.CardEdge_CLA
    #     #ins= INS_COMPUTE_CRYPT
    #     #p1= key_nbr
    #     p2= JCconstants.OP_FINALIZE
    #     lc= 2+chunk+ len(hmac)
    #     apdu=[cla, ins, p1, p2, lc]
    #     apdu+=[((chunk>>8) & 0xFF), (chunk & 0xFF)]
    #     apdu+= message[buffer_offset:(buffer_offset+chunk)]+hmac
    #     buffer_offset+=chunk
    #     buffer_left-=chunk
    #     # send apdu
    #     response, sw1, sw2 = self.card_transmit(apdu)
        
    #     # parse signature from response
    #     if (sw1!=0x90 or sw2!=0x00):
    #         logger.warning(f"Unexpected error in card_sign_message() (error code {hex(256*sw1+sw2)})") #debugSatochip
    #         compsig=b''
    #     else:
    #         # Prepend the message for signing as done inside the card!!
    #         hash = sha256d(msg_magic(message, altcoin))
    #         compsig=self.parser.parse_message_signature(response, hash, pubkey)
                
    #     return (response, sw1, sw2, compsig)

    # def card_parse_transaction(self, transaction: bytes, is_segwit=False):
    #     ''' Parse a transaction to be signed by the device
        
    #     Parameters: 
    #     transaction (bytes): the transaction to parse
    #     is_segwit (bool)
        
    #     Returns: 
    #     (response, sw1, sw2, tx_hash, needs_2fa)
    #     tx_hash (list): hash as computed by the device
    #     needs_2FA (bool): whether 2FA is required
    #     '''
    #     logger.debug("In card_parse_transaction")
    #     cla= JCconstants.CardEdge_CLA
    #     ins= JCconstants.INS_PARSE_TRANSACTION
    #     p1= JCconstants.OP_INIT
    #     p2= 0X01 if is_segwit else 0x00

    #     # init transaction data and context
    #     txparser= TxParser(transaction)
    #     while not txparser.is_parsed():

    #         chunk= txparser.parse_segwit_transaction() if is_segwit else txparser.parse_transaction()
    #         lc= len(chunk)
    #         apdu=[cla, ins, p1, p2, lc]
    #         apdu+=chunk

    #         # log state & send apdu
    #         #if (txparser.is_parsed():
    #             #lc= 86 # [hash(32) | sigsize(2) | sig | nb_input(4) | nb_output(4) | coord_actif_input(4) | amount(8)]
    #             #logCommandAPDU("cardParseTransaction - FINISH",cla, ins, p1, p2, data, lc)
    #         #elif p1== JCconstants.OP_INIT:
    #             #logCommandAPDU("cardParseTransaction-INIT",cla, ins, p1, p2, data, lc)
    #         #elif p1== JCconstants.OP_PROCESS:
    #             #logCommandAPDU("cardParseTransaction - PROCESS",cla, ins, p1, p2, data, lc)

    #         # send apdu
    #         response, sw1, sw2 = self.card_transmit(apdu)

    #         # switch to process mode after initial call to parse
    #         p1= JCconstants.OP_PROCESS
        
    #     #parse response
    #     (tx_hash, needs_2fa)= self.parser.parse_parse_transaction(response)
        
    #     return (response, sw1, sw2, tx_hash, needs_2fa)

    # def card_sign_transaction(self, keynbr, txhash, chalresponse):
    #     ''' Sign the transaction in the device
        
    #     Parameters: 
    #     keynbr (int): the key to use (0xFF for bip32 key)
    #     txhash (list): the transaction hash as returned by the device
    #     chalresponse (list): the hmac code if 2FA is enabled
        
    #     Returns: 
    #     (response, sw1, sw2)
    #     response (list): the signature in DER format
    #     '''
    #     logger.debug("In card_sign_transaction")
    #     #if (type(chalresponse)==str):
    #     #    chalresponse = list(bytes.fromhex(chalresponse))
    #     cla= JCconstants.CardEdge_CLA
    #     ins= JCconstants.INS_SIGN_TRANSACTION
    #     p1= keynbr
    #     p2= 0x00

    #     if len(txhash)!=32:
    #         raise ValueError("Wrong txhash length: " + str(len(txhash)) + "(should be 32)")
    #     elif chalresponse==None:
    #         data= txhash
    #     else:
    #         if len(chalresponse)!=20:
    #             raise ValueError("Wrong Challenge response length:"+ str(len(chalresponse)) + "(should be 20)")
    #         data= txhash + list(bytes.fromhex("8000")) + chalresponse  # 2 middle bytes for 2FA flag
    #     lc= len(data)
    #     apdu=[cla, ins, p1, p2, lc]+data

    #     # send apdu
    #     response, sw1, sw2 = self.card_transmit(apdu)
    #     return (response, sw1, sw2)
    
    def card_sign_transaction_hash(self, keynbr, txhash, chalresponse):
        ''' Sign the transaction hash in the device
        
        Parameters: 
        keynbr (int): the key to use (0xFF for bip32 key)
        txhash (list): the transaction hash 
        chalresponse (list): the hmac code if 2FA is enabled
        
        Returns: 
        (response, sw1, sw2)
        response (list): the signature in DER format
        '''
        logger.debug("In card_sign_transaction_hash")
        #if (type(chalresponse)==str):
        #    chalresponse = list(bytes.fromhex(chalresponse))
        cla= JCconstants.CardEdge_CLA
        ins= 0x7A
        p1= keynbr
        p2= 0x00

        if len(txhash)!=32:
            raise ValueError("Wrong txhash length: " + str(len(txhash)) + "(should be 32)")
        elif chalresponse==None:
            data= txhash
        else:
            if len(chalresponse)!=20:
                raise ValueError("Wrong Challenge response length:"+ str(len(chalresponse)) + "(should be 20)")
            data= txhash + list(bytes.fromhex("8000")) + chalresponse  # 2 middle bytes for 2FA flag
        lc= len(data)
        apdu=[cla, ins, p1, p2, lc]+data

        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)
        return (response, sw1, sw2)
     
    ###########################################
    #                         2FA commands                        #
    ###########################################
     
    def card_set_2FA_key(self, hmacsha160_key, amount_limit):
        ''' Enable and import 2FA in the device
        
        Parameters: 
        hmacsha160_key (bytes | list): the 20-bytes secret
        amount_limit (int): the amount 
        
        Returns: 
        (response, sw1, sw2)
        '''
        if type(hmacsha160_key) is str:
            hmacsha160_key= list(bytes.fromhex(hmacsha160_key))
        elif type(hmacsha160_key) is bytes:
            hmacsha160_key= list(hmacsha160_key)
            
        logger.debug("In card_set_2FA_key")
        cla= JCconstants.CardEdge_CLA
        ins= 0x79
        p1= 0x00
        p2= 0x00
        lc= 28 # data=[ hmacsha160_key(20) | amount_limit(8) ]
        apdu=[cla, ins, p1, p2, lc]

        apdu+= hmacsha160_key
        for i in reversed(range(8)):
            apdu+=[(amount_limit>>(8*i))&0xff]

        # send apdu (contains sensitive data!)
        (response, sw1, sw2) = self.card_transmit(apdu)
        if (sw1==0x90) and (sw2==0x00):
            self.needs_2FA= True
        return (response, sw1, sw2)

    def card_reset_2FA_key(self, chalresponse):
        ''' Disable 2FA.
        
        Parameters: 
        chalresponse (list | bytes | hex_str): the 20-bytes code to confirm
        
        Returns: 
        (response, sw1, sw2)
        '''
        logger.debug("In card_reset_2FA_key")
        if type(chalresponse) is str:
            chalresponse= list(bytes.fromhex(chalresponse))
        elif type(chalresponse) is bytes:
            chalresponse= list(chalresponse)
        
        cla= JCconstants.CardEdge_CLA
        ins= 0x78
        p1= 0x00
        p2= 0x00
        lc= 20 # data=[ hmacsha160_key(20) ]
        apdu=[cla, ins, p1, p2, lc]
        apdu+= chalresponse

        # send apdu 
        (response, sw1, sw2) = self.card_transmit(apdu)
        if (sw1==0x90) and (sw2==0x00):
            self.needs_2FA= False
        return (response, sw1, sw2)

    def card_crypt_transaction_2FA(self, msg, is_encrypt=True):
        logger.debug("In card_crypt_transaction_2FA")
        if (type(msg)==str):
            msg = msg.encode('utf8')
        msg=list(msg)
        msg_out=[]

        # CIPHER_INIT - no data processed
        cla= JCconstants.CardEdge_CLA
        ins= 0x76
        p2= JCconstants.OP_INIT
        blocksize=16
        if is_encrypt:
            p1= 0x02
            lc= 0x00
            apdu=[cla, ins, p1, p2, lc]
            # for encryption, the data is padded with PKCS#7
            size=len(msg)
            padsize= blocksize - (size%blocksize)
            msg= msg+ [padsize]*padsize
            # send apdu
            (response, sw1, sw2) = self.card_transmit(apdu)
            if sw1==0x90 and sw2==0x00:
                # extract IV & id_2FA
                IV= response[0:16]
                id_2FA= response[16:36]
                msg_out=IV
                # id_2FA is 20 bytes, should be 32 => use sha256
                from hashlib import sha256
                id_2FA= sha256(bytes(id_2FA)).hexdigest()
            elif sw1==0x9c and sw2==0x19:
                raise RuntimeError(f"Error: 2FA is not enabled (error code: {hex(256*sw1+sw2)}")
            else:
                raise UnexpectedSW12Error(f'Unexpected error code: {hex(256*sw1+sw2)}')
        else:
            p1= 0x01
            lc= 0x10
            apdu=[cla, ins, p1, p2, lc]
            # for decryption, the IV must be provided as part of the msg
            IV= msg[0:16]
            msg=msg[16:]
            apdu= apdu+IV
            if len(msg)%blocksize!=0:
                logger.info('Padding error!')
            # send apdu
            (response, sw1, sw2) = self.card_transmit(apdu)
            if sw1==0x90 and sw2==0x00:
                pass
            elif sw1==0x9c and sw2==0x19:
                raise RuntimeError(f"Error: 2FA is not enabled (error code: {hex(256*sw1+sw2)}")
            else:
                raise UnexpectedSW12Error(f'Unexpected error code: {hex(256*sw1+sw2)}')
            
        # msg is cut in chunks and each chunk is sent to the card for encryption/decryption
        # given the protocol overhead, size of each chunk is limited in size:
        # without secure channel, an APDU command is max 255 byte, so chunk<=255-(5+2)
        # with secure channel, data is encrypted and HMACed, the max size is then 152 bytes
        # (overhead: 20b mac, padding, iv, byte_size)
        chunk= 128 #152 
        buffer_offset=0
        buffer_left=len(msg)
        # CIPHER PROCESS/UPDATE (optionnal)
        while buffer_left>chunk:
            p2= JCconstants.OP_PROCESS
            lc= 2+chunk
            apdu=[cla, ins, p1, p2, lc]
            apdu+=[((chunk>>8) & 0xFF), (chunk & 0xFF)]
            apdu+= msg[buffer_offset:(buffer_offset+chunk)]
            buffer_offset+=chunk
            buffer_left-=chunk
            # send apdu
            response, sw1, sw2 = self.card_transmit(apdu)
            # extract msg
            out_size= (response[0]<<8) + response[1]
            msg_out+= response[2:2+out_size]

        # CIPHER FINAL/SIGN (last chunk)
        chunk= buffer_left #following while condition, buffer_left<=chunk
        p2= JCconstants.OP_FINALIZE
        lc= 2+chunk
        apdu=[cla, ins, p1, p2, lc]
        apdu+=[((chunk>>8) & 0xFF), (chunk & 0xFF)]
        apdu+= msg[buffer_offset:(buffer_offset+chunk)]
        buffer_offset+=chunk
        buffer_left-=chunk
        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)
        # extract msg
        out_size= (response[0]<<8) + response[1]
        msg_out+= response[2:2+out_size]

        if is_encrypt:
            #convert from list to string
            msg_out= base64.b64encode(bytes(msg_out)).decode('ascii')
            return (id_2FA, msg_out)
        else:
            #remove padding
            pad= msg_out[-1]
            msg_out=msg_out[0:-pad]
            msg_out= bytes(msg_out).decode('latin-1')#''.join(chr(i) for i in msg_out) #bytes(msg_out).decode('latin-1')
            return (msg_out)

    ###########################################
    #                         PIN commands                        #
    ###########################################
    
    # def card_create_PIN(self, pin_nbr, pin_tries, pin, ublk):
    #     logger.debug("In card_create_PIN")
    #     cla= JCconstants.CardEdge_CLA
    #     ins= JCconstants.INS_CREATE_PIN
    #     p1= pin_nbr
    #     p2= pin_tries
    #     lc= 1 + len(pin) + 1 + len(ublk)
    #     apdu=[cla, ins, p1, p2, lc] + [len(pin)] + pin + [len(ublk)] + ublk

    #     # send apdu
    #     response, sw1, sw2 = self.card_transmit(apdu)
    #     return (response, sw1, sw2)

    # #deprecated but used for testcase
    # def card_verify_PIN_deprecated(self, pin_nbr, pin):
    #     logger.debug("In card_verify_PIN_deprecated")
    #     cla= JCconstants.CardEdge_CLA
    #     ins= JCconstants.INS_VERIFY_PIN
    #     p1= pin_nbr
    #     p2= 0x00
    #     lc= len(pin)
    #     apdu=[cla, ins, p1, p2, lc] + pin
    #     # send apdu
    #     response, sw1, sw2 = self.card_transmit(apdu)
    #     return (response, sw1, sw2)

    def card_verify_PIN(self):
        logger.debug("In card_verify_PIN")
        
        while (self.card_present):
            if self.pin is None:
                is_PIN= False
                if self.client is not None:
                    msg = f'Enter the PIN for your {self.card_type}:'
                    (is_PIN, pin_0)= self.client.PIN_dialog(msg) #todo: use request?
                if is_PIN is False:
                    raise RuntimeError(('Device cannot be unlocked without PIN code!'))
                pin_0=list(pin_0)
            else:
                pin_0= self.pin
            cla= JCconstants.CardEdge_CLA
            ins= JCconstants.INS_VERIFY_PIN
            apdu=[cla, ins, 0x00, 0x00, len(pin_0)] + pin_0
            
            if (self.needs_secure_channel):
	                apdu = self.card_encrypt_secure_channel(apdu)
            response, sw1, sw2 = self.cardservice.connection.transmit(apdu)
            
            # correct PIN: cache PIN value
            if sw1==0x90 and sw2==0x00: 
                self.set_pin(0, pin_0) 
                return (response, sw1, sw2)     
            # wrong PIN, get remaining tries available (since v0.11)
            elif sw1==0x63 and (sw2 & 0xc0)==0xc0:
                self.set_pin(0, None) #reset cached PIN value
                pin_left= (sw2 & ~0xc0)
                msg = ("Wrong PIN! {} tries remaining!").format(pin_left)
                if self.client is not None:
                    self.client.request('show_error', msg)
            # wrong PIN (legacy before v0.11)    
            elif sw1==0x9c and sw2==0x02:
                self.set_pin(0, None) #reset cached PIN value
                (response2, sw1b, sw2b, d)=self.card_get_status() # get number of pin tries remaining
                pin_left= d.get("PIN0_remaining_tries",-1)
                msg = ("Wrong PIN! {} tries remaining!").format(pin_left)
                if self.client is not None:
                    self.client.request('show_error', msg)
            # blocked PIN
            elif sw1==0x9c and sw2==0x0c:
                msg = (f"Too many failed attempts! Your device has been blocked! \n\nYou need your PUK code to unblock it (error code {hex(256*sw1+sw2)})")
                if self.client is not None:
                    self.client.request('show_error', msg)
                raise RuntimeError(msg)
            # any other edge case
            else:
                self.set_pin(0, None) #reset cached PIN value
                msg = (f"Please check your card! Unexpected error (error code {hex(256*sw1+sw2)})")
                if self.client is not None:
                    self.client.request('show_error', msg)
                return (response, sw1, sw2)     
                
        #if not self.card_present:
        if self.client is not None:
            self.client.request('show_error', 'No card found! Please insert card!')
        else:
            raise RuntimeError('No card found! Please insert card!')
        return
            
    def set_pin(self, pin_nbr, pin):
        self.pin_nbr=pin_nbr
        self.pin=pin
        return

    def card_change_PIN(self, pin_nbr, old_pin, new_pin):
        logger.debug("In card_change_PIN")
        cla= JCconstants.CardEdge_CLA
        ins= JCconstants.INS_CHANGE_PIN
        p1= pin_nbr
        p2= 0x00
        lc= 1 + len(old_pin) + 1 + len(new_pin)
        apdu=[cla, ins, p1, p2, lc] + [len(old_pin)] + old_pin + [len(new_pin)] + new_pin
        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)
        
        # correct PIN: cache PIN value
        if sw1==0x90 and sw2==0x00: 
            self.set_pin(pin_nbr, new_pin) 
        # wrong PIN, get remaining tries available (since v0.11)
        elif sw1==0x63 and (sw2 & 0xc0)==0xc0:
            self.set_pin(pin_nbr, None) #reset cached PIN value
            pin_left= (sw2 & ~0xc0)
            msg = ("Wrong PIN! {} tries remaining!").format(pin_left)
            if self.client is not None:
                self.client.request('show_error', msg)
        # wrong PIN (legacy before v0.11)    
        elif sw1==0x9c and sw2==0x02: 
            self.set_pin(pin_nbr, None) #reset cached PIN value
            (response2, sw1b, sw2b, d)=self.card_get_status() # get number of pin tries remaining
            pin_left= d.get("PIN0_remaining_tries",-1)
            msg = ("Wrong PIN! {} tries remaining!").format(pin_left)
            if self.client is not None:
                self.client.request('show_error', msg)
            raise RuntimeError(msg)
        # blocked PIN
        elif sw1==0x9c and sw2==0x0c:
            msg = (f"Too many failed attempts! Your device has been blocked! \n\nYou need your PUK code to unblock it (error code {hex(256*sw1+sw2)})")
            if self.client is not None:
                self.client.request('show_error', msg)
            raise RuntimeError(msg)
	        
        return (response, sw1, sw2)      

    def card_unblock_PIN(self, pin_nbr, ublk):
        logger.debug("In card_unblock_PIN")
        cla= JCconstants.CardEdge_CLA
        ins= JCconstants.INS_UNBLOCK_PIN
        p1= pin_nbr
        p2= 0x00
        lc= len(ublk)
        apdu=[cla, ins, p1, p2, lc] + ublk
        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)
        
        # wrong PUK, get remaining tries available (since v0.11)
        if sw1==0x63 and (sw2 & 0xc0)==0xc0:
            self.set_pin(pin_nbr, None) #reset cached PIN value
            pin_left= (sw2 & ~0xc0)
            msg = ("Wrong PUK! {} tries remaining!").format(pin_left)
            if self.client is not None:
                self.client.request('show_error', msg)
        # wrong PUK (legacy before v0.11)    
        elif sw1==0x9c and sw2==0x02: 
            self.set_pin(pin_nbr, None) #reset cached PIN value
            (response2, sw1b, sw2b, d)=self.card_get_status() # get number of pin tries remaining
            pin_left= d.get("PUK0_remaining_tries",-1)
            msg = ("Wrong PUK! {} tries remaining!").format(pin_left)
            if self.client is not None:
                self.client.request('show_error', msg)
        # blocked PUK
        elif sw1==0x9c and sw2==0x0c:
            msg = (f"Too many failed attempts! Your device has been blocked! \n\nYou need your PUK code to unblock it (error code {hex(256*sw1+sw2)})")
            if self.client is not None:
                self.client.request('show_error', msg)
            raise RuntimeError(msg)
        
        return (response, sw1, sw2)

    def card_logout_all(self):
        logger.debug("In card_logout_all")
        cla= JCconstants.CardEdge_CLA
        ins= JCconstants.INS_LOGOUT_ALL
        p1= 0x00
        p2= 0x00
        lc=0
        apdu=[cla, ins, p1, p2, lc]
        # send apdu
        response, sw1, sw2 = self.card_transmit(apdu)
        self.set_pin(0, None)
        return (response, sw1, sw2)
        
    ###########################################
    #                         Secure Channel                        #
    ###########################################
    
    def card_initiate_secure_channel(self):
        logger.debug("In card_initiate_secure_channel()")
        cla= JCconstants.CardEdge_CLA
        ins= 0x81
        p1= 0x00 
        p2= 0x00
        
        # get sc
        self.sc= SecureChannel(logger.getEffectiveLevel())
        pubkey= list(self.sc.sc_pubkey_serialized)
        lc= len(pubkey) #65
        apdu=[cla, ins, p1, p2, lc] + pubkey
        
        # send apdu 
        response, sw1, sw2 = self.card_transmit(apdu) 
        
        # parse response and extract pubkey...
        peer_pubkey = self.parser.parse_initiate_secure_channel(response)
        peer_pubkey_bytes= peer_pubkey
        self.sc.initiate_secure_channel(peer_pubkey_bytes)
        
        return peer_pubkey             
       
    def card_encrypt_secure_channel(self, apdu):
        logger.debug("In card_encrypt_secure_channel()")
        cla= JCconstants.CardEdge_CLA
        ins= 0x82
        p1= 0x00 
        p2= 0x00
        
        # log plaintext apdu
        if (apdu[1] in (JCconstants.INS_SETUP, JCconstants.INS_SET_2FA_KEY,
                                JCconstants.INS_BIP32_IMPORT_SEED, JCconstants.INS_BIP32_RESET_SEED,
                                JCconstants.INS_CREATE_PIN, JCconstants.INS_VERIFY_PIN,
                                JCconstants.INS_CHANGE_PIN, JCconstants.INS_UNBLOCK_PIN)):
            logger.debug(f"Plaintext C-APDU: {toHexString(apdu[0:5])}{(len(apdu)-5)*' *'}")
        else:
            logger.debug(f"Plaintext C-APDU: {toHexString(apdu)}")
            
        (iv, ciphertext, mac)= self.sc.encrypt_secure_channel(bytes(apdu))
        data= list(iv) + [len(ciphertext)>>8, len(ciphertext)&0xff] + list(ciphertext) + [len(mac)>>8, len(mac)&0xff] + list(mac)
        lc= len(data)
        
        encrypted_apdu= [cla, ins, p1, p2, lc]+data
        
        return encrypted_apdu
    
    def card_decrypt_secure_channel(self, response):
        logger.debug("In card_decrypt_secure_channel")
        
        if len(response)==0:
            return response
        elif len(response)<18:
            raise RuntimeError('Encrypted response has wrong lenght!')
        
        iv= bytes(response[0:16])
        size= ((response[16] & 0xff)<<8) + (response[17] & 0xff)
        ciphertext= bytes(response[18:])
        if len(ciphertext)!=size:
            logger.warning(f'In card_decrypt_secure_channel: ciphertext has wrong length: expected {str(size)} got {str(len(ciphertext))}')
            raise RuntimeError('Ciphertext has wrong lenght!')
            
        plaintext= self.sc.decrypt_secure_channel(iv, ciphertext)
        
        #log response
        logger.debug( f'Plaintext R-APDU: {toHexString(plaintext)}')
        
        return plaintext
        
    #################################
    #                  SEEDKEEPER              #        
    #################################                               
        
    # def seedkeeper_generate_masterseed(self, seed_size, export_rights, label:str):
    #     logger.debug("In seedkeeper_generate_masterseed")
    #     cla= JCconstants.CardEdge_CLA
    #     ins= 0xA0
    #     p1= seed_size
    #     p2= export_rights
        
    #     label= list(label.encode('utf-8'))
    #     label_size= len(label)
    #     data= [label_size]+label
        
    #     lc= len(data)
    #     apdu=[cla, ins, p1, p2, lc]+data
        
    #     # send apdu (contains sensitive data!)
    #     response, sw1, sw2 = self.card_transmit(apdu)
    #     if (sw1==0x90) and (sw2==0x00):
    #         id= (response[0]<<8)+response[1]
    #         logger.debug(f"Masterseed generated successfully with id: {id}")
    #         fingerprint_list= response[2:2+4]
    #         fingerprint= bytes(fingerprint_list).hex()
    #     else:
    #         logger.error(f"Error during masterseed generation: {sw1} {sw2}")
    #         id=None
    #         fingerprint= None
            
    #     return (response, sw1, sw2, id, fingerprint)
    
    # def seedkeeper_generate_2FA_secret(self, export_rights, label:str):
    #     logger.debug("In seedkeeper_generate_2FA_secret")
    #     cla= JCconstants.CardEdge_CLA
    #     ins= 0xAE
    #     p1= 0x00
    #     p2= export_rights
        
    #     label= list(label.encode('utf-8'))
    #     label_size= len(label)
    #     data= [label_size]+label
        
    #     lc= len(data)
    #     apdu=[cla, ins, p1, p2, lc]+data
        
    #     # send apdu (contains sensitive data!)
    #     response, sw1, sw2 = self.card_transmit(apdu)
    #     if (sw1==0x90) and (sw2==0x00):
    #         id= (response[0]<<8)+response[1]
    #         logger.debug(f"2FA secret generated successfully with id: {id}")
    #         fingerprint_list= response[2:2+4]
    #         fingerprint= bytes(fingerprint_list).hex()
    #     else:
    #         logger.error(f"Error during masterseed generation: {sw1} {sw2}")
    #         id=None
    #         fingerprint= None
            
    #     return (response, sw1, sw2, id, fingerprint)
        
    # def seedkeeper_import_secret(self, secret_dic, sid_pubkey=None):
    #     logger.debug("In seedkeeper_import_secret")
        
    #     is_secure_import= False if (sid_pubkey is None) else True
        
    #     cla= JCconstants.CardEdge_CLA
    #     ins= 0xA1
    #     p1= 0x02 if is_secure_import else 0x01
        
    #     # OP_INIT
    #     p2= 0x01        
    #     header= list(bytes.fromhex(secret_dic['header'][4:])) 
        
    #     #data= [secret_type, export_rights, rfu1, rfu2, label_size] + label_list + [(sid_pubkey>>8)%256, sid_pubkey%256] + iv
    #     data=  header
    #     if (is_secure_import):
    #         iv= list(bytes.fromhex(secret_dic['iv']))
    #         data+= [(sid_pubkey>>8)%256, sid_pubkey%256] + iv
    #     lc=len(data)
    #     apdu=[cla, ins, p1, p2, lc]+data
    #     response, sw1, sw2 = self.card_transmit(apdu)
    #     if (sw1!=0x90 or sw2!=0x00):
    #         logger.error(f"Error during secret import - OP_INIT: {(sw1*256+sw2):0>4X}")
    #         raise UnexpectedSW12Error(f"Unexpected error during secure secret import (error code {hex(256*sw1+sw2)})")
            
    #     # OP_PROCESS
    #     p2= 0x02
    #     chunk_size=128;
    #     if (is_secure_import):
    #         secret_list= list(bytes.fromhex(secret_dic['secret_encrypted']))
    #     else:
    #         secret_list= secret_dic['secret_list']
    #     secret_offset= 0
    #     secret_remaining= len(secret_list)
    #     while (secret_remaining>chunk_size):
    #         data= [(chunk_size>>8), (chunk_size%256)] + secret_list[secret_offset:(secret_offset+chunk_size)]
    #         lc=len(data)
    #         apdu=[cla, ins, p1, p2, lc]+data
    #         response, sw1, sw2 = self.card_transmit(apdu)
    #         if (sw1!=0x90 or sw2!=0x00):
    #             logger.error(f"Error during secret import - OP_PROCESS (error code {hex(256*sw1+sw2)})")
    #             raise UnexpectedSW12Error(f"Unexpected error during secure secret import (error code {hex(256*sw1+sw2)})")
    #         secret_offset+=chunk_size
    #         secret_remaining-=chunk_size
        
    #     # OP_FINAL
    #     p2= 0x03
    #     data= [(secret_remaining>>8), (secret_remaining%256)] + secret_list[secret_offset:(secret_offset+secret_remaining)]
    #     if (is_secure_import):
    #         hmac= list(bytes.fromhex(secret_dic['hmac']))
    #         data+= [len(hmac)] + hmac
    #     lc=len(data)
    #     apdu=[cla, ins, p1, p2, lc]+data
    #     response, sw1, sw2 = self.card_transmit(apdu)
    #     if (sw1==0x9C and sw2==0x33):
    #         logger.error(f"Error during secret import - OP_FINAL: wrong mac (error code {hex(256*sw1+sw2)})")
    #         raise SeedKeeperError(f"Error during secret import: wrong mac (error code {hex(256*sw1+sw2)})")
    #     elif (sw1!=0x90 or sw2!=0x00):
    #         logger.error(f"Error during secret import - OP_FINAL (error code {hex(256*sw1+sw2)})")
    #         raise UnexpectedSW12Error(f"Unexpected error during secure secret import (error code {hex(256*sw1+sw2)})")
    #     secret_offset+=chunk_size
    #     secret_remaining=0
        
    #     # check fingerprint
    #     id= response[0]*256+response[1]
    #     fingerprint_list= response[2:6]
    #     fingerprint_from_seedkeeper= bytes(fingerprint_list).hex()
    #     if (is_secure_import):
    #         fingerprint_from_secret= secret_dic['fingerprint'] 
    #     else:
    #         fingerprint_from_secret= hashlib.sha256(bytes(secret_list)).hexdigest()[0:8]
    #     if (fingerprint_from_secret == fingerprint_from_seedkeeper ):
    #         logger.debug("Fingerprints match !")
    #     else:
    #         logger.error(f"Fingerprint mismatch: expected {fingerprint_from_secret} but recovered {fingerprint_from_seedkeeper} ")
         
    #     return id, fingerprint_from_seedkeeper
        
    # def seedkeeper_export_secret(self, sid, sid_pubkey= None):
    #     logger.debug("In seedkeeper_export_secret")
        
    #     is_secure_export= False if (sid_pubkey is None) else True
        
    #     cla= JCconstants.CardEdge_CLA
    #     ins= 0xA2
    #     p1= 0x02 if is_secure_export else 0x01
    #     p2= 0x01
        
    #     data= [(sid>>8)%256, sid%256]
    #     if (is_secure_export):
    #         data+=[(sid_pubkey>>8)%256, sid_pubkey%256]
    #     lc=len(data)
    #     apdu=[cla, ins, p1, p2, lc]+data
        
    #     # initial call
    #     response, sw1, sw2 = self.card_transmit(apdu)
    #     if (sw1==0x90 and sw2==0x00):
    #         pass
    #     elif (sw1==0x9c and sw2==0x31):
    #         logger.warning("Export failed: export not allowed by SeedKeeper policy.")
    #         raise SeedKeeperError("Export failed: export not allowed by SeedKeeper policy.")
    #     elif (sw1==0x9c and sw2==0x08):
    #         logger.warning("Export failed: secret not found")
    #         raise SeedKeeperError("Export failed: secret not found")
    #     elif (sw1==0x9c and sw2==0x30):
    #         logger.warning("Export failed: lock error - try again")
    #         #TODO: try again?
    #         raise SeedKeeperError("Export failed: lock error - try again")
    #     else:
    #         logger.warning(f"Unexpected error (error code {hex(256*sw1+sw2)})")
    #         raise UnexpectedSW12Error(f"Unexpected error (error code {hex(256*sw1+sw2)})")
            
    #     # parse header
    #     secret_dict= self.parser.parse_seedkeeper_header(response)
    #     # iv
    #     if (is_secure_export):
    #         iv=  response[-16:] #todo: parse also in parse_seedkeeper_header()?
    #         logger.debug("IV:"+ bytes(iv).hex())
    #         secret_dict['iv_list']=iv
    #         secret_dict['iv']= bytes(iv).hex()
                
    #     secret=[]
    #     p2= 0x02
    #     apdu=[cla, ins, p1, p2, lc]+data
    #     while(True):
            
    #         response, sw1, sw2 = self.card_transmit(apdu)
    #         # parse data
    #         response_size= len(response)
    #         chunk_size= (response[0]<<8)+response[1]
    #         chunk= response[2:(2+chunk_size)]
    #         secret+= chunk
            
    #         # check if last chunk
    #         if (chunk_size+2<response_size):
    #             offset= chunk_size+2
    #             sign_size=  (response[offset]<<8)+response[offset+1]
    #             offset+=2
    #             sign= response[offset:(offset+sign_size)]
                
    #             # check signature
    #             full_data=secret_dict['header_list']+secret
    #             if (sign_size==20):
    #                 secret_dict['hmac_list']=sign
    #                 secret_dict['hmac']=bytes(sign).hex()
    #             else:
    #                 self.parser.verify_signature(full_data, sign, self.parser.authentikey)
    #                 secret_dict['sign_list']=sign
    #                 secret_dict['sign']=bytes(sign).hex()
    #             secret_dict['full_data_list']= full_data
    #             secret_dict['full_data']= bytes(full_data).hex()
    #             break
    #     secret_dict['secret_list']= secret
    #     if is_secure_export:
    #         secret_dict['secret_encrypted']= bytes(secret).hex()
    #     else:
    #         secret_dict['secret']= bytes(secret).hex()
    #     #logger.debug(f"Secret: {secret_dict['secret']}")
    #     #TODO: parse secret depending to type for all possible cases
        
    #     # check fingerprint
    #     if not is_secure_export:
    #         secret_dict['fingerprint_from_secret']= hashlib.sha256(bytes(secret)).hexdigest()[0:8]
    #         if ( secret_dict['fingerprint_from_secret'] == secret_dict['fingerprint'] ):
    #             logger.debug("Fingerprints match !")
    #         else:
    #             logger.error(f"Fingerprint mismatch: expected {secret_dict['fingerprint']} but recovered {secret_dict['fingerprint_from_secret']} ")
            
    #     return secret_dict
    
    # def seedkeeper_list_secret_headers(self):
    #     logger.debug("In seedkeeper_list_secret_headers")
    #     cla= JCconstants.CardEdge_CLA
    #     ins= 0xA6
    #     p1= 0x00
        
    #     # init
    #     headers=[]
    #     p2= 0x01
    #     apdu=[cla, ins, p1, p2]
    #     response, sw1, sw2 = self.card_transmit(apdu)
        
    #     while (sw1==0x90 and sw2==0x00):
    #         secret_dict= self.parser.parse_seedkeeper_header(response)
    #         headers+=[secret_dict]
    #         #todo: verif signature
            
    #         # next object
    #         p2= 0x02
    #         apdu=[cla, ins, p1, p2]
    #         response, sw1, sw2 = self.card_transmit(apdu)
        
    #     if  (sw1==0x90 and sw2==0x00):
    #         pass
    #     elif (sw1==0x9C and sw2==0x12):
    #         logger.debug(f"No more object in memory")
    #     elif (sw1==0x9C and sw2==0x04):
    #         logger.warning(f"UninitializedSeedError during object listing: {sw1} {sw2}")
    #         raise UninitializedSeedError("SeedKeeper is not initialized!")
    #     else:
    #         logger.warning(f"Unexpected error during object listing (error code {hex(256*sw1+sw2)})")
    #         raise UnexpectedSW12Error(f"Unexpected error during object listing (error code {hex(256*sw1+sw2)})")
            
    #     return headers

    # def seedkeeper_print_logs(self, print_all=True):
    #     logger.debug("In seedkeeper_print_logs")
    #     cla= JCconstants.CardEdge_CLA
    #     ins= 0xA9
    #     p1= 0x00
        
    #     # init
    #     p2= 0x01
    #     apdu=[cla, ins, p1, p2]
    #     response, sw1, sw2 = self.card_transmit(apdu)
        
    #     # first log
    #     logs=[]
    #     log_size=7;
    #     if (sw1==0x90 and sw2==0x00):
    #         nbtotal_logs= response[0]*256+response[1]
    #         nbavail_logs= response[2]*256+response[3]
    #         logger.debug("nbtotal_logs: "+ str(nbtotal_logs))
    #         logger.debug("nbavail_logs: "+ str(nbavail_logs))
    #         if len(response)>=4+log_size:
    #             (opins, id1, id2, res)= self.parser.parse_seedkeeper_log(response[4:4+log_size])
    #             logs=logs+[[opins, id1, id2, res]]
    #             logger.debug("Latest log: "+ str(logs[0]))
    #         else:
    #             logger.debug("No logs available!")           
    #     elif (sw1==0x9C and sw2==0x04):
    #         logger.warning(f"UninitializedSeedError during object listing: {sw1} {sw2}")
    #         raise UninitializedSeedError("SeedKeeper is not initialized!")
    #     else:
    #         logger.warning(f"Unexpected error during object listing (error code {hex(256*sw1+sw2)})")
    #         raise UnexpectedSW12Error(f"Unexpected error during object listing (error code {hex(256*sw1+sw2)})")    
            
    #     #next logs
    #     p2= 0x02
    #     apdu=[cla, ins, p1, p2]
    #     counter=0
    #     while (print_all and sw1==0x90 and sw2==0x00):
            
    #         response, sw1, sw2 = self.card_transmit(apdu)
    #         if (len(response)==0):
    #             break
                
    #         while (len(response)>=log_size):
    #             (opins, id1, id2, res)= self.parser.parse_seedkeeper_log(response[0:log_size])
    #             logger.debug("Next log: "+ str([opins, id1, id2, res]))
    #             logs=logs+[[opins, id1, id2, res]]
    #             response= response[log_size:]
            
    #         counter+=1
    #         if (counter>100): # safe break; should never happen
    #             logger.warning(f"Counter exceeded during log printing: {counter}")
    #             break
            
    #     if (sw1!=0x90 or sw2!=0x00):
    #         logger.warning(f"Error during log printing: {sw1} {sw2}")
        
    #     #debug: print logs
    #     logger.debug(f"LOGS size: {len(logs)}")
    #     i=0
    #     for log in logs:
    #         (opins, id1, id2, res)= log
    #         logger.debug(f"index: {i} | {hex(opins)} {id1} {id2} {hex(res)}")
    #         i+=1
            
    #     return (logs, nbtotal_logs, nbavail_logs)
    
    # def make_header(self, secret_type, export_rights, label):
    #     dic_type= {'BIP39 mnemonic':0x30, 'Electrum mnemonic':0x40, 'Masterseed':0x10, 'Secure import from json':0x00, 
    #                             'Public Key':0x70, 'Authentikey from TrustStore':0x70, 'Password':0x90, 'Authentikey certificate':0xA0, '2FA secret':0xB0}
    #     dic_export_rights={'Export in plaintext allowed':0x01 , 'Export encrypted only':0x02}
    #     id=2*[0x00]
    #     if type(secret_type) is str:
    #         itype= dic_type[secret_type]
    #     else:
    #         itype= secret_type
    #     origin= 0x00
    #     if type(export_rights) is str:
    #         export= dic_export_rights[export_rights]
    #     else:
    #         export= export_rights
    #     export_counters=3*[0x00]
    #     fingerprint= 4*[0x00]
    #     rfu=2*[0x00]
    #     label_size= len(label)
    #     label_list= list(label.encode('utf8'))
    #     header_list= id + [itype, origin, export] + export_counters + fingerprint + rfu + [label_size] + label_list
    #     header_hex= bytes(header_list).hex()
    #     return header_hex
    
    #################################
    #                   PERSO PKI                 #        
    #################################    
    def card_export_perso_pubkey(self):
        logger.debug("In card_export_perso_pubkey")
        cla= JCconstants.CardEdge_CLA
        ins= JCconstants.INS_EXPORT_PKI_PUBKEY
        p1= 0x00
        p2= 0x00
        apdu=[cla, ins, p1, p2]
        response, sw1, sw2 = self.card_transmit(apdu)
        if (sw1==0x90 and sw2==0x00):
            pass
        elif (sw1==0x6D and sw2==0x00):
            logger.error(f"Error during personalization pubkey export: command unsupported(0x6D00")
            raise CardError(f"Error during personalization pubkey export: command unsupported (0x6D00)")
        else: 
            logger.error(f"Error during personalization pubkey export (error code {hex(256*sw1+sw2)})")
            raise UnexpectedSW12Error(f"Error during personalization pubkey export (error code {hex(256*sw1+sw2)})")
        return response
    
    def card_export_perso_certificate(self):
        logger.debug("In card_export_perso_certificate")
        cla= JCconstants.CardEdge_CLA
        ins= JCconstants.INS_EXPORT_PKI_CERTIFICATE
        p1= 0x00
        p2= 0x01 #init
        
        #init
        apdu=[cla, ins, p1, p2]
        response, sw1, sw2 = self.card_transmit(apdu)
        if (sw1==0x90 and sw2==0x00):
            pass
        elif (sw1==0x6D and sw2==0x00):
            logger.error(f"Error during personalization certificate export: command unsupported(0x6D00)")
            raise CardError(f"Error during personalization certificate export: command unsupported (0x6D00)")
        elif (sw1==0x00 and sw2==0x00):
            logger.error(f"Error during personalization certificate export: no card present(0x0000)")
            raise CardNotPresentError(f"Error during personalization certificate export: no card present (0x0000)")
        else: 
            logger.error(f"Error during personalization certificate export: (error code {hex(256*sw1+sw2)})")
            raise UnexpectedSW12Error(f"Error during personalization certificate export: (error code {hex(256*sw1+sw2)})")
        
        certificate_size= (response[0] & 0xFF)*256 + (response[1] & 0xFF)
        if (certificate_size==0):
            return "(empty)"
                
        # UPDATE apdu: certificate data in chunks
        p2= 0x02 #update
        certificate= certificate_size*[0]
        chunk_size=128;
        chunk=[]
        remaining_size= certificate_size;
        cert_offset=0;
        while(remaining_size>128):
            # data=[ chunk_offset(2b) | chunk_size(2b) ]
            data= [ ((cert_offset>>8)&0xFF), (cert_offset&0xFF) ]
            data+= [ 0,  (chunk_size & 0xFF) ] 
            apdu=[cla, ins, p1, p2, len(data)]+data
            response, sw1, sw2 = self.card_transmit(apdu)
            certificate[cert_offset:(cert_offset+chunk_size)]=response[0:chunk_size]
            remaining_size-=chunk_size;
            cert_offset+=chunk_size;
        
        # last chunk
        data= [ ((cert_offset>>8)&0xFF), (cert_offset&0xFF) ]
        data+= [ 0,  (remaining_size & 0xFF) ] 
        apdu=[cla, ins, p1, p2, len(data)]+data
        response, sw1, sw2 = self.card_transmit(apdu)
        certificate[cert_offset:(cert_offset+remaining_size)]=response[0:remaining_size]    
        
        # parse and return raw certificate
        self.cert_pem= self.parser.convert_bytes_to_string_pem(certificate)
        return self.cert_pem
    
    def card_challenge_response_pki(self, pubkey):
        logger.debug("In card_challenge_response_pki")
        cla= JCconstants.CardEdge_CLA
        ins= JCconstants.INS_CHALLENGE_RESPONSE_PKI
        p1= 0x00
        p2= 0x00
        
        challenge_from_host= urandom(32)
        
        apdu=[cla, ins, p1, p2, len(challenge_from_host)]+ list(challenge_from_host)
        response, sw1, sw2 = self.card_transmit(apdu)
        
        # verify challenge-response
        verif= self.parser.verify_challenge_response_pki(response, challenge_from_host, pubkey)
        
        return verif;
    
    
    #################################
    #                     HELPERS                 #        
    ################################# 
    
    # #deprecated
    # def get_authentikey_from_masterseed(self, masterseed):
    #     # compute authentikey locally from masterseed
    #     # authentikey privkey is first 32 bytes of HmacSha512('Bitcoin seed2', masterseed)
    #     bytekey= bytes('Bitcoin seed2', 'utf8') #b'Bitcoin seed2'
    #     byteseed= bytes(masterseed)
    #     mac= hmac.new(bytekey, byteseed, hashlib.sha512).digest()[0:32]
    #     priv= ECPrivkey(mac)
    #     pub= priv.get_public_key_bytes(True)
    #     pub_hex= pub.hex()
    #     logger.debug('Authentikey_local= ' + pub_hex)
        
    #     return pub_hex

# class AuthenticationError(Exception):
#     """Raised when the command requires authentication first"""
#     pass

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

# class SeedKeeperError(Exception):
#     """Raised when an error is returned by the SeedKeeper"""
#     pass   
    

# if __name__ == "__main__":

#     cardconnector= CardConnector()
#     cardconnector.card_get_ATR()
#     cardconnector.card_select()
#     #cardconnector.card_setup()
#     cardconnector.card_bip32_get_authentikey()
#     #cardconnector.card_bip32_get_extendedkey()
#     cardconnector.card_disconnect()
