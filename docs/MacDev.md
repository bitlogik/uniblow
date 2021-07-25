Uniblow development on MacOS
============================

The following instructions commands are given to run uniblow **from the source**
on the MacOS 11 system. This can also be used for development purpose.

When running from the source files, for ETH, you can put your Infura key in
ETHwallet, or use the EtherscanAPI.

There are specific instructions and scripts to build uniblow binaries for the
Windows and Debian platforms in the [Build document](docs/Build.md).

**Note** : The MacOS support for Uniblow is for now experimental. There are some
issues and the app can freeze.

Known issues :

-   No contect menu in SeedWatcher
-   App window freezes after the error modal shown


#### Install prerequisites

You MacOS system needs :

-   [Python 3.8
    pkg](https://www.python.org/ftp/python/3.8.10/python-3.8.10-macos11.pkg)
    installed

-   XCode and developer tools

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
python -m pip install wxPython==4.1.1 pyscard=2.0.0 pysha3==1.0.2 pynacl==1.4.0
python -m pip install .
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