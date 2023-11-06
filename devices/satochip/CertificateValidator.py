#!/usr/bin/python3
# -*- coding: utf8 -*-

# Satochip smartcard certificate validation
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

import os
import traceback
import logging

from cryptography import x509
from cryptography.hazmat.primitives.serialization import PublicFormat, Encoding
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CertificateValidator:
    def __init__(self, loglevel=logging.WARNING):
        logger.setLevel(loglevel)
        # logger.setLevel(logging.DEBUG) # force DEBUG
        logger.debug("In __init__")

    def validate_certificate_chain(self, device_pem, device_type, is_test_ca=False):
        logger.debug("DEBUG: In validate_certificate_chain")

        txt_ca = txt_subca = txt_device = txt_error = ""
        device_pubkey = bytes(65 * [0])
        device_pem_bytes = device_pem.encode("utf-8")

        # load subca according to device type
        directory = os.path.join(os.path.dirname(__file__), "cert")
        logger.debug(f"directory: {directory}")
        path_ca = os.path.join(directory, "ca.cert")
        if device_type == "Satochip":
            path_subca = os.path.join(directory, "subca-satochip.cert")
        else:
            txt_error = "Unknown card_type: " + str(device_type)
            return False, device_pubkey, txt_ca, txt_subca, txt_device, txt_error

        # # for testing purpose only, ignore!
        # if is_test_ca:
        #     #path_ca = os.path.join(directory, 'bad-ca.cert') #for testing purpose!
        #     path_ca = os.path.join(directory, 'test-ca.cert') #for testing purpose!
        #     path_subca = os.path.join(directory, 'test-subca-seedkeeper.cert') #for testing purpose!

        # todo: FileNotFoundError
        logger.debug(f"path_ca: {path_ca}")
        logger.debug(f"path_subca: {path_subca}")
        with open(path_ca, "r", encoding="utf-8") as f:
            ca_pem = f.read()
            ca_pem_bytes = ca_pem.encode("utf-8")
            logger.debug("CA pem: " + ca_pem)
        with open(path_subca, "r", encoding="utf-8") as f:
            subca_pem = f.read()
            subca_pem_bytes = subca_pem.encode("utf-8")
            logger.debug("SUBCA pem: " + subca_pem)
        # print("DEVICE pem: " + device_pem)

        try:
            logger.debug("Trying to parse certs...")
            ca_cert = x509.load_pem_x509_certificate(ca_pem_bytes)
            txt_ca = self.dump_certificate_info(ca_pem, ca_cert)
            subca_cert = x509.load_pem_x509_certificate(subca_pem_bytes)
            txt_subca = self.dump_certificate_info(subca_pem, subca_cert)
            device_cert = x509.load_pem_x509_certificate(device_pem_bytes)
            txt_device = self.dump_certificate_info(device_pem, device_cert)
        except Exception as ex:
            logger.warning(f"Exception: {ex}")
            logger.warning(traceback.format_exc())
            txt_error = "Exception during pem certificates parsing: " + str(ex)
            return False, device_pubkey, txt_ca, txt_subca, txt_device, txt_error

        # extract pubkey from device certificate
        ca_pubkey = ca_cert.public_key()
        logger.debug(f"CA pubkey: {ca_pubkey}")
        subca_pubkey = subca_cert.public_key()
        logger.debug(f"SUBCA pubkey: {subca_pubkey}")
        device_pubkey_object = device_cert.public_key()
        device_pubkey = device_pubkey_object.public_bytes(
            Encoding.X962, PublicFormat.UncompressedPoint
        )
        logger.debug(f"DEVICE pubkey: {device_pubkey.hex()}")

        # verify certificate signature
        # we only verify signature between subca and device,
        # since ca and subca are hardcoded in pysatochip
        try:
            subca_pubkey.verify(
                device_cert.signature,
                device_cert.tbs_certificate_bytes,
                ec.ECDSA(hashes.SHA256()),
                # device_cert.signature_algorithm_parameters, # only available starting cryptography v41
            )
        except Exception as ex:
            logger.warning(f"Exception: {ex}")
            logger.warning(traceback.format_exc())
            txt_error = "Failed to verify device certificate signature: " + str(ex)
            return False, device_pubkey, txt_ca, txt_subca, txt_device, txt_error

        # if is_test_ca:
        #     txt_error= "WARNING: Chain certificate validated with TEST CA! NOT FOR PRODUCTION!"
        #     return False, device_pubkey, txt_ca, txt_subca, txt_device, txt_error

        return True, device_pubkey, txt_ca, txt_subca, txt_device, txt_error

    def dump_certificate_info(self, cert_pem, cert_obj):
        cert_txt = ""
        cert_txt += f"version: {cert_obj.version} \n"
        cert_txt += f"serial_number: {cert_obj.serial_number} \n"
        cert_txt += f"issuer: {cert_obj.issuer} \n"
        cert_txt += f"not_valid_before: {cert_obj.not_valid_before} \n"
        cert_txt += f"not_valid_after: {cert_obj.not_valid_after} \n"
        cert_txt += f"subject: {cert_obj.subject} \n"
        cert_txt += f"signature_hash_algorithm: {cert_obj.signature_hash_algorithm.name} \n"
        # cert_txt+= f"signature_algorithm_parameters: {cert_obj.signature_algorithm_parameters} \n" # only available in cryptography v41+
        cert_txt += f"signature_algorithm_oidsignature: {cert_obj.signature_algorithm_oid} \n"
        cert_txt += f"signature: {cert_obj.signature.hex()} \n"
        # cert_txt+= f"tbs_certificate_bytes: {cert_obj.tbs_certificate_bytes.hex()} \n"
        cert_txt += f"pubkkey: {cert_obj.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint).hex()} \n"
        cert_txt += "extension(s): \n"
        for ext in cert_obj.extensions:
            cert_txt += f"{ext} \n"
        # cert_txt+= f"\n\n"
        # cert_txt+= f"cert_pem: \n"
        # cert_txt+= f"{cert_pem}"

        logger.debug(f"Certificate: \n{cert_txt}")
        return cert_txt
