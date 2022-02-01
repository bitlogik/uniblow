"""
*******************************************************************************
*   Ledger Hardware Wallet Python API
*   (c) 2014 BTChip
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


class LedgerException(Exception):
    def __init__(self, message, sw=0x6F00):
        self.message = message
        self.sw = sw

    def __str__(self):
        buf = "Exception : " + self.message
        return buf
