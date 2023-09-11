"""
 * Python API for the SatoChip Bitcoin Hardware Wallet
 * (c) 2015 by Toporin - 16DMCk4WUaHofchAhpMaQS4UPm4urcy2dN
 * Sources available on https:#github.com/Toporin
 *
 * Copyright 2015 by Toporin (https:#github.com/Toporin)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http:#www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
"""

class JCconstants:

    # code of CLA byte in the command APDU header
    CardEdge_CLA =  0xB0

    '''****************************************
       *         Instruction codes            *
       ****************************************'''

    # Applet initialization
    INS_SETUP =  0x2A;

    # Keys' use and management
    INS_GEN_KEYPAIR =  0x30;
    INS_GEN_KEYSYM =  0x31;
    INS_IMPORT_KEY =  0x32;
    INS_EXPORT_KEY =  0x34;
    INS_GET_PUBLIC_FROM_PRIVATE= 0x35;
    INS_COMPUTE_CRYPT =  0x36;
    INS_COMPUTE_SIGN =  0x37; # added

    # External authentication
    INS_CREATE_PIN =  0x40;
    INS_VERIFY_PIN =  0x42;
    INS_CHANGE_PIN =  0x44;
    INS_UNBLOCK_PIN =  0x46;
    INS_LOGOUT_ALL =  0x60;
    INS_GET_CHALLENGE =  0x62;
    INS_EXT_AUTH =  0x38;

    # Objects' use and management
    INS_CREATE_OBJ =  0x5A;
    INS_DELETE_OBJ =  0x52;
    INS_READ_OBJ =  0x56;
    INS_WRITE_OBJ =  0x54;
    INS_SIZE_OBJ =  0x57;

    # Status information
    INS_LIST_OBJECTS =  0x58;
    INS_LIST_PINS =  0x48;
    INS_LIST_KEYS =  0x3A;
    INS_GET_STATUS =  0x3C;

    # HD wallet
    INS_COMPUTE_SHA512 =  0x6A;
    INS_COMPUTE_HMACSHA512=  0x6B;
    INS_BIP32_IMPORT_SEED=  0x6C;
    INS_BIP32_RESET_SEED=  0x77;
    INS_BIP32_GET_AUTHENTIKEY=  0x73;
    INS_BIP32_GET_EXTENDED_KEY=  0x6D;
    INS_SIGN_MESSAGE=  0x6E;
    INS_SIGN_SHORT_MESSAGE=  0x72;
    INS_SIGN_TRANSACTION=  0x6F;
    INS_BIP32_SET_EXTENDED_KEY=  0x70;
    INS_PARSE_TRANSACTION =  0x71;

    # 2FA
    INS_SET_2FA_KEY = 0x79;
    
    # Secure Channel
    INS_INIT_SECURE_CHANNEL =  0x81;
    INS_PROCESS_SECURE_CHANNEL =  0x82;
    
    # Perso PKI
    INS_IMPORT_PKI_CERTIFICATE = 0x92;
    INS_EXPORT_PKI_CERTIFICATE = 0x93;
    INS_SIGN_PKI_CSR = 0x94;
    INS_SET_ALLOWED_CARD_AID = 0x95;
    INS_GET_ALLOWED_CARD_AID = 0x96;
    INS_EXPORT_PKI_PUBKEY = 0x98;
    INS_LOCK_PKI = 0x99;
    INS_CHALLENGE_RESPONSE_PKI= 0x9A;


    '''****************************************
       *             Error codes              *
       ****************************************'''
    #o error!
    SW_OK = 0x9000;
    # There have been memory problems on the card
    SW_NO_MEMORY_LEFT = 0x9c01;
    # Entered PIN is not correct */
    SW_AUTH_FAILED =  0x9C02;
    # Required operation is not allowed in actual circumstances
    SW_OPERATION_NOT_ALLOWED =  0x9C03;
    # Required setup is not not done */
    SW_SETUP_NOT_DONE =  0x9C04;
    # Required feature is not (yet) supported */
    SW_UNSUPPORTED_FEATURE =  0x9C05;
    # Required operation was not authorized because of a lack of privileges */
    SW_UNAUTHORIZED =  0x9C06;
    # Required object is missing */
    SW_OBJECT_NOT_FOUND =  0x9C07;
    # New object ID already in use */
    SW_OBJECT_EXISTS =  0x9C08;
    # Algorithm specified is not correct */
    SW_INCORRECT_ALG =  0x9C09;

    # Incorrect P1 parameter */
    SW_INCORRECT_P1 =  0x9C10;
    # Incorrect P2 parameter */
    SW_INCORRECT_P2 =  0x9C11;
    # No more data available */
    SW_SEQUENCE_END =  0x9C12;
    # Invalid input parameter to command */
    SW_INVALID_PARAMETER =  0x9C0F;

    # Verify operation detected an invalid signature */
    SW_SIGNATURE_INVALID =  0x9C0B;
    # Operation has been blocked for security reason */
    SW_IDENTITY_BLOCKED =  0x9C0C;
    # Unspecified error */
    SW_UNSPECIFIED_ERROR =  0x9C0D;
    # For debugging purposes */
    SW_INTERNAL_ERROR =  0x9CFF;
    # For debugging purposes 2*/
    SW_DEBUG_FLAG =  0x9FFF;
    # Very low probability error */
    SW_BIP32_DERIVATION_ERROR =  0x9C0E;
    # Support only hardened key currently */
    SW_BIP32_HARDENED_KEY_ERROR =  0x9C16;
    # Incorrect initialization of method */
    SW_INCORRECT_INITIALIZATION =  0x9C13;
    # Bip32 seed is not initialized*/
    SW_BIP32_UNINITIALIZED_SEED =  0x9C14;
    # Incorrect transaction hash */
    SW_INCORRECT_TXHASH =  0x9C15;

    '''****************************************
       *          Algorithm codes             *
       ****************************************'''

    # Cipher Operations admitted in ComputeCrypt()
    OP_INIT =  0x01;
    OP_PROCESS =  0x02;
    OP_FINALIZE =  0x03;
