Uniblow
=======

![Uniblow logo](uniblow_logo.png)

A **uni**versal **blo**ckchain **w**allet for cryptos

- Handy, almost 1-click

- Fast and lightweight

- Multiple cryptos blockchains

- Tokens ERC20

- NFT ERC721 and BAB SBT

- WalletConnect v1 and v2

- Multiple networks (testnets,...)

- Multi-platform : PC, Mac and Linux

- Open source GPLv3

Official web site : https://uniblow.org  

![Uniblow screenshot](screenshot.png)

Don't expect to get advanced settings for the fees. This software provides an
easy and basic wallet, focused on universality and ease in use, as it works on
multiple blockchains and platforms.

Compatible with the following blockchains :

- BTC
  
  - mainnet and testnet networks
  
  - Standard wallet (P2PKH)
  
  - Segwit P2SH compatibility
  
  - Full Segwit wallet bech32 (P2WPKH)
  
  - Send to Taproot Bech32m address (P2TR)

- ETH
  
  - mainnet and Sepolia networks
  
  - ERC20 tokens, NFTs and SBTs
  
  - WalletConnect Dapps

- BSC
  
  - mainnet and testnet networks
  
  - BEP20 tokens, NFTs and SBTs
  
  - WalletConnect Dapps

- MATIC
  
  - Mainnet and Amoy networks
  
  - ERC20 tokens, NFTs
  
  - WalletConnect Dapps

- TRON
  
  - Mainnet, Shasta and Nile networks
  
  - TRC20 tokens

- Gnosis
  
  - Mainnet and Testnet networks
  
  - ERC20 tokens and NFTs tokens
  
  - WalletConnect Dapps

- FTM Opera
  
  - Mainnet and Testnet networks
  
  - ERC20 tokens, NFTs
  
  - WalletConnect Dapps

- Sonic
  
  - Mainnet and Blaze testnet networks
  
  - ERC20 tokens, NFTs
  
  - WalletConnect Dapps

- OP
  
  - Mainnet and Testnet networks
  
  - ERC20 tokens, NFTs
  
  - WalletConnect Dapps

- BASE
  
  - Mainnet and Testnet networks
  
  - ERC20 tokens, NFTs
  
  - WalletConnect Dapps

- METIS
  
  - Mainnet and Testnet networks
  
  - ERC20 tokens
  
  - WalletConnect Dapps

- CELO
  
  - Mainnet, Alfajores and Baklava networks
  
  - ERC20 tokens
  
  - WalletConnect Dapps

- GLMR
  
  - Moonbeam, Moonriver and Moonbase Alpha
  
  - ERC20 tokens
  
  - WalletConnect Dapps

- ARB
  
  - Arbitrum mainnet
  
  - ERC20 tokens, NFTs and SBTs
  
  - WalletConnect Dapps

- AVAX
  
  - Mainnet and Fuji testnet networks
  
  - ERC20 tokens, NFTs and SBTs
  
  - WalletConnect Dapps

- SOL
  
  - mainnet and testnet networks

- XTZ
  
  - tz1 wallet
  
  - tz2 wallet
  
  - Main Tezos and testnet Ghost networks

- LTC
  
  - mainnet network
  
  - Standard wallet (P2PKH)
  
  - Segwit P2SH compatibility

- DOGE
  
  - mainnet networks


Run Uniblow
-----------

On **Windows** : Minimum version is Windows 8.1

