Uniblow versions history

## 2.2.0

* Add NFT ERC721 and SBT BAB
* Update OP testnet
* Improve balance thread management
* Change internal derivation method BIP name

## 2.0.2

* Tezos : Add Ghost and Kathmandu test networks
* Fix Arbitrum wallet display
* Simplify Bitcoin transactions
* OpenPGP no more requires UIF

## 2.0.0

* Full redesign of the GUI
* Allow offline mode, display address
* Add fiat prices
* Improve Ledger
* Fix issue preventing start in some Windows
* Eth testnets add Sepolia, remove Rinkeby and Ropsten
* Tezos testnets add Jakarta remove Hangzhou

## 1.6.5

* Add Optimism
* METIS in SeedWatcher
* Fix Ledger device

## 1.6.4

* Change CELO and ARB RPC to Ankr
* GMLR is primary, not MOVR
* Raise the default WC gas limit
* Allow incorrect chars in WC eth_sign

## 1.6.2

* Add Cryptnox B-NFT-1 support
* Refine GUI balance

## 1.6.0

* Refine GUI in Windows
* Fix blank title in Windows
* Fix table shift when RPC error in SeedWatcher
* Update pyscard
* Update pyInstaller

## 1.5.3

* Improve SeedWatcher display for EOS
* Update pyWeb3 : improve web3 queries
* Add one more alternative derivation for ETH

## 1.5.2

* Add METIS
* Change web3 RPCs to ANKR, no more Infura
* Release resources when closing binary
* WCv1 auto-disconnect while running binary

## 1.5.1

* Refine GUI look
* Enforce PIN digits check in the GUI
* Fix modal closing
* Fix clipboard in info modal

## 1.5.0

* Remove BasicFile device
* HDdevice renamed to Local File
* Add the Cryptnox card device
* Add MOVR and GLMR chains
* Display min/max length for PIN or password
* Query and display PIN remaining tries
* WalletConnect v1 auto disconnect
* WC chain id mismatch fully ignored
* Balance always displayed as human float, no more sci
* GUI messages are clearer for hardware devices
* Improve UI aligments
* SeedWatcher color check indicators only for BIP39
* GUI grey area when not used
* Add PIN locked detection
* Improve EOS transactions following PowerUp
* Improve XTZ API error handling
* Improve OpenPGP devices compatibility

## 1.4.2

* Center balance display
* Fix WalletConnect issue to sign
* Update XTZ wallet
* XTZ RPC back to SmartPy
* ETH RPC default changed to ANKR
* Disable wallets input when balance back to 0
* OpenPGP checks the current key type in device
* Refactor devices : pubkey always binary uncompressed
* Updated pyWeb3 for better error handling
* Refactor Ledger device code

## 1.4.0

* Add Ledger device (for ETH/EVM, incl. tokens support)
* Add WalletConnect v2 (experimental)
* Improve UI/UX
* Action build for MacOS fixed for SSL CA
* Base device class created
* Update pyNaCl/libsodium

## 1.3.1

* Update XTZ wallet

## 1.3.0

* Add FTM, CELO and AVAX-c
* Gas price compatible with less than a Gwei
* RPC calls more reliable
* Enforce check on WalletConnect version

## 1.2.2

* BTC : Send to Taproot address P2TR (BIP341)
* Add full Bech32m BIP350 support
* Update XTZ networks and parameters
* Adding Electrum Old mnemonic in SeedWatcher

## 1.2.0

* Full account and index derivation options
* Write wallet files in the user data directory
* Various UI refinements
* Add ETH alternative derivation in SeedWatcher
* Change RPC for Polygon chain
* Fix disappearing SeedWatcher taskbar on Linux
* Mac build on Github Actions

## 1.0.4

* Add ARB and EOS in SeedWatcher
* Fix SeedWatcher info shift

## 1.0.2

* Improve ETH node queries reliability
* Better WalletConnect compatibility w/o chainID control

## 1.0.0

* Add ARB
* Unify Ethereum compliant wallets
* External pyWeb3 lib
* Update RPC endpoints selection
* Update preset tokens list
* Fix EOS wallet
* Fix BasicFile creation
* Fix OpenPGP wallet
* Python 3.9 in Windows

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
