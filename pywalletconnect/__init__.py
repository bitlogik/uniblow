#!/usr/bin/python3
# -*- coding: utf8 -*-

# pyWalletConnect : a Python library to use WalletConnect
# Copyright (C) 2021 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have receive a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


"""WalletConnect for desktop wallets"""


from os import urandom
from urllib.parse import unquote, urlparse
from json import dumps, loads
from logging import getLogger
from re import compile as regexcompile
from ssl import create_default_context, SSLWantReadError
from socket import create_connection
from threading import Timer
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


# ---- WalletConnect settings


DEFAULT_HTTPS_PORT = 443

GLOBAL_TIMEOUT = 8  # seconds
UNIT_WAITING_TIME = 0.4
CYCLES_TIMEOUT = int(GLOBAL_TIMEOUT / UNIT_WAITING_TIME)

AES_BLOCK_SIZE = 16
AES_BLOCK_SIZE_BITS = AES_BLOCK_SIZE << 3
WC_AES_KEY_SIZE = 32  # WCv1 uses 256 bits AES key

RECEIVING_BUFFER_SIZE = 8192


logger = getLogger(__name__)


# ---- Crypto primitives for the secure channel


def hmac_sha256(key, message):
    """Compute a Hash-based Message Authentication Code by using the SHA256 hash function."""
    hmac256 = hmac.HMAC(key, hashes.SHA256())
    hmac256.update(message)
    return hmac256.finalize()


def check_hmac(message, mac, key):
    """Verify the HMAC signature."""
    hmac256 = hmac.HMAC(key, hashes.SHA256())
    hmac256.update(message)
    # Can throw cryptography.exceptions.InvalidSignature
    hmac256.verify(mac)


def pad_data(databin):
    """Add a PCKS7 message padding for AES."""
    padder = PKCS7(AES_BLOCK_SIZE_BITS).padder()
    return padder.update(databin) + padder.finalize()


def unpad_data(databin_padded):
    """Remove a PCKS7 padding from the message for AES."""
    remover = PKCS7(AES_BLOCK_SIZE_BITS).unpadder()
    # Can throw ValueError if the padding is incorrect
    return remover.update(databin_padded) + remover.finalize()


def encrypt_aes(key, message):
    """Encrypt a message with a key using AES-CBC."""
    init_vector = urandom(AES_BLOCK_SIZE)
    cipher = Cipher(algorithms.AES(key), modes.CBC(init_vector))
    encryptor = cipher.encryptor()
    enc_data = encryptor.update(pad_data(message)) + encryptor.finalize()
    return (enc_data, init_vector)


