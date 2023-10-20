#!/usr/bin/python3
# -*- coding: utf8 -*-

# Satochip smartcard 2FA
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

import hashlib
import base64
import time
import logging
import ssl
from xmlrpc.client import ServerProxy

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# User can select his 2FA server from a list
# User should select the same server on the 2FA app
SERVER_LIST = [
    "https://cosigner.electrum.org",
    "https://cosigner.satochip.io",
    "http://sync.imaginary.cash:8081",
]

ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)


class Satochip2FA:
    def __init__(self, loglevel=logging.INFO):
        logger.setLevel(loglevel)

    # send the challenge and get the reply
    @classmethod
    def do_challenge_response(cls, d, server_name=SERVER_LIST[0]):
        logger.debug("In do_challenge_response()")
        id_2FA = d["id_2FA"]
        msg = d["msg_encrypt"]
        replyhash = hashlib.sha256(id_2FA.encode("utf-8")).hexdigest()

        # set server
        if server_name not in SERVER_LIST:
            server_name = SERVER_LIST[0]
        server = ServerProxy(server_name, allow_none=True, context=ssl_context)

        # purge server from old messages then sends message
        server.delete(id_2FA)
        server.delete(replyhash)
        server.put(id_2FA, msg)
        logger.info(f"Challenge sent to id_2FA:{id_2FA}")

        # wait for reply
        timeout = 180
        period = 10
        reply = None
        while timeout > 0:
            try:
                reply = server.get(replyhash)
            except Exception as e:
                logger.warning(f"Exception: cannot contact server - error: {str(e)}")
                continue
            if reply:
                logger.info(f"Received response from {replyhash}")
                logger.info(f"Response received: {reply}")
                d["reply_encrypt"] = base64.b64decode(reply)
                server.delete(replyhash)
                break
            # poll every t seconds
            time.sleep(period)
            timeout -= period

        if reply is None:
            logger.warning(f"Error: Time-out without server reply...")
            d["reply_encrypt"] = None  # default
