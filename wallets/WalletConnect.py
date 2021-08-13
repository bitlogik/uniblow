#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW WalletConnect library
# Copyright (C) 2021 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#


import re
from os import urandom
from urllib.parse import unquote, urlparse
from json import dumps, loads
from ssl import create_default_context
from socket import create_connection
from time import sleep
from uuid import uuid4

from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from wsproto import WSConnection, ConnectionType
from wsproto.events import (
    Request,
    AcceptConnection,
    RejectConnection,
    CloseConnection,
    Ping,
    Message,
    TextMessage,
    BytesMessage,
)

from wallets.wallets_utils import InvalidOption


# ---- WalletConnect settings


DEFAULT_HTTPS_PORT = 443

GLOBAL_TIMEOUT = 8  # seconds
UNIT_WAITING_TIME = 0.1
CYCLES_TIMEOUT = int(GLOBAL_TIMEOUT / UNIT_WAITING_TIME)

AES_BLOCK_SIZE = 16
AES_BLOCK_SIZE_BITS = AES_BLOCK_SIZE << 3
WC_AES_KEY_SIZE = 32  # WCv1 uses 256 bits AES key

RECEIVING_BUFFER_SIZE = 8192


# ---- Crypto primitives for the secure channel


def HMAC_SHA256(key, message):
    hmac256 = hmac.HMAC(key, hashes.SHA256())
    hmac256.update(message)
    return hmac256.finalize()


def check_HMAC(message, mac, key):
    hmac256 = hmac.HMAC(key, hashes.SHA256())
    hmac256.update(message)
    # can throw cryptography.exceptions.InvalidSignature
    hmac256.verify(mac)


def pad_data(databin):
    padder = PKCS7(AES_BLOCK_SIZE_BITS).padder()
    return padder.update(databin) + padder.finalize()


def unpad_data(databin_padded):
    remover = PKCS7(AES_BLOCK_SIZE_BITS).unpadder()
    return remover.update(databin_padded) + remover.finalize()


def encrypt_AES(key, message):
    iv = urandom(AES_BLOCK_SIZE)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    enc_data = encryptor.update(pad_data(message)) + encryptor.finalize()
    return (enc_data, iv)


def decrypt_AES(key, iv, message):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    clear_txt = decryptor.update(message) + decryptor.finalize()
    return unpad_data(clear_txt)


# ---- Helpers about message encoding


def json_encode(dataobj):
    return dumps(dataobj, separators=(",", ":"))


def JSONRPCencpack_response(id, result_obj):
    """Build a JSON-RPC response"""
    request_obj = {
        "jsonrpc": "2.0",
        "id": id,
        "result": result_obj,
    }
    return json_encode(request_obj).encode("utf8")


def JSONRPCunpack_query(buffer):
    """Decode a JSON-RPC query"""
    try:
        resp_obj = loads(buffer)
    except Exception:
        raise Exception(f"Error : not JSON response : {buffer}")
    if resp_obj["jsonrpc"] != "2.0":
        raise Exception(f"Server is not JSONRPC 2.0 but {resp_obj.jsonrpc}")
    if "error" in resp_obj:
        raise Exception(resp_obj["error"]["message"])
    else:
        # Response
        # print(f"<--  {resp_obj['result']} ")
        # return resp_obj["result"]
        # Request : method, params
        return resp_obj["id"], resp_obj["method"], resp_obj["params"]


class TLSsocket:
    def __init__(self, domain, port):
        context = create_default_context()
        sock = create_connection((domain, port))
        self.conn = context.wrap_socket(sock, server_hostname=domain)
        self.conn.settimeout(None)

    def __del(self):
        self.conn.close()

    def send(self, data_buffer):
        self.conn.sendall(data_buffer)

    def receive(self):
        return self.conn.recv(RECEIVING_BUFFER_SIZE)


class WebSocketClientException(Exception):
    pass


