#!/usr/bin/env python
#
# Satochip 2-Factor-Authentication app for the Satochip Bitcoin Hardware Wallet
# (c) 2019 by Toporin - 16DMCk4WUaHofchAhpMaQS4UPm4urcy2dN
# Sources available on https://github.com/Toporin	
#
# Based on Electrum - lightweight Bitcoin client
# Copyright (C) 2014 Thomas Voegtlin
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import hashlib
import base64
import time
import logging 
import certifi
import ssl
from xmlrpc.client import ServerProxy

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# User can select his 2FA server from a list
# User should select the same server on the 2FA app
SERVER_LIST= [
    'https://cosigner.electrum.org',
    'https://cosigner.satochip.io', 
    'http://sync.imaginary.cash:8081', 
]

ca_path = certifi.where()
ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=ca_path)
#server = ServerProxy('https://cosigner.electrum.org', allow_none=True, context=ssl_context)
#server = ServerProxy('https://cosigner.satochip.io', allow_none=True, context=ssl_context)
#server = ServerProxy('http://sync.imaginary.cash:8081', allow_none=True, context=ssl_context)
#server = ServerProxy('https://cosigner.satochip.io:81', allow_none=True, context=ssl_context) # wrong port to generate timeout error

class Satochip2FA:
    def __init__(self, loglevel= logging.INFO):
        logger.setLevel(loglevel)
    
    # send the challenge and get the reply 
    @classmethod
    def do_challenge_response(cls, d, server_name= SERVER_LIST[0]):
        logger.debug("In do_challenge_response()")
        id_2FA= d['id_2FA']
        msg= d['msg_encrypt']        
        replyhash= hashlib.sha256(id_2FA.encode('utf-8')).hexdigest()
        
        # set server
        if server_name not in SERVER_LIST:
            server_name= SERVER_LIST[0]
        server = ServerProxy(server_name, allow_none=True, context=ssl_context)
        
        #purge server from old messages then sends message
        server.delete(id_2FA)
        server.delete(replyhash)
        server.put(id_2FA, msg)
        logger.info(f"Challenge sent to id_2FA:{id_2FA}")
                
        # wait for reply
        timeout= 180
        period=10
        reply= None
        while timeout>0:
            try:
                reply = server.get(replyhash)
            except Exception as e:
                logger.warning(f"Exception: cannot contact server - error: {str(e)}")
                continue
            if reply:
                logger.info(f"Received response from {replyhash}")
                logger.info(f"Response received: {reply}")
                d['reply_encrypt']=base64.b64decode(reply)
                server.delete(replyhash)
                break
            # poll every t seconds
            time.sleep(period)
            timeout-=period
        
        if reply is None:
            logger.warning(f"Error: Time-out without server reply...")
            d['reply_encrypt']= None #default 
    