
# Uniblow on Linux

As Linux desktops are not very standardized among distributions, there is no yet uniblow binaries for Linux. The following instructions commands are given to run uniblow from the source. This can also be used for development purpose.

When running from the source files, for ETH, you have to put your Infura key in ETHwallet, or use the EtherscanAPI.

## Ubuntu / Debian / Mint

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