class WebSocketClient:
    def __init__(self, wsURL):
        ws_url = urlparse(wsURL)
        assert ws_url.scheme == "https"
        try:
            port_num = ws_url.port or DEFAULT_HTTPS_PORT
            self.ssocket = TLSsocket(ws_url.hostname, port_num)
            self.ws_conn = WSConnection(ConnectionType.CLIENT)
            print("path target")
            self.send(Request(host=ws_url.hostname, target=ws_url.path or "/"))
            cyclew = 0
            while cyclew < CYCLES_TIMEOUT:
                print(f"{cyclew} loop ws")
                messages_queue = self.get_messages()
                while len(messages_queue) > 0:
                    res = messages_queue.pop(0)
                    if res == "established":
                        return
                    if res == "rejected":
                        raise WebSocketClientException("WebSocket handshake rejected")
                cyclew += 1
            if cyclew == CYCLES_TIMEOUT:
                raise WebSocketClientException("WebSocket handshake timeout")
        except Exception as e:
            print(e)
            raise WebSocketClientException(e)

    def send(self, data_frame):
        frame_bin = self.ws_conn.send(data_frame)
        self.ssocket.send(frame_bin)

    def write_message(self, data_message):
        raw_message = Message(data_message)
        self.send(raw_message)

    def get_messages(self):
        sleep(UNIT_WAITING_TIME)
        # Listen to server data and build a queue generator
        datar = self.ssocket.receive()
        self.ws_conn.receive_data(datar)
        events = []
        for event in self.ws_conn.events():
            if isinstance(event, AcceptConnection):
                print("Connection established")
                events.insert(0, "established")
            elif isinstance(event, RejectConnection):
                print("Connection rejected")
                events.insert(0, "rejected")
            elif isinstance(event, CloseConnection):
                print(
                    "Connection closed: code={} reason={}".format(
                        event.code, event.reason
                    )
                )
                del self
            elif isinstance(event, Ping):
                print("Ping received")
                self.send(event.response())
                print("Pong sent")
                events.insert(0, "ping")
            elif isinstance(event, TextMessage):
                print("Text received")
                if event.message_finished:
                    events.insert(0, event.data)
            elif isinstance(event, BytesMessage):
                print("Bytes received")
                if event.message_finished:
                    events.insert(0, vent.data)
            else:
                Exception("Unknown event: {!r}".format(event))
        print("get messages out:")
        print(events)
        return events


class EncryptedChannel:
    def __init__(self, key):
        self.key = key

    def encrypt_payload(self, message):
        enc_msg_iv = encrypt_AES(self.key, message)
        mac_data = HMAC_SHA256(self.key, enc_msg_iv[0] + enc_msg_iv[1]).hex()
        payload_obj = {
            "data": enc_msg_iv[0].hex(),
            "hmac": mac_data,
            "iv": enc_msg_iv[1].hex(),
        }
        return payload_obj

    def decrypt_payload(self, fullpayload_obj):
        payload_obj = loads(fullpayload_obj["payload"])
        msg_bin = bytes.fromhex(payload_obj["data"])
        mac_sig = bytes.fromhex(payload_obj["hmac"])
        iv = bytes.fromhex(payload_obj["iv"])
        check_HMAC(msg_bin + iv, mac_sig, self.key)
        return decrypt_AES(self.key, iv, msg_bin)


class WalletConnectClientException(Exception):
    pass


