
# Uniblow on Ubuntu, Debian or Tails


We provide a **Linux binary file** which can be used directly on Ubuntu, Debian or Tails OS Linux distributions, for the common x86/64 *AMD64* architecture.

For the following Linux OS :

* Ubuntu from version 22.04
* Ubuntu derivatives, like Mint or PureOS
* Debian Bullseye 11
* Tails OS : Should work on any v5.x

It may run on other Linux, as RHEL or Fedora. But without any testing and no guarantee.

### Download the binary

Get the binary and its signature file.

**Download** from the uniblow website :  
[Uniblow program](https://uniblow.org/dist/Uniblow-linux-x86_64-2.6.4)  
 and its  
[PGP signature](https://uniblow.org/dist/Uniblow-linux-x86_64-2.6.4.sig)

**Or** using the terminal, in Tails you may need to prepend *torsocks* to these commands :
```
wget https://uniblow.org/dist/Uniblow-linux-x86_64-2.6.4
wget https://uniblow.org/dist/Uniblow-linux-x86_64-2.6.4.sig
```

### Check authenticity

The binary is signed with the PGP key of the editor's developer. You have to check the authenticity of the binary. This way, you can be sure it is the official approved binary from the editor, and was not altered in any way.

**Get the public key** :  
Tails   : `gpg --import <(torsocks wget -O - https://keys.openpgp.org//vks/v1/by-email/antoine.ferron%40bitlogik.fr)`  
Debian/Ubuntu : `gpg --import <(wget -O - https://keys.openpgp.org//vks/v1/by-email/antoine.ferron%40bitlogik.fr)`

When the public key download is successful, it says `Total number processed/imported : 1`.

In Tails, if this outputs *No valid OpenPGP data found*, your Tor access node is probably banned from the web server : turn off and then connect again the network interface. That will change the Tor circuit.

**Check the binary signature** :

In Tails, using the Files explorer, you can right click on the sig file and select "Open With Verify Signature" in the context menu. Then a toast notification on top should display after the verification :  
*Uniblow : Untrusted Valid Signature*  
*Valid but untrusted signature by Antoine FERRON <antoine...*

OR alternatively using the Terminal, in Debian/Ubuntu (also valid for Tails) :
```
UniblowFile=Uniblow-linux-x86_64-2.6.4
gpg --verify --trust-model always $UniblowFile.sig $UniblowFile
```

The terminal should give out something like :
```
gpg: Signature made ddd XXX 202y xx:xx:xx PM UTC
gpg:                using RSA key 9F8106C10FBDB88A71B7FEE5E353957C22F95B31
gpg: Good signature from "Antoine FERRON (BitLogiK) <antoine.ferron@bitlogik.fr>" [unknown]
gpg: WARNING: Using untrusted key!
```

The most important part to check for presence is *Good signature from Antoine FERRON (BitLogiK)* with the RSA key id.

The warning message *untrusted* is because the key is not formally approved by *gpg*. But you are sure of the key since it was retrieved from an HTTPS trusted website.

Note that since you get the signed binary and the PGP key from 2 different sources (Web distribution server and a key server), a hacker would need to modify data in our web distribution server and our key. Else, you would notice with this signature check. Still, this doesn't protect our building process nor our PGP private key, there are dedicated security measures for those of course.


### Run it

Before to run Uniblow, you have to set as runnable once the binary, like tell Linux this is indeed an executable binary.

In the GUI, with a file explorer like Files, Nautilus or Nemo : right-click on the Uniblow file, select Properties. Then in the Permissions tab, tick the checkbox *Allow executing file as program* for the Execute option. Then close the properties window.

OR within the terminal :
```
chmod +x Uniblow-linux-*
```

Now, you can run Uniblow.

In **Tails**, the *torsocks* software is required to wrap the internet queries of the Uniblow app. Else you get the network error message *Network is unreachable*.
```
torsocks ./Uniblow-linux-x86_64-2.6.4
```


In **Debian or Ubuntu**, you can directly run it from the file explorer GUI : double-click on the Uniblow binary icon to start it.

If nothing happens after some seconds, open a terminal in the current directory and type `./Uniblow-linux-x86_64-2.6.4`