- Download the Uniblow binary [from the uniblow official website](https://uniblow.org/get).

To increase the security, the Windows exe releases are signed with the publisher [Extended
Validation certificate](https://en.wikipedia.org/wiki/Code_signing#Extended_validation_(EV)_code_signing), bringing even greater confidence in the integrity of the application.

On **Debian / Tails / Ubuntu** :

- Follow the [dedicated instructions page](docs/LinuxRunBin.md).

To increase the security, the Linux binaries releases are [signed with the publisher PGP
key](https://bitlogik.fr/pgp/bitlogik.asc), bringing even greater confidence in
the integrity of the application. The checking process is described in [this
instructions document](docs/LinuxRunBin.md).

On **MacOS**

- Download the Uniblow dmg package for Mac [from the uniblow official
  website](https://uniblow.org/get).

- Open the dmg to mount it.

- Drag and drop Uniblow (on the left) to the Applications icon on right.

- Eject the dmg disk and you can delete the dmg file.

To increase the security, the Mac dmg package and the uniblow app are
signed (stapled) and notarized by Apple, bringing greater confidence in the
integrity of the application.

Devices
-------

### Seed Watcher

Useful for paperwallets or one-time analysis of a mnemonic seed. This specific
device can be also useful to provide an ephemeral temporary wallet, in TailsOS
for example.

It is compatible with BIP39, SLIP39 (Trezor) and Electrum mnemonics. The derivation complies with BIP32/44 and SLIP10.

This device doesn't store permanently the private keys. It provides a window GUI
to read a mnemonic seed, analyzes it, and displays the major cryptos held by
this given mnemonic, with their respective balance. It can also securely
generate new BIP39 mnemonic seeds. Then one can load a given asset wallet in the
app to make some transactions.

The seed generated within SeedWatcher is BIP39 only, and is not compatible with
Electrum. You can't input a seed generated with Uniblow in an Electrum wallet
without selecting the BIP39 option in Electrum.

Note that Seed Watcher only looks at the one given address account/index. If you
used a full HD wallet for BTC, LTC or DOGE (such as Electrum), the whole balance
could not be recomputed properly.

Using the Electrum seed derivation, the same limitation applies : it can only
look at one address account at a time. That means it may not see all your full
Electrum account. You need to manually increase the index number. Additionally,
the SeedWatcher can't generate an Electrum compatible seed, still it can read an
Electrum seed (of one single address).

### Local File

This wallet is compatible with BIP39/32/44 wallets. You can save 12/24 words
when initializing a new one, and get back you fund late using this same
mnemonic.

You can also import an existing wallet from a compatible wallet, and it will use
the funds. Note there is a limitation on BTC, LTC and DOGE : it only uses one
static address for all transactions on a given blockchain. And it won't retrieve
your money if you use some other HD wallets with many transactions.

You can also export the saved words mnemonic in an other compatible wallet, and
it should access and use all your funds.

The Local File device stores the wallet seed in a file on your disk, in your
user data directory. The encryption is done with your password. LocalFile stores
only the seed encrypted [with a random salt using libsodium XSalsa20/Poly1305](https://libsodium.gitbook.io/doc/secret-key_cryptography/secretbox#algorithm-details),
using an encryption key derived from the user chosen password using [Argon2id
(moderate settings)](https://raw.githubusercontent.com/P-H-C/phc-winner-argon2/master/argon2-specs.pdf).
If you setup a password but forget it, there would be no way to recover your
coins from the backup file. But you can still initialize a new Local File wallet
with the same mnemonic words.

The seed of this wallet is encrypted and stored in a file named *HDseed.key*, in
the user data folder for Uniblow. To backup it, copy the file elsewhere. To
remove this wallet and start a fresh one, delete this file. You can also rename
it and that would start a new different Local File wallet, and keep the first
wallet aside. In this case, rename back to HDseed and you read back the first
wallet.

The folder where the HDseed file is stored, sits in the user data directory.

- Windows :  
  C:\\Users\\\<USER\>\\AppData\\Local\\BitLogiK\\Uniblow\\keys\\

- Linux :  
  \~/.local/share/Uniblow/keys/  
  or in \$XDG_DATA_HOME if defined

- MacOS :  
  \~/Library/Application Support/Uniblow/keys/

### Ledger

A Ledger hardware device such as Nano X and Nano S, can be used with Uniblow but
only for Ethereum/EVM chains (ETH, BSC, MATIC, GNO, FTM, OP, BASE, METIS, CELO, GLMR, MOVR, AVAX and ARB).

The Ledger needs to be unlocked and run the Ethereum app. The address displayed
in the wallet can be checked on the Ledger screen by clicking a dedicated UI
button. The Uniblow wallet has a tokens list integrated, which allows to send
thousands of major tokens without enabling the "blind signing" features.

In case you use Uniblow with the Ledger on a web3 dapp, with the WalletConnect
option, the transactions can require the "blind signing" option to be enabled in
the Ledger app. In this situation, a dedicated modal will appear asking you to
activate this, and you need to make the transaction again after the option
activation.

On Linux, the udev rules need to be allowed for the Ledger USB device. Run [this
official
script](https://raw.githubusercontent.com/LedgerHQ/udev-rules/master/add_udev_rules.sh)
as root/sudo to allow the Ledger device.

### Cryptnox card

The [Cryptnox card](https://cryptnox.com) is a crypto credit-card sized hardware wallet with advanced functionalities. This device is very secure thanks to its CC EAL6+ security grade central chip. The compatible models are the BG-1 and the B-NFT-1 cards (single or Dual).

When a BG-1 card is initialized using Uniblow, it generates a BIP39 mnemonic seed,
which is loaded in the the card. This mnemonic seed is displayed to the user
once during the initialization process, and acts as a backup for the internal
keys card. By design, there's no way to extract any private key from the card
after the setup. The only way to recover the wallet keys is to perform a new
initialization and input the same mnemonic provided. Note that the SeedWatcher
device also gives you a temporary and fast access to these keys from the
mnemonic, thanks to Cryptnox BIP39 compatibility.

Uniblow doesn't use many advanced features of this wallet, but only simple
stuff, to keep it simple and providing the same user experience as the others
devices. Uniblow uses the Cryptnox card only with a simple PIN authentication
method.

Uniblow can setup and initialize a blank BG1 card. The B-NFT-1 model shall be used already initialized.

If the BG1 card was not initialized using Uniblow, the card needs to be in a state :

- PIN enabled

- Standard secured channel key

- Seed or derivable key loaded

If the card is locked, only half initialized, or in a fancy state, you can use
the [CryptnoxPro](https://github.com/Cryptnox-Software/cryptnoxpro) or the [Cryptnox iOS app](https://apps.apple.com/app/id1583011693). Because Uniblow
cannot perform advanced operations such as PIN unlock, nor card reset.


### Satochip card

The [Satochip card](https://satochip.io) is an easy-to-use, [open-source](https://github.com/Toporin/SatochipApplet) hardware wallet based on a smartcard. 

Satochip can be initialized from Uniblow by providing a new PIN (4 to 16 alphanumeric characters) and a BIP39 seed. By design, once a seed is imported into Satochip, it cannot be recovered, and the private keys derived from the seed are never exported outside of the chip. So it is important that the user makes a backup of the mnemonic seed during the card initialization.

Satochip supports both contact (usb smartcard reader) and contactless (NFC) connections.

### OpenPGP device

Works with an OpenPGP v2/v3 device that accepts ECP 256K1 key pairs.

This device type is very secure, because the signature is performed in the
OpenPGP physical device, outside of the computer. Most of these devices are
built with a secure element chip. The private key never escapes the hardware
device boundary. Note that the drawback is that there is no easy backup of the
keys, so one have to take care of not forgetting the PIN or losing the device.  
Still, you can upload your own keyin this device, but this importation feature
is not supported by Uniblow.

For the best experience, the OpenPGP device should be in its default reset state
before using it with uniblow. Uniblow asks the user to choose the admin PIN
(PIN3), and the user PIN (PIN1), then it configures the device with these PINs.  
The device can also be already configured, with one EC256k1 key generated in the
SIG key slot. Uniblow will ask for the user PIN1 and use this key.

Without backup, if you forget the PIN, or lost the OpenPGP device, there would
be no way to recover your coins. Except if you initialized the PGP device on your
own and uploaded a key pair.

The Yubico 5 is a recommended OpenPGP device.

Special wallet options
----------------------

### Tokens / ERC20

In ETH, BSC, MATIC, TRX, GNO, FTM, OP, BASE, METIS, CELO, GLMR, MOVR, AVAX or ARB, you can enable the Tokens option. Select a known preset token, or input an ERC20
custom token contract address. It is TRC20 base58 address for Tron.

### NFT

Uniblow can display the NFT or SBT from the collection contract address. NFT ERC721 and SBT BAB are compatible on the networks : ETH, BSC, MATIC, GNO, OP, BASE, AVAX and ARB. You can select a known preset token, or input an NFT custom contract address.

### WalletConnect

In ETH, BSC, MATIC, GNO, FTM, OP, BASE, METIS, CELO, GLMR, MOVR, AVAX or ARB, Uniblow can connect to a Dapp
using the WalletConnect system. Click on the WalletConnect option,
input the wc URI and it will connect to the web3 app using WalletConnect.  
Note that in this mode, Uniblow disables sending any transaction from the GUI.
All the transactions have to be performed from the connected web app,
after your approval in Uniblow. Else you have to connect to a standard (or
token) account type to process a sending transaction using Uniblow directly.

With a Ledger device, the transactions can require the "blind signing" option to
be enabled in the Ledger ETH app.

The SecuBoost seed derivation type
----------------------------------

Uniblow is offering an alternative to [the BIP39 mnemonic derivation
method](https://en.bitcoin.it/wiki/BIP_0039). The SecuBoost algorithm is
specific to Uniblow, so it won't work in a different wallet. This derivation
option replaces the key derivation function of the BIP39 standard for a much
stronger one. The key derivation (BIP39 or SecuBoost) is used to turn your
mnemonic words list and password into the BIP32 seed (the H.D. wallet first data
key).

The benefit is that you can use a "weaker" password for your wallet, so it is
easy to remember. For example, 2 random words in the dictionary would take years
to recover. Similarly, only 5 random letters would take also years to be
recovered. By strengthening the derivation, one can use a password that is much
easier to remember. Another benefit is even without any password setup, it
protects your mnemonic better because the derivation is more difficult, and more
specific.

Technically, the [HMAC](https://en.wikipedia.org/wiki/HMAC)(SHA512 x 2048) is
replaced with
[Scrypt](http://passwords12.project.ifi.uio.no/Colin_Percival_scrypt/Colin_Percival_scrypt_Passwords12.pdf)(8x Sensitive, spaces removed).
A high-end [GPU hash-box](https://www.shellntel.com/blog/2017/2/8/how-to-build-a-8-gpu-password-cracker)
can perform 1 million BIP39 derivations per second. With SecuBoost, it is
approximately only 10 per second. The SecuBoost derivation is 100'000 times
slower and additionally it takes 1GB RAM per try, so it is also very robust
against large-scale parallel hardware attacks. The SecuBoost algorithm is
designed to use a larger amount of memory and time, making a hardware
implementation much more expensive, and therefore limiting the amount of
parallelism one can use for brute-force recovery. Even a dictionary attack would
be slowed down by this time factor.

Note that this algorithm, per design, uses extensive resources : requires 1 GB
RAM, and takes approximately 20 seconds on a desktop computer.

Development
-----------

### Run it from source

- **Windows** : Read the [WinDev document](docs/WinDev.md).

- **MacOS** : Read the [MacDev document](docs/MacDev.md).

- **Linux** : Read the [LinuxDev document](docs/LinuxDev.md)

### Build binaries

There are specific instructions and scripts to build uniblow binaries for the
Windows, Debian and MacOS platforms in a dedicated [build document](docs/Build.md).

License
-------

Copyright (C) 2021-2024 BitLogiK SAS

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the [GNU General Public License](LICENSE.md) for more
details.