class WalletConnectClient:
    def __init__(self, wcURL, account, chain_id, topic, symkey, debug=True):
        print(wcURL)
        print(account)
        print(chain_id)
        print(topic)
        print(symkey)
        print(debug)
        try:
            self.debug = debug
            self.topic = topic
            self.ws = WebSocketClient(wcURL)
            self.data_queue = self.read_data()
        except Exception as e:
            print(e)
            raise WalletConnectClientException(e)
        self.id = str(uuid4())
        self.enc_channel = EncryptedChannel(symkey)
        self.account = account
        self.chain = chain_id
        self.service_id = None
        self.open_session()

    @classmethod
    def from_wc_uri(cls, wc_uri_str, account_adr, chain_id):
        pattern = r"^wc:(.+)@(\d)\?bridge=(.+)&key=(.+)$"
        found = re.findall(pattern, wc_uri_str)
        if not found:
            raise InvalidOption("Bad wc URI\nMust be wc:xxxx")
        wc_data = found[0]
        if len(wc_data) != 4:
            raise InvalidOption("Bad data received in URI")
        handshake_topic = wc_data[0]
        wc_ver = wc_data[1]
        bridge_url = unquote(wc_data[2])
        sym_key = bytes.fromhex(wc_data[3])
        if wc_ver != "1":
            raise InvalidOption("Bad WalletConnect version. Only supports v1.")
        if len(sym_key) != WC_AES_KEY_SIZE:
            raise InvalidOption("Bad key data in URI")
        return cls(bridge_url, account_adr, chain_id, handshake_topic, sym_key, True)

    def write(self, data_dict):
        raw_data = json_encode(data_dict)
        print("Sending :")
        print(raw_data)
        self.ws.write_message(raw_data)

    def read_data(self):
        # Read possible server data and return list
        return self.ws.get_messages()

    def get_data(self):
        # read the first data in the received queue messages
        if len(self.data_queue) > 0:
            return self.data_queue.pop(0)
        # Refill data queue
        self.data_queue = self.read_data()
        if len(self.data_queue) > 0:
            rcvd_message = self.data_queue.pop(0)
            if rcvd_message and rcvd_message.startswith('{"'):
                return self.enc_channel.decrypt_payload(loads(rcvd_message))
            return rcvd_message

    def reply(self, peer_id, req_id, result):
        payload_bin = JSONRPCencpack_response(req_id, result)
        datafull = {
            "topic": peer_id,
            "type": "pub",
            "payload": json_encode(self.enc_channel.encrypt_payload(payload_bin)),
        }
        # if self.debug:
        print(f"--> [{req_id}] {result} ")
        print(payload_bin)
        self.write(datafull)

    def reply_session_request(self, to_peer, msg_id):
        session_request_result = {
            "peerId": self.id,
            "peerMeta": {
                "description": "Uniblow multi wallet by BitLogiK",
                "url": "https://github.com/bitlogik/uniblow",
                "icons": [""],
                "name": "Uniblow",
            },
            "approved": True,
            "chainId": self.chain,
            "accounts": [self.account],
        }
        self.reply(to_peer, msg_id, session_request_result)

    def subscribe(self, peer_uuid):
        data = {"topic": peer_uuid, "type": "sub", "payload": ""}
        self.write(data)

    def open_session(self):
        self.subscribe(self.topic)
        self.subscribe(self.id)

        # Waiting for sessionRequest
        print("Waiting for sessionRequest")
        cyclew = 0
        while cyclew < CYCLES_TIMEOUT:
            read_data = self.get_data()
            if read_data and read_data != "ping":
                print(">>> read :")
                print(read_data)
                msg_id, method, query_params = JSONRPCunpack_query(read_data)
                if method == "wc_sessionRequest":
                    break
            cyclew += 1
        if cyclew == CYCLES_TIMEOUT:
            raise WalletConnectClientException("sessionRequest timeout")

        print(" -- Session Request --")
        self.service_id = query_params[0]["peerId"]
        param = query_params[0]["peerMeta"]
        
        print("From :", param["name"])
        print(" URL :", param["url"])
        print("")
        print(param["description"])
        print(" -> Accept ?")
        sleep(1)
        print("accepted automatically")
        
        self.reply_session_request(self.service_id, msg_id)


if __name__ == "__main__":

    print("WC handler")

    string_uri = input("Input the WalletConnect URI : ")

    relay = WalletConnectClient.from_wc_uri(string_uri)

    # Waiting for new message
    sleep(2)
    while True:
        resp = relay.get_data()
        if resp and resp != "ping":
            print(">>> read :")
            print(resp)
            break
