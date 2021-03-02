
# Uniblow

![Uniblow logo](uniblow_logo.png)

A **uni**versal **blo**ckchain **w**allet for cryptos

* Handy, almost 1-click
* Fast and lightweight
* Don't wait for confirmation, instant transactions
* Multiple cryptos blockchains
* Multiple networks (testnets,...)
* Multi platforms : PC, Mac and Linux
* Open source GPLv3

The Uniblow software can also be used integrated in your services, as it provides a unified, platform agnostic and blockchain agnostic interface to manage many differents wallets. By using the wallet class, this is as simple as : `ETH_wallet = wallet("ETH")`, and you get the interface methods mentioned in the developer section below.

![Uniblow screenshot](screenshot.png)

Don't expect to make complicated DeFi transactions, nor advanced settings for the fees. This software provides an easy and basic wallet, focused on universality and ease in use, as it works on multiple blockchains and platforms.

For now, works with :

* BTC
    * mainnet and testnet networks
    * Standard wallet
    * Segwit P2SH compatibility
    * Full Segwit bech32
* ETH
    * mainnet, Rinkeby, Ropsten, Kovan and Goerli networks

Note : the BasicFile device does not provide any security to protect your private key, except the security your hard-drive computer offers for your files.

ToDo list in development :

* EOS network
* ERC20 tokens on ETH
* LTC, BCH, DOGE
* Use win32 CNG key storage TPM as device
* PGP device to secure with a hardware key

## Use the GUI

* Download the Uniblow binary in Github releases

To increase security, the Windows exe releases are [signed with our Extended Validation certificate](https://en.wikipedia.org/wiki/Code_signing#Extended_validation_(EV)_code_signing), bringing even greater confidence in the integrity of
the application.

## Development

### Use it from source

* For the GUI, [install wxPython 4](https://wxpython.org/pages/downloads/) with your system binaries wheels.
    * Windows and MacOS: Use `pip3 install -U wxPython`
    * Linux : use your package manager, as `apt-get install python3-wxgtk4.0`
* Install dependencies
    * `python3 -m pip install -U cryptography ecdsa pysha3 qrcode`
* For ETH, put your Infura key in ETHwallet, or use the EtherscanAPI

### Add more cryptos

For developers, one can easily add any crypto in this wallet, following this Python3 programming interface class :

```Python
class newCOINwallet:
    def __init__(self, coin, *options):
     ... create the wallet, for now options is network,wtype indexes (indexing the list returned by get_networks and get_account_types)

    def get_networks(self):
     ... return list of different possible networks names

    def get_account_types(self):
     ... return list of different possible account types

    def get_account(self):
    ... return the account name (address or similar)

    def get_balance(self):
     ...

    def check_address(self, addr_str):
     ... return True if the address/account name is valid
    
    def history(self):
     ... return a tx list for this account (not used for now)

    def transfer(self, amount, to_account, fee):
     ... transfer to pay x coin unit to an external account and return txid
     ... fee is 0, 1 or 2 : "economic", "normal", "fast"
    
    def transfer_all(self, to_account, fee_priority):
     ... transfer all the wallet to an address (minus fee)
     ... fee is 0, 1 or 2 : "economic", "normal", "fast"
```