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
from ecdsa.curves import SECP256k1
from ecdsa.util import sigdecode_der

from .ecc import ECPubkey, InvalidECPointException, sig_string_from_der_sig, sig_string_from_r_and_s, get_r_and_s_from_sig_string, CURVE_ORDER

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
        self.authentikey=None
        self.authentikey_coordx= None
        self.authentikey_from_storage=None
    
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

        # if already initialized, check that authentikey match value retrieved from storage!
        if (self.authentikey_from_storage is not None):
            if  self.authentikey != self.authentikey_from_storage:
                raise ValueError("The seed used to create this wallet file no longer matches the seed of the Satochip device!\n\n"+MSG_WARNING)

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
        logger.debug('[CardDataParser] parse_bip32_get_extendedkey: first signature recovery')
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
        logger.debug('[CardDataParser] parse_bip32_get_extendedkey: second signature recovery')
        msg2_size= msg_size+2+sig_size
        msg2= response[0:msg2_size]
        sig2_size = ((response[msg2_size] & 0xff)<<8) + (response[msg2_size+1] & 0xff)
        signature2= response[(msg2_size+2):(msg2_size+2+sig2_size)]
        authentikey= self.get_pubkey_from_signature(self.authentikey_coordx, msg2, signature2)
        if authentikey != self.authentikey:
            raise ValueError("The seed used to create this wallet file no longer matches the seed of the Satochip device!\n\n"+MSG_WARNING)

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
                if ( authentikey.get_public_key_bytes(compressed=False) != self.authentikey.get_public_key_bytes(compressed=False) ):
                    raise ValueError("Recovered authentikey does not correspond to registered authentikey!")
                logger.info("In parse_initiate_secure_channel: successfuly recovered authentikey:"+ authentikey.get_public_key_bytes(compressed=False).hex()) #debug
                    
            logger.info("In parse_initiate_secure_channel: successfuly recovered pubkey:"+ self.pubkey.get_public_key_bytes(compressed=False).hex()) #debug
            return (self.pubkey)
    
    ##############
    def parse_message_signature(self, response, hash, pubkey):
        logger.debug("In parse_message_signature")
        # Prepend the message for signing as done inside the card!!
        #message = to_bytes(message, 'utf8')
        #hash = sha256d(msg_magic(message))

        coordx= pubkey.get_public_key_bytes()
        
        response= bytearray(response)
        recid=-1
        for id in range(4):
            compsig=self.parse_to_compact_sig(response, id, compressed=True)
            # remove header byte
            compsig2= compsig[1:]

            try:
                pk = ECPubkey.from_sig_string(compsig2, id, hash)
                pkbytes= pk.get_public_key_bytes(compressed=True)   
            except InvalidECPointException:
                continue

            if coordx==pkbytes:
                recid=id
                break

        if recid == -1:
            raise ValueError("Unable to recover public key from signature")

        return compsig

    ##############
    # def parse_rsv_from_dersig(self, dersig: bytes, hash: bytes, pubkey: ECPubkey):
    #     """ Takes in input the DER signature returned by Satochip and return the r, s, v and sigstring format."""
    #     logger.debug("In parse_rsv_from_dersig")
    #     #dersig= bytearray(response)
    #     #hash = to_bytes(hash, 'utf8') 
    #     coordx= pubkey.get_public_key_bytes()
    
    #     sigstring= sig_string_from_der_sig(dersig)
    #     r, s= get_r_and_s_from_sig_string(sigstring) #r,s:long int
    #     # enforce low-S signature (BIP 62)
    #     if s > CURVE_ORDER//2:
    #         logger.debug('In parse_rsv_from_dersig(): S is higher than CURVE_ORDER//2')
    #         s = CURVE_ORDER - s
    #         sigstring= sig_string_from_r_and_s(r,s)
        
    #     # v
    #     recid=-1
    #     for id in range(4):
    #         try:
    #             pk = ECPubkey.from_sig_string(sigstring, id, hash)
    #             pkbytes= pk.get_public_key_bytes(compressed=True)
    #             logger.debug("    =>parse_hash_signature - rec_pubkey:"+pkbytes.hex())
    #         except InvalidECPointException:
    #             continue

    #         if coordx==pkbytes:
    #             recid=id
    #             logger.debug("    =>parse_hash_signature - found good pubkey:"+pkbytes.hex())
    #             break

    #     if recid == -1:
    #         raise ValueError("Unable to recover public key from signature")
        
    #     v= recid % 2# 
    #     sigstring= bytes([v])+sigstring
    #     return (r, s, v, sigstring)
        
        
    ##############
    # def parse_hash_signature(self, response, hash, pubkey):
        # print("    =>parse_hash_signature - Debug1")
        # # Prepend the message for signing as done inside the card!!
        # hash = to_bytes(hash, 'utf8')
        # print("    =>parse_hash_signature - Debug1A")
        # #hash = sha256d(msg_magic(message))
        # print("    =>parse_hash_signature - Debug1B")
        # coordx= pubkey.get_public_key_bytes()
        
        # print("    =>parse_hash_signature - Debug2")
        
        # response= bytearray(response)
        # recid=-1
        # for id in range(4):
            # compsig=self.parse_to_compact_sig(response, id, compressed=True)
            # # remove header byte
            # compsig2= compsig[1:]

            # try:
                # pk = ECPubkey.from_sig_string(compsig2, id, hash)
                # pkbytes= pk.get_public_key_bytes(compressed=True)
                # print("    =>parse_hash_signature - rec_pubkey:"+pkbytes.hex())
            # except InvalidECPointException:
                # continue

            # if coordx==pkbytes:
                # recid=id
                # print("    =>parse_hash_signature - found good pubkey:"+pkbytes.hex())
                # break

        # if recid == -1:
            # raise ValueError("Unable to recover public key from signature")

        # return compsig
    
    ##############
    def get_pubkey_from_signature(self, coordx, data, sig):
        logger.debug("In get_pubkey_from_signature")
        data= bytearray(data)
        sig= bytearray(sig)
        coordx= bytearray(coordx)

        digest= sha256()
        digest.update(data)
        hash=digest.digest()

        recid=-1
        pubkey=None
        for id in range(4):
            compsig=self.parse_to_compact_sig(sig, id, compressed=True)
            # remove header byte
            compsig= compsig[1:]

            try:
                pk = ECPubkey.from_sig_string(compsig, id, hash)
                pkbytes= pk.get_public_key_bytes(compressed=True)
            except InvalidECPointException:
                continue

            pkbytes= pkbytes[1:]

            if coordx==pkbytes:
                recid=id
                pubkey=pk
                break

        if recid == -1:
            raise ValueError("Unable to recover public key from signature")
        
        logger.debug("Signature verified!")
        return pubkey

    #######
    # def verify_signature(self, data, sig, authentikey):
    #     logger.debug("In verify_signature")
    #     data= bytearray(data)
    #     sig= bytearray(sig)

    #     digest= sha256()
    #     digest.update(data)
    #     hash=digest.digest()

    #     recid=-1
    #     for id in range(4):
    #         compsig=self.parse_to_compact_sig(sig, id, compressed=True)
    #         # remove header byte
    #         compsig= compsig[1:]

    #         try:
    #             pk = ECPubkey.from_sig_string(compsig, id, hash)
    #         except InvalidECPointException:
    #             continue
            
    #         if pk== authentikey:
    #             recid=id
    #             break
            
    #     if recid == -1:
    #         raise ValueError("Unable to recover authentikey from signature")

    #     return pk
    
    # def get_trusted_pubkey(self, response):
    #     pubkey_size= response[0]*256+response[1]
    #     if (pubkey_size !=65):
    #         raise RuntimeError(f'Error while recovering trusted pubkey: wrong pubkey size, expected 65 but received {pubkey_size}')
    #     data= response[0:(2+pubkey_size)]
    #     sig_size= response[2+pubkey_size]*256 + response[2+pubkey_size+1] 
    #     sig= response[(2+pubkey_size+2):(2+pubkey_size+2+sig_size)]
        
    #     pubkey_hex= bytes(response[2:2+pubkey_size]).hex()
    #     logger.debug(f"Verifying sig for pubkey {pubkey_hex} using authentikey {self.authentikey.get_public_key_bytes(compressed=False).hex()}")
        
    #     try:
    #         self.verify_signature(data, sig, self.authentikey)
    #     except Exception as ex:
    #         logger.error('Exception in get_trusted_pubkey: ' + str(ex))
            
    #     return pubkey_hex
    
    ##############
    # def parse_parse_transaction(self, response):
    #     '''Satochip returns: [(hash_size+2)(2b) | tx_hash(32b) | need2fa(2b) | sig_size(2b) | sig(sig_size) | txcontext]'''
    #     logger.debug("In parse_to_compact_sig")
    #     offset=0
    #     data_size= ((response[offset] & 0xff)<<8) + (response[offset+1] & 0xff)
    #     txhash_size= data_size-2
    #     offset+=2
    #     tx_hash= response[offset:(offset+txhash_size)]
    #     offset+=txhash_size
    #     needs_2fa= ((response[offset] & 0xff)<<8) + (response[offset+1] & 0xff)
    #     needs_2fa= False if (needs_2fa==0) else True
    #     offset+=2
    #     sig_size= ((response[offset] & 0xff)<<8) + (response[offset+1] & 0xff)
    #     sig_data= response[0:data_size+2] # txhash_size+hash+needs_2fa
    #     offset+=2
    #     if sig_size>0 and self.authentikey_coordx:
    #         sig= response[offset:(offset+sig_size)]
    #         pubkey= self.get_pubkey_from_signature(self.authentikey_coordx, sig_data, sig)
    #         if pubkey != self.authentikey:
    #             raise Exception("signing key is not authentikey!")
    #     #todo: error checking

    #     return (tx_hash, needs_2fa)

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
    
    # def parse_compact_sig_to_ethcompsig(self, compsig):
        # print("    =>parse_compact_sig_to_ethcompsig - compsig:"+compsig.hex())
        # v= compsig[0]-27 if (compsig[0]<=28)  else compsig[0]-27-4 # recid is 0 or 1
        # ethcompsig= compsig[1:]+v.to_bytes(1, byteorder='big')
        # print("    =>parse_compact_sig_to_ethcompsig - ethcompsig:"+ethcompsig.hex())
        # return ethcompsig
    
    # def parse_compact_sig_to_rsv(self, compsig):
        # r= compsig[1:33] #init
        # s= compsig[33:]
        # #s= compsig[1:33] # new but wrong?
        # #r= compsig[33:]
        # v= compsig[0]-27 if (compsig[0]<=28)  else compsig[0]-27-4 # recid is 0 or 1
        # return (r,s,v)
    
    #################################
    #                  SEEDKEEPER              #        
    #################################   
    
    # def parse_seedkeeper_header(self, response):
    #     # parse header
        
    #     header_dict={}
    #     if ( len(response) <12 ):
    #         logger.error(f"SeedKeeper error: header response too short: {len(response)}")
    #         return header_dict
        
    #     header_dict['id']= (response[0]<<8) +response[1]
    #     header_dict['type']= response[2]
    #     header_dict['origin']= response[3]
    #     header_dict['export_rights']= response[4]
    #     header_dict['export_nbplain']=  response[5]
    #     header_dict['export_nbsecure']=  response[6]
    #     header_dict['export_counter']=  response[7]
    #     header_dict['fingerprint_list']= response[8:12]
    #     header_dict['fingerprint']= bytes(header_dict['fingerprint_list']).hex()
    #     header_dict['rfu1']= response[12]
    #     header_dict['rfu2']= response[13]
    #     header_dict['label_size']= response[14]
    #     if ( len(response) <(15+header_dict['label_size'])):
    #         logger.error(f"SeedKeeper error: header response too short: {len(response)}")
    #         return header_dict
            
    #     header_dict['label_list']= response[15:(15+header_dict['label_size'])]
    #     try:
    #         header_dict['label']=  bytes(header_dict['label_list']).decode("utf-8") 
    #     except UnicodeDecodeError as e:
    #         logger.warning("UnicodeDecodeError while decoding label header!")
    #         header_dict['label']=  str(bytes(header_dict['label_list']))
    #     header_dict['header_list']=  response[0:(15+header_dict['label_size'])]
    #     header_dict['header']=  bytes(header_dict['header_list']).hex()
        
    #     # logger.debug(f"++++++++++++++++++++++++++++++++")
    #     # logger.debug(f"Secret id: {header_dict['id']}")
    #     # logger.debug(f"Secret type: {header_dict['type']}")
    #     # logger.debug(f"Secret export_rights: {header_dict['export_rights']}")
    #     # logger.debug(f"Secret export_nbplain: {header_dict['export_nbplain']}")
    #     # logger.debug(f"Secret export_nbsecure: {header_dict['export_nbsecure']}")
    #     # logger.debug(f"Secret export_counter: {header_dict['export_counter']}")
    #     # logger.debug(f"Secret fingerprint: {header_dict['fingerprint']}")
    #     # logger.debug(f"Secret label: {header_dict['label']}")
    #     # logger.debug(f"Secret label_list: {header_dict['label_list']}")
    #     # logger.debug(f"++++++++++++++++++++++++++++++++")
                    
    #     return header_dict
    
    # def parse_seedkeeper_log(self, log):
        
    #     # todo: 
    #     LOG_SIZE=7
    #     if (len(log)<LOG_SIZE):
    #         logger.error(f"Log record has the wrong lenght {len(log)}, should be {LOG_SIZE}")
    #         raise Exception(f"Log record has the wrong lenght {len(log)}, should be {LOG_SIZE}")
        
    #     ins= log[0]
    #     id1= log[1]*256+ log[2]
    #     id2= log[3]*256+ log[4]
    #     res= log[5]*256+ log[6]
        
    #     return (ins, id1, id2, res)

    #################################
    #                   PERSO PKI                 #        
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
        
        from ecdsa import VerifyingKey, BadSignatureError, MalformedPointError
        
        # parse response 
        challenge_from_device= bytes(response[0:32])
        sig_size= ((response[32] & 0xFF)<<8) + (response[33] & 0xFF)
        sig= bytes(response[34:(34+sig_size)])
        challenge= "Challenge:".encode("utf-8") + challenge_from_device + challenge_from_host
        logger.debug("challenge: "+ challenge.hex())
        
        # parse pubkey & verify sig
        vk = VerifyingKey.from_string(bytes(pubkey), curve=SECP256k1, hashfunc=sha256, validate_point=True)
        try:
            vk.verify(sig, challenge, hashfunc=sha256, sigdecode=sigdecode_der)
            return True, ""
        except BadSignatureError:
            return False, "Bad signature during challenge response!"
        except MalformedPointError:
            return False, "Invalid X9.62 encoding of the public key: " + bytes(pubkey).hex()
        
        
        
    