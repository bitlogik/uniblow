
# Uniblow on Debian or Tails


We provide a Linux binary file which can be used directly on Tails OS and the Debian 10 Linux distribution, for the common x86/64 *AMD64* architecture.

For the following Linux OS :

* Tails v4.20, should work on any v4.x
* Debian Buster 10.10, should work on any 10.x "Buster"


### Download the binary

Get the binary and its signature file.

From the uniblow Github release page :
https://github.com/bitlogik/uniblow/releases/latest/

OR using the terminal, in Tails you need to prepend *torsocks* to these commands :
```
curl -LOJ https://github.com/bitlogik/uniblow/releases/latest/download/Uniblow-deb-x86_64-0.8.0
curl -LOJ https://github.com/bitlogik/uniblow/releases/latest/download/Uniblow-deb-x86_64-0.8.0.sig
```

### Check authenticity

The binary is signed with the PGP key of the editor's developer. You have to check the authenticity of the binary. This way, you can be sure it is the official approved binary from the editor, and was not altered in any way.

**Get the public key** :  
Tails  : `gpg --import <(torsocks curl https://keys.openpgp.org//vks/v1/by-email/antoine.ferron%40bitlogik.fr)`  
Debian : `gpg --import <(curl https://keys.openpgp.org//vks/v1/by-email/antoine.ferron%40bitlogik.fr)`

When the public key download is successful, it says `Total number processed/imported : 1`.

In Tails, if this outputs *No valid OpenPGP data found*, your Tor access node is probably banned from the web server : turn off and then connect again the network interface. That will change the Tor circuit.

**Check the binary signature** :

In Tails, using the Files explorer, you can right click on the sig file and select "Open With Verify Signature" in the context menu. Then a toast notification on top should display after the verification :  
*Uniblow : Untrusted Valid Signature*  
*Valid but untrusted signature by Antoine FERRON <antoine...*

OR alternatively using the Terminal, in Debian (also valid for Tails) :
```
UniblowFile=Uniblow-deb-x86_64-0.8.0
gpg --verify --trust-model always $UniblowFile.sig $UniblowFile
```

The terminal should give out something like :
```
gpg: Signature made ddd XXX 202y xx:xx:xx PM UTC
gpg:                using RSA key 9F8106C10FBDB88A71B7FEE5E353957C22F95B31
gpg: Good signature from "Antoine FERRON (BitLogiK) <antoine.ferron@bitlogik.fr>" [unknown]
gpg: WARNING: Using untrusted key!
```

The most important part to check for presence is *Good signature from Antoine FERRON (BitLogiK)*.

The warning message *untrusted* is because the key is not formally approved by *gpg*. But you are sure of the key since it was retrieved from an HTTPS trusted website.

Note that since you get the signed binary and the PGP key from 2 different sources (Github and the key server), a hacker would need to modify data in our Github account and our key. Else, you would notice with this signature check. Still, this doesn't protect our building process nor our PGP private key, there are dedicated security measures for those of course.


### Run it

Before to run Uniblow, you have to set as runnable once the binary, like tell Linux this is indeed an executable binary.

In the GUI, with a file explorer like Files, Nautilus or Nemo : right-click on the Uniblow file, select Properties. Then in the Permissions tab, tick the checkbox *Allow executing file as program* for the Execute option. Then close the properties window.

OR within the terminal :
```
chmod +x Uniblow-deb-*
```

Now, you can run Uniblow.

In **Tails**, the *torsocks* software is required to wrap the internet queries of the Uniblow app. Else you get the network error message *Network is unreachable*.
```
torsocks ./Uniblow-deb-x86_64-0.8.0
```


In **Debian**, you can directly run it from the file explorer GUI : double-click on the Uniblow binary icon to start it.

If nothing happens after some seconds, open a terminal in the current directory and type `./Uniblow-deb-x86_64-0.8.0`

