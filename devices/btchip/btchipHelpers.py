"""
*******************************************************************************
*   BTChip Bitcoin Hardware Wallet Python API
*   (c) 2014 BTChip
*   (c) 2022 BitLogiK
*
*  Licensed under the Apache License, Version 2.0 (the "License");
*  you may not use this file except in compliance with the License.
*  You may obtain a copy of the License at
*
*      http://www.apache.org/licenses/LICENSE-2.0
*
*   Unless required by applicable law or agreed to in writing, software
*   distributed under the License is distributed on an "AS IS" BASIS,
*   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*  See the License for the specific language governing permissions and
*   limitations under the License.
********************************************************************************
"""

import re

from .btchipException import BTChipException


def writeUint32BE(value):
    return value.to_bytes(4, byteorder="big")


def parse_bip32_path(path):
    if len(path) == 0:
        return bytearray([0])
    result = b""
    elements = path.split("/")
    if len(elements) > 10:
        raise BTChipException("Path too long")
    for path_element in elements:
        element = re.split("'|h|H", path_element)
        if len(element) == 1:
            result += writeUint32BE(int(element[0]))
        else:
            result += writeUint32BE(0x80000000 | int(element[0]))
    return bytes([len(elements)]) + result


def read_uint8(data, offset):
    """Extract and decode utint8 at the given offset bytes"""
    return int.from_bytes(data[offset : offset + 1], "big")


def read_uint256(data, offset):
    """Extract and decode utint256 at the given offset bytes"""
    return int.from_bytes(data[offset : offset + 32], "big")