def decrypt_aes(key, init_vector, message):
    """Decrypt a message with a key using AES-CBC."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(init_vector))
    decryptor = cipher.decryptor()
    clear_txt = decryptor.update(message) + decryptor.finalize()
    return unpad_data(clear_txt)


# ---- Helpers about message encoding


def json_encode(dataobj):
    """Compact JSON encoding."""
    return dumps(dataobj, separators=(",", ":"))


def json_rpc_pack_response(idmsg, result_obj):
    """Build a JSON-RPC response."""
    request_obj = {
        "jsonrpc": "2.0",
        "id": idmsg,
        "result": result_obj,
    }
    return json_encode(request_obj).encode("utf8")


def json_rpc_unpack(buffer):
    """Decode a JSON-RPC query : id, method, params."""
    try:
        resp_obj = loads(buffer)
    except Exception as exc:
        raise Exception(f"Error : not JSON response : {buffer}") from exc
    if resp_obj["jsonrpc"] != "2.0":
        raise Exception(f"Server is not JSONRPC 2.0 but {resp_obj.jsonrpc}")
    if "error" in resp_obj:
        raise Exception(resp_obj["error"]["message"])
    return resp_obj["id"], resp_obj["method"], resp_obj["params"]


class TLSsocket:
    """TLS socket client with a host, push and read data."""

    def __init__(self, domain, port):
        """Open the TLS connection with a host domain:port."""
        context = create_default_context()
        sock = create_connection((domain, port))
        self.conn = context.wrap_socket(sock, server_hostname=domain)
        self.conn.settimeout(0)

    def __del__(self):
        """Close the socket when deleting the object."""
        self.close()

    def close(self):
        """Close the socket"""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def send(self, data_buffer):
        """Send data to the host."""
        self.conn.sendall(data_buffer)

    def receive(self):
        """Read data from the host.
        If no data received from host since last read, return empty bytes.
        """
        try:
            return self.conn.recv(RECEIVING_BUFFER_SIZE)
        except SSLWantReadError:
            return b""


class WebSocketClientException(Exception):
    """Exception from the WebSocket client."""


class WebSocketClient:
    """WebSocket client with a host within HTTPS, send and decode messages."""

    def __init__(self, wsURL):
        """Open the WebSocket connection to a given a URL."""
        ws_url = urlparse(wsURL)
        assert ws_url.scheme == "https"
        self.received_messages = []
        try:
            port_num = ws_url.port or DEFAULT_HTTPS_PORT
            self.ssocket = TLSsocket(ws_url.hostname, port_num)
            self.websock_conn = WSConnection(ConnectionType.CLIENT)
            logger.debug(
                "Connecting to WebSocket Host=%s PathTarget=%s", ws_url.hostname, ws_url.path
            )
            self.send(Request(host=ws_url.hostname, target=ws_url.path or "/"))
            cyclew = 0
            while cyclew < CYCLES_TIMEOUT:
                logger.debug("Waiting WebSocket handshake : %ith loop.", cyclew + 1)
                sleep(UNIT_WAITING_TIME)
                self.get_messages()
                while len(self.received_messages) > 0:
                    res = self.received_messages.pop(0)
                    if res == "established":
                        # Start a timer to reply pings in real-time & collect input messages
                        self.timer_pings = Timer(UNIT_WAITING_TIME, self.collect_messages)
                        self.timer_pings.daemon = True
                        self.timer_pings.start()
                        return
                    if res == "rejected":
                        raise WebSocketClientException("WebSocket handshake rejected")
                cyclew += 1
            if cyclew == CYCLES_TIMEOUT:
                raise WebSocketClientException("WebSocket handshake timeout")
        except Exception as exc:
            logger.error("Error during WebSocket connection : %s", str(exc), exc_info=exc)
            raise WebSocketClientException(exc) from exc

    def close(self):
        """Stop read timer and close the TLS connection when deleting the object."""
        logger.debug("Cancelling the WebSocket reading timer")
        self.timer_pings.cancel()
        logger.debug("Closing WebSocket")
        self.ssocket.close()
        delattr(self, "ssocket")

    def send(self, data_frame):
        """Send a WebSocket data frame to the host."""
        frame_bin = self.websock_conn.send(data_frame)
        self.ssocket.send(frame_bin)

    def write_message(self, data_message):
        """Send a message to the host."""
        raw_message = Message(data_message)
        self.send(raw_message)

    def collect_messages(self):
        """Collect input messages.
        Used to be called periodically from the timer.
        So that pings are reply almost real time "async".
        """
        self.get_messages()
        # Restart the reading timer if the socket is still present
        if hasattr(self, "ssocket"):
            self.timer_pings = Timer(UNIT_WAITING_TIME, self.collect_messages)
            self.timer_pings.daemon = True
            self.timer_pings.start()

    def get_messages(self):
        """Read data from server and decode messages.
        Return a list of messages.
        "established", "rejected", "ping", <text>, <bytes>.
        Text and Bytes mesages are given as their content.
        Close underlying TLS socket if WS connection closed.
        Auto-reply to ping messages.
        """
        # Listen to server data and build a queue generator
        datarcv = self.ssocket.receive()
        if datarcv:
            self.websock_conn.receive_data(datarcv)
            for event in self.websock_conn.events():
                if isinstance(event, AcceptConnection):
                    logger.debug("WebSocket connection established.")
                    self.received_messages.insert(0, "established")
                elif isinstance(event, RejectConnection):
                    logger.debug("WebSocket connection rejected.")
                    self.received_messages.insert(0, "rejected")
                elif isinstance(event, CloseConnection):
                    logger.error(
                        "WebSocket Connection closed: code=%i reason=%s", event.code, event.reason
                    )
                    del self
                elif isinstance(event, Ping):
                    logger.debug("Ping received in WebSocket")
                    self.send(event.response())
                    logger.debug("Pong reply sent")
                elif isinstance(event, TextMessage):
                    logger.debug("WebSocket Text message received : %s", event.data)
                    if event.message_finished:
                        self.received_messages.insert(0, event.data)
                elif isinstance(event, BytesMessage):
                    logger.debug("WebSocket Bytes message received : %s", event.data)
                    if event.message_finished:
                        self.received_messages.insert(0, event.data)
                else:
                    Exception("Unknown WebSocket event : {!r}".format(event))


class EncryptedChannel:
    """Provide an encryption tunnel for WalletConnect messages."""

    def __init__(self, key):
        """Start a tunnel with an AES key."""
        self.key = key

    def encrypt_payload(self, message):
        """Encrypt a bytes message into a payload object."""
        enc_msg_iv = encrypt_aes(self.key, message)
        mac_data = hmac_sha256(self.key, enc_msg_iv[0] + enc_msg_iv[1]).hex()
        payload_obj = {
            "data": enc_msg_iv[0].hex(),
            "hmac": mac_data,
            "iv": enc_msg_iv[1].hex(),
        }
        return payload_obj

    def decrypt_payload(self, fullpayload_obj):
        """Decrypt a payload object into a bytes message."""
        payload_obj = loads(fullpayload_obj["payload"])
        msg_bin = bytes.fromhex(payload_obj["data"])
        mac_sig = bytes.fromhex(payload_obj["hmac"])
        init_vector = bytes.fromhex(payload_obj["iv"])
        check_hmac(msg_bin + init_vector, mac_sig, self.key)
        return decrypt_aes(self.key, init_vector, msg_bin)


class WalletConnectClientException(Exception):
    """Exception from the WalletConnect client."""


class WalletConnectClientInvalidOption(Exception):
    """Exception from the WebSocket client when decoding URI input."""


class WalletConnectClient:
    """WalletConnect client with a host within WebSocket."""

    wc_uri_pattern = regexcompile(r"^wc:(.+)@(\d)\?bridge=(.+)&key=(.+)$")

    def __init__(self, ws_url, topic, symkey):
        """Create a WalletConnect client from parameters.
        Call open_session immediately after to get the session request info.
        """
        # Chain ID is managed outside the walletconnect class
        # Shall be managed by the user / webapp
        logger.debug("Opening a WalletConnect client with %s", ws_url)
        self.relay_url = ws_url
        try:
            self.websock = WebSocketClient(ws_url)
            self.data_queue = self.websock.received_messages
        except Exception as exc:
            logger.error("Error during device initialization : %s", str(exc), exc_info=exc)
            raise WalletConnectClientException(exc) from exc
        self.wallet_id = str(uuid4())
        self.enc_channel = EncryptedChannel(symkey)
        self.app_peer_id = None
        self.subscribe(topic)

    def close(self):
        """Close the WebSocket connection when deleting the object."""
        logger.debug("Closing WalletConnect link.")
        self.websock.close()

    @classmethod
    def from_wc_uri(cls, wc_uri_str):
        """Create a WalletConnect client from wc URI"""
        found = WalletConnectClient.wc_uri_pattern.findall(wc_uri_str)
        if not found:
            raise WalletConnectClientInvalidOption("Bad wc URI provided\nMust be : wc:xxxx...")
        wc_data = found[0]
        if len(wc_data) != 4:
            raise WalletConnectClientInvalidOption("Bad data received in URI")
        handshake_topic = wc_data[0]
        wc_ver = wc_data[1]
        bridge_url = unquote(wc_data[2])
        if len(wc_data[3]) % 2 != 0 or len(wc_data[3]) // 2 != WC_AES_KEY_SIZE:
            raise WalletConnectClientInvalidOption("Bad key data format in URI")
        sym_key = bytes.fromhex(wc_data[3])
        if wc_ver != "1":
            raise WalletConnectClientInvalidOption("Bad WalletConnect version. Only supports v1.")
        logger.debug("wc URI provided decoded successfully, now starting the WalletConnect client")
        return cls(bridge_url, handshake_topic, sym_key)

    def get_relay_url(self):
        """Give the URL of the WebSocket relay bridge."""
        return self.relay_url

    def write(self, data_dict):
        """Send a data_object to the WalletConnect relay.
        Usually : { topic: 'xxxx', type: 'pub/sub', payload: 'xxxx' }
        """
        raw_data = json_encode(data_dict)
        logger.debug("WalletConnect message sending to relay : %s", raw_data)
        self.websock.write_message(raw_data)

    def get_data(self):
        """Read the first data available in the receive queue messages."""
        # Non-blocking, so return None if no data has been received
        if len(self.data_queue) > 0:
            rcvd_message = self.data_queue.pop(0)
            if rcvd_message and rcvd_message.startswith('{"'):
                return self.enc_channel.decrypt_payload(loads(rcvd_message))
            return rcvd_message
        return None

    def get_message(self):
        """
        Like get data but filter the messages and fully decode them.
        Return : (id, method, params) or (None, "", [])
        Use like a pump : call get_message() until empty response,
        because it read message from the receiving bucket.
        Non-blocking, so return (None, "", []) if no data has been received
        """
        rcvd_data = self.get_data()
        if rcvd_data and isinstance(rcvd_data, bytes) and rcvd_data.startswith(b'{"'):
            # return (id, method, params)
            msg_ready = json_rpc_unpack(rcvd_data)
        else:
            msg_ready = (None, "", [])
        logger.debug("Get data, WalletConnect message available : %s", msg_ready)
        return msg_ready

    def reply(self, req_id, result):
        """Send a RPC response to the webapp through the relay."""
        payload_bin = json_rpc_pack_response(req_id, result)
        datafull = {
            "topic": self.app_peer_id,
            "type": "pub",
            "payload": json_encode(self.enc_channel.encrypt_payload(payload_bin)),
        }
        logger.debug(
            "--> WalletConnect Replying id[%i] : result=%s\nRaw message: %s",
            req_id,
            result,
            payload_bin,
        )
        self.write(datafull)

    def subscribe(self, peer_uuid):
        """Start listening to a given peer."""
        logger.debug("Sending a subscription request for %s.", peer_uuid)
        data = {"topic": peer_uuid, "type": "sub", "payload": ""}
        self.write(data)

    def open_session(self):
        """Start a WalletConnect session : read session request message
        Return : (message RPC ID, chain ID, peerMeta data object).
        Or throw WalletConnectClientException("sessionRequest timeout")
        after GLOBAL_TIMEOUT seconds.
        """
        self.subscribe(self.wallet_id)

        # Waiting for sessionRequest
        logger.debug("Waiting for WalletConnect sessionRequest.")
        cyclew = 0
        while cyclew < CYCLES_TIMEOUT:
            sleep(UNIT_WAITING_TIME)
            read_data = self.get_data()
            if read_data:
                logger.debug("<-- WalletConnect message read : %s", read_data)
                msg_id, method, query_params = json_rpc_unpack(read_data)
                logger.debug("RPC Call id=%i : method=%s params=%s", msg_id, method, query_params)
                if method == "wc_sessionRequest":
                    break
            cyclew += 1
        if cyclew == CYCLES_TIMEOUT:
            self.close()
            raise WalletConnectClientException("sessionRequest timeout")

        logger.debug(" -- Session Request received : %s", query_params[0])
        self.app_peer_id = query_params[0]["peerId"]
        app_chain_id = query_params[0]["chainId"]
        return msg_id, app_chain_id, query_params[0]["peerMeta"]

    def reply_session_request(self, msg_id, chain_id, account_address):
        """Send the fort sessionRequest result."""
        session_request_result = {
            "peerId": self.wallet_id,
            "peerMeta": {
                "description": "pyWalletConnect by BitLogiK",
                "url": "https://github.com/bitlogik/pyWalletConnect",
                "icons": [""],
                "name": "pyWalletConnect",
            },
            "approved": True,
            "chainId": chain_id,
            "accounts": [account_address],
        }
        logger.debug("Replying the sessionRequest.")
        self.reply(msg_id, session_request_result)
