
# Uniblow development on Linux

A binary is given to run on Tails and Debian OS. For easy run on these platforms, check the [specific instructions in the LinuxBin doc](docs/LinuxBin.md) instead.

The following instructions commands are given to run uniblow **from the source** and build on various Linux distributions. This can also be used for development purpose.

When running from the source files, for ETH, you can put your Infura key in ETHwallet, or use the EtherscanAPI.

## Debian

For Debian 10

#### Install system packages
```
sudo apt update
sudo apt install -y git libsdl2-2.0-0 python3-pip python3-pyscard
```

#### Install required packages 
```
sudo python3 -m pip install -U pip
sudo python3 -m pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/debian-10/wxPython-4.1.1-cp37-cp37m-linux_x86_64.whl wxPython
python3 -m pip install -U pip setuptools-rust
```

#### Get the uniblow source
```
git clone https://github.com/bitlogik/uniblow.git
cd uniblow
```

#### Install uniblow dependencies
```
python3 setup.py install --user
```

#### Run uniblow
```
python3 uniblow.py
```

#### Build binary
```
python3 -m pip install pyinstaller
python3 -O -m PyInstaller package/uniblow.spec
```
## Ubuntu / Mint

Tested on Ubuntu 20.04

#### Install system packages

```
sudo add-apt-repository universe < /dev/null
sudo apt update < /dev/null
sudo apt install -y git python3-pip < /dev/null
```

#### Install required packages (Ubuntu 20.04)
```
sudo apt install -y libsdl2-dev < /dev/null
sudo pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04 wxPython < /dev/null
sudo apt install -y python3-pyscard < /dev/null
```

#### Get the uniblow source
```
git clone https://github.com/bitlogik/uniblow.git
cd uniblow
```

#### Install uniblow dependencies
```
python3 setup.py install --user
```

#### Run uniblow
```
python3 uniblow.py
```

#### Build binary
```
python3 -m pip install pyinstaller
python3 -O -m PyInstaller package/uniblow.spec
```

## Fedora / RHEL / centOS

Tested on Fedora 32-34

#### Install system packages
```
sudo dnf install -y git python3-pip
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

#### Install uniblow dependencies
```
python3 setup.py install --user
```

#### Run uniblow
```
python3 uniblow.py
```

#### Build binary
```
python3 -m pip install pyinstaller
python3 -O -m PyInstaller package/uniblow.spec
```