Uniblow development on MacOS
============================

The following instructions commands are given to run uniblow **from the source**
on the MacOS 11 system. This can also be used for development purpose.

When running from the source files, for ETH, you can put your Infura key in
ETHwallet, or use the EtherscanAPI.

There are specific instructions and scripts to build uniblow binaries for the
Windows, Debian and MacOS platforms in the [Build document](Build.md).

#### Install prerequisites

You MacOS system needs :

-   [Python 3.9
    pkg](https://www.python.org/ftp/python/3.9.7/python-3.9.7-macos11.pkg)
    installed

-   XCode and developer tools

#### Prepare system

Update the Python certificates, in the Terminal.

```
cd /Applications/Python\ 3.9/
./Install\ Certificates.command
```

#### Get the uniblow source
```
git clone https://github.com/bitlogik/uniblow.git
cd uniblow
```

#### Create venv for uniblow
```
python3 -m venv unibenv
source unibenv/bin/activate
```

#### Install uniblow dependencies
```
python -m pip install pip==21.2.1
python -m pip install wxPython==4.1.1 pyscard==2.0.1 pysha3==1.0.2 pynacl==1.4.0 pyWalletConnect==1.0.0
python -m pip install -e .
```

#### Run uniblow
```
python uniblow.py
```

#### Quit the venv
```
deactivate
```

#### Run uniblow next time

Within a terminal, in the uniblow directory
```
source unibenv/bin/activate
python uniblow.py
deactivate
```