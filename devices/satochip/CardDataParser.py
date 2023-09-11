"""
 * Python API for the SatoChip Bitcoin Hardware Wallet
 * (c) 2015 by Toporin - 16DMCk4WUaHofchAhpMaQS4UPm4urcy2dN
 * Sources available on https://github.com/Toporin
 *
 * Copyright 2015 by Toporin (https://github.com/Toporin)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
"""
import logging 
import base64
from hashlib import sha256
from struct import pack, unpack

from cryptolib.cryptography import public_key_recover
from cryptolib.ECKeyPair import ECpubkey

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MSG_WARNING= ("Before you request bitcoins to be sent to addresses in this "
                    "wallet, ensure you can pair with your device, or that you have "
                    "its seed (and passphrase, if any).  Otherwise all bitcoins you "
                    "receive will be unspendable.")

class CardDataParser:

    def __init__(self, loglevel= logging.WARNING):
        logger.setLevel(loglevel)
        logger.debug("In __init__")
        self.authentikey=None # pubkey in bytes (uncompressed)
        self.authentikey_coordx= None # in bytes
        #self.authentikey_from_storage=None
    
    def bip32path2bytes(self, bip32path:str) -> (int, bytes):
        splitPath = bip32path.split('/')
        splitPath = [x for x in splitPath if x] # removes empty values
        if splitPath and splitPath[0] == 'm':
            splitPath = splitPath[1:]
            #bip32path = bip32path[2:]

        bytePath = b''
        depth = len(splitPath)
        for index in splitPath:
            if index.endswith("'"):
               bytePath += pack( ">I", int(index.rstrip("'"))+0x80000000 )
            else:
               bytePath += pack( ">I", int(index) )

        return depth, bytePath
    
    
    def parse_bip32_get_authentikey(self,response):
        # response= [data_size | data | sig_size | signature]
        # where data is coordx
        logger.debug("In parse_bip32_get_authentikey")
        data_size = ((response[0] & 0xff)<<8) + ((response[1] & 0xff))
        data= response[2:(2+data_size)]
        msg_size= 2+data_size
        msg= response[0:msg_size]
        sig_size = ((response[msg_size] & 0xff)<<8) + ((response[msg_size+1] & 0xff))
        signature= response[(msg_size+2):(msg_size+2+sig_size)]

        if sig_size==0:
           raise ValueError("Signature missing")
        # self-signed
        coordx=data
        self.authentikey= self.get_pubkey_from_signature(coordx, msg, signature)
        self.authentikey_coordx= coordx

        return self.authentikey

    def parse_bip32_import_seed(self,response):
        # response= [data_size | data | sig_size | signature]
        # where data is coordx
        logger.debug("In parse_bip32_import_seed")
        return self.parse_bip32_get_authentikey(response)

    def parse_bip32_get_extendedkey(self, response):
        logger.debug("In parse_bip32_get_extendedkey")
        if self.authentikey is None:
            raise ValueError("Authentikey not set!")

        # double signature: first is self-signed, second by authentikey
        # firs self-signed sig: data= coordx
        #logger.debug('parse_bip32_get_extendedkey: first signature recovery')
        self.chaincode= bytearray(response[0:32])
        data_size = ((response[32] & 0x7f)<<8) + (response[33] & 0xff) # (response[32] & 0x80) is ignored (optimization flag)
        data= response[34:(32+2+data_size)]
        msg_size= 32+2+data_size
        msg= response[0:msg_size]
        sig_size = ((response[msg_size] & 0xff)<<8) + (response[msg_size+1] & 0xff)
        signature= response[(msg_size+2):(msg_size+2+sig_size)]
        if sig_size==0:
           raise ValueError("Signature missing")
        # self-signed
        coordx=data
        self.pubkey= self.get_pubkey_from_signature(coordx, msg, signature)
        self.pubkey_coordx= coordx

        # second signature by authentikey
        #logger.debug('parse_bip32_get_extendedkey: second signature recovery')
        msg2_size= msg_size+2+sig_size
        msg2= response[0:msg2_size]
        sig2_size = ((response[msg2_size] & 0xff)<<8) + (response[msg2_size+1] & 0xff)
        signature2= response[(msg2_size+2):(msg2_size+2+sig2_size)]
        authentikey= self.get_pubkey_from_signature(self.authentikey_coordx, msg2, signature2)
        if authentikey != self.authentikey:
            raise ValueError("The seed used to create this wallet file no longer matches the seed of the Satochip device!\n\n"+MSG_WARNING)

        # self.pubkey, self.chaincode in bytes
        return (self.pubkey, self.chaincode)

    def parse_initiate_secure_channel(self, response):
            logger.debug("In parse_initiate_secure_channel")
            # double signature: first is self-signed, second by authentikey (optional)
            # firs self-signed sig: data= coordx
            #logger.debug(f'parse_initiate_secure_channel: first signature recovery')
            data_size = ((response[0] & 0xff)<<8) + (response[1] & 0xff)
            data= response[2:(2+data_size)]
            msg_size= 2+data_size
            msg= response[0:msg_size]
            sig_size = ((response[msg_size] & 0xff)<<8) + (response[msg_size+1] & 0xff)
            signature= response[(msg_size+2):(msg_size+2+sig_size)]
            if sig_size==0:
               raise ValueError("Signature missing")
            # self-signed
            coordx=data
            self.pubkey= self.get_pubkey_from_signature(coordx, msg, signature)
            self.pubkey_coordx= coordx
            
            # second signature by authentikey (optional)
            #logger.debug(f'parse_initiate_secure_channel: second signature recovery')
            msg2_size= msg_size+2+sig_size
            sig2_size = ((response[msg2_size] & 0xff)<<8) + (response[msg2_size+1] & 0xff)  
            if sig2_size>0 and self.authentikey_coordx:
                msg2= response[0:msg2_size]
                signature2= response[(msg2_size+2):(msg2_size+2+sig2_size)] 
                authentikey= self.get_pubkey_from_signature(self.authentikey_coordx, msg2, signature2)
                if ( authentikey != self.authentikey ):
                    raise ValueError("Recovered authentikey does not correspond to registered authentikey!")
                logger.info("In parse_initiate_secure_channel: successfuly recovered authentikey:"+ authentikey.hex()) #debug
                    
            logger.info("In parse_initiate_secure_channel: successfuly recovered pubkey:"+ self.pubkey.hex()) #debug
            return (self.pubkey)


    def get_pubkey_from_signature(self, coordx, data, dersig):

        #logger.debug("In get_pubkey_from_signature")
        data= bytearray(data)
        dersig= bytearray(dersig)
        coordx= bytearray(coordx)
        #logger.debug(f"In get_pubkey_from_signature coordx: {coordx.hex()}")

        digest= sha256()
        digest.update(data)
        hash=digest.digest()
        h = int.from_bytes(hash, "big")

        # decoding der signature
        lenr = int(dersig[3])
        lens = int(dersig[5 + lenr])
        r = int.from_bytes(dersig[4 : lenr + 4], "big")
        s = int.from_bytes(dersig[lenr + 6 : lenr + 6 + lens], "big")
        
        recid=-1
        pubkey=None
        for id in range(4):
            try:
                # Parity recovery
                pkbytes=  public_key_recover(h, r, s, id)
                #logger.debug(f"In get_pubkey_from_signature id: {id}")
                #logger.debug(f"In get_pubkey_from_signature pkbytes: {pkbytes.hex()}")
            except InvalidECPointException:
                continue

            coordx_pkbytes= pkbytes[1:33]
            #logger.debug(f"In get_pubkey_from_signature coordx_pkbytes: {coordx_pkbytes.hex()}")
            if coordx_pkbytes==coordx:
                recid=id
                pubkey=pkbytes
                break

        if recid == -1:
            raise ValueError("Unable to recover public key from signature")
        
        logger.debug(f"In get_pubkey_from_signature: recovered pubkey: {pkbytes.hex()}")
        return pubkey


    def parse_to_compact_sig(self, sigin, recid, compressed):
        ''' convert a DER encoded signature to compact 65-byte format
            input is bytearray in DER format
            output is bytearray in compact 65-byteformat
            http://bitcoin.stackexchange.com/questions/12554/why-the-signature-is-always-65-13232-bytes-long
            https://bitcointalk.org/index.php?topic=215205.0
        '''
        logger.debug("In parse_to_compact_sig")
        sigout= bytearray(65*[0])
        # parse input
        first= sigin[0]
        if first!= 0x30:
            raise ValueError("Wrong first byte!")
        lt= sigin[1]
        check= sigin[2]
        if  check!= 0x02:
            raise ValueError("Check byte should be 0x02")
        # extract r
        lr= sigin[3]
        for i in range(32):
            tmp= sigin[4+lr-1-i]
            if lr>=(i+1):
                sigout[32-i]= tmp
            else:
                sigout[32-i]=0
        # extract s
        check= sigin[4+lr];
        if check!= 0x02:
            raise ValueError("Second check byte should be 0x02")
        ls= sigin[5+lr]
        if lt != (lr+ls+4):
            raise ValueError("Wrong lt value")
        for i in range(32):
            tmp= sigin[5+lr+ls-i]
            if ls>=(i+1):
                sigout[64-i]= tmp;
            else:
                sigout[64-i]=0; 
        # 1 byte header
        if recid>3 or recid<0:
            raise ValueError("Wrong recid value")
        if compressed:
            sigout[0]= 27 + recid + 4
        else:
            sigout[0]= 27 + recid

        return sigout;

    #################################
    #            PERSO PKI          #        
    #################################    
    
    def convert_bytes_to_string_pem(self, cert_bytes):
        
        #logger.debug(f"certbytes size: {str(len(cert_bytes))}")
        #logger.debug(f"convert_bytes_to_string_pem certbytes: {str(cert_bytes)}")
        #logger.debug(f"convert_bytes_to_string_pem certbytes: {bytes(cert_bytes).hex()}")
        cert_bytes_b64 = base64.b64encode(bytes(cert_bytes))
        cert_b64= cert_bytes_b64.decode('ascii')
        cert_pem= "-----BEGIN CERTIFICATE-----\r\n" 
        cert_pem+= '\r\n'.join([cert_b64[i:i+64] for i in range(0, len(cert_b64), 64)]) 
        cert_pem+= "\r\n-----END CERTIFICATE-----"
        return cert_pem
        
    def verify_challenge_response_pki(self, response, challenge_from_host, pubkey):
        logger.debug("In verify_challenge_response_pki")
        
        # parse response 
        challenge_from_device= bytes(response[0:32])
        sig_size= ((response[32] & 0xFF)<<8) + (response[33] & 0xFF)
        sig= bytes(response[34:(34+sig_size)])
        challenge= "Challenge:".encode("utf-8") + challenge_from_device + challenge_from_host
        logger.debug("challenge: "+ challenge.hex())
        
        # verify challenge-response
        vk = ECpubkey(bytes(pubkey), "K1")
        try:
            vk.check_signature(challenge, sig)
            logger.debug("Challenge-response verified!")
            return True, ""
        except Exception as ex:
            logger.debug(f"Challenge-response failed: {repr(ex)}")
            return False, f"Bad signature during challenge response: {repr(ex)}"

class InvalidECPointException(Exception):
    """e.g. not on curve, or infinity"""
