
# Uniblow development on Linux

A binary is provided to run on Ubuntu, Debian and Tails OS, for AMD64 cpu arch. For easy run on these platforms, check the [specific instructions in the LinuxRunBin doc](LinuxRunBin.md) instead.

The following instructions commands are given to run uniblow **from the source** on various Linux distributions. This can also be used for development purpose.

Additionally, there are specific instructions and scripts to build uniblow binaries for the Windows, Debian/Ubuntu and MacOS platforms in the [Build document](Build.md).

When running from the source files, for ETH testnets, you can put your Infura key in ETHwallet.

## Run on Linux

This document presents instructions how to run uniblow from source on the following Linux flavors :

* [Debian](#debian)
* [Ubuntu / Mint](#ubuntu--mint)
* [Fedora / RHEL / CentOS](#fedora--rhel--centos)

## Debian

For Debian 10-11

#### Install system packages
```
sudo apt update
sudo apt install -y git libnotify4 libgtk-3-0 libpcsclite1 libsdl2-2.0-0 python3-venv python3-pip python3-pyscard
```

#### Install required packages 
```
python3 -m pip install -U pip < /dev/null
python3 -m pip install https://extras.wxpython.org/wxPython4/extras/linux/gtk3/debian-10/wxPython-4.1.1-cp37-cp37m-linux_x86_64.whl < /dev/null
python3 -m pip install -U pip setuptools-rust < /dev/null
```

#### Get the uniblow source
```
git clone https://github.com/bitlogik/uniblow.git
cd uniblow
```

#### Create venv for uniblow
```
python3 -m venv --system-site-packages unibenv
source unibenv/bin/activate
```

#### Install uniblow dependencies
```
python setup.py install
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


## Ubuntu / Mint

Tested on Ubuntu 20.04

#### Install system packages

```
sudo add-apt-repository universe < /dev/null
sudo apt update < /dev/null
sudo apt install -y git python3-venv python3-pip < /dev/null
```

#### Install required packages (Ubuntu 20.04)
```
sudo apt install -y libsdl2-dev < /dev/null
python3 -m pip install -U pip < /dev/null
sudo pip3 install https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/wxPython-4.1.1-cp38-cp38-linux_x86_64.whl < /dev/null
sudo apt install -y python3-pyscard < /dev/null
```


The wxPython link has to be changed for the good one that fits your ditro. Check [here in the list](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/) for your distro. Also some modern Ubuntu based distros can work with the *whl* in [the ubuntu-18.04 directory](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-18.04/). Because there's no *cp39* package in ubuntu-20.04, but there is one in ubuntu-18.04.


#### Get the uniblow source
```
git clone https://github.com/bitlogik/uniblow.git
cd uniblow
```

#### Create venv for uniblow
```
python3 -m venv --system-site-packages unibenv
source unibenv/bin/activate
```

#### Install uniblow dependencies
```
python setup.py install
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


## Fedora / RHEL / centOS

Tested on Fedora 32-34

#### Install system packages
```
sudo dnf install -y git python3-virtualenv python3-pip
```

#### Install required packages
```
sudo dnf -y groupinstall "Development Tools" "Development Libraries" < /dev/null
sudo dnf -y install gcc-c++ wxGTK3-devel python3-pyscard < /dev/null
```

#### Get the uniblow source
```
git clone https://github.com/bitlogik/uniblow.git
cd uniblow
```

#### Create venv for uniblow
```
python3 -m venv --system-site-packages unibenv
source unibenv/bin/activate
```

#### Install uniblow dependencies
```
python -m pip install -U pip
python setup.py install
```

#### Run uniblow
```
python uniblow.py -v
```

#### Quit the venv
```
deactivate
```

#### Run uniblow next time

Within a terminal, in the uniblow directory
```
source unibenv/bin/activate
python uniblow.py -v
deactivate
```

The '-v' argument enables the debug logging output for more verbose terminal output.
