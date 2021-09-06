
Uniblow versions history

## 0.9.8

* Full compliant with SLIP10 : k1, r1 and Ed keys
* Add SOL
* Add Tezos tz1
* Tezos testnet changed to Florence
* Fix clipboard in SeedWatcher

## 0.9.7

* Improve Linux build
* Fix History open on some Linux
* Fix Copy clipboard on MacOS
* Add internal EC pair for R1 and Ed (SLIP10)
* Fix BSC transactions

## 0.9.6

* Improve GUI UX
* SeedWatcher wallets seeking done in background
* Works on Python 3.6
* Full WalletConnect support
* WalletConnect auto reconnect
* Build in Gitlab Actions

## 0.9.4

* Fix GUI : options selection displayed

## 0.9.3

* Fix possible bad message when not enough balance
* Allow null chainID from web3 dapp
* Improve UI/UX recover on error

## 0.9.2

* First MacOS binary package
* Many fixes for MacOS GUI
* Update packaging scripts

## 0.9.0

* WalletConnect compatible
* Add MATIC
* Tokens preset list
* Refine GUI
* SeedWatcher wallet can use all options
* Improve address and amount check
* Add logging
* CLI -v arg for debug log output

## 0.8.0

* Hand cursor for buttons
* Customized images buttons
* Add Electrum seed in SeedWatcher
* Choices label enabled
* Improved API errors output
* Rework EOS wallet, eospy removed
* EOS wallet is PowerUp capable
* Change balance timer
* Fix docs

## 0.6.0

* Add ERC20 and BEP20 tokens
* Can select the HD-BIP44 account index
* Can use a BIP39 password
* Action context menu in SeedWatcher
* SeedWatcher addresses can be opened in wallet
* Add the SecuBoost derivation capability
* Fix the input value (negative, float errors)
* Various GUI improvements
* More code reusability
* Binary release for Debian and Tails
* Full building script for Debian binary

## 0.5.0

* Add a Seed Watcher
* Major rewrite of the crypto libraries
    * Cleaner, smaller, more modern
    * Using exclusively cryptography lib and Python internal
    * Get rid of the external ecdsa lib
    * Testing (from standards tests vectors)
* Add Binance Smart Chain
* Binary detail properties added for Windows

## 0.4.0

* Add new HD BIP32/39/44 wallet device
* Add History button
* Display ETH address checksummed
* Improve XTZ signatures reliability

## 0.3.0

* Add XTZ
* Message modal text copiable
* Full checksum computation
* Improved UI check feedback
* EOS Jungle API updated
* EOS balance checked before sending
* Fix HDPI capability

## 0.2.0

* Add DOGE
* Add LTC
* Add EOS
* Detect when spending negative value
* More abstract device
* Modal when making a transaction
* Add OpenPGP device

## 0.1.0

* Change device creation modal type
* Highlight the destination address from check
* Copy button disabled on start

## 0.0.2

* Fix freeze when network error
* Assess tx size for BTC (lower fee when Segwit)
* Update GUI and device loading
* Add a password for the BasicFile device key
* Transfer all with Swipe Max button
* Compile Windows binary with Python 3.8

## 0.0.1

* First version
* BTC and ETH
* Basic File device (no password)
* QRcode
* clipboard copy
* Windows binary
