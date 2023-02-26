
# Uniblow development on Linux

A binary is provided to run on Ubuntu, Debian and Tails OS, for AMD64 cpu arch. For easy run on these platforms, check the [specific instructions in the LinuxRunBin doc](LinuxRunBin.md) instead.

The following instructions commands are given to run uniblow **from the source** on various Linux distributions. This can also be used for development purpose.

Additionally, there are specific instructions and scripts to build uniblow binaries for the Windows, Debian/Ubuntu and MacOS platforms in the [Build document](Build.md).

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
python3 -m pip install https://extras.wxpython.org/wxPython4/extras/linux/gtk3/debian-10/wxPython-4.2.0-cp37-cp37m-linux_x86_64.whl < /dev/null
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


#### Install system packages

```
sudo add-apt-repository universe < /dev/null
sudo apt update < /dev/null
sudo apt install -y git python3-venv python3-pip < /dev/null
```

#### Install required packages (For Ubuntu 20.04)
```
sudo apt install -y libsdl2-dev < /dev/null
python3 -m pip install -U pip < /dev/null
sudo pip3 install https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/wxPython-4.2.0-cp38-cp38-linux_x86_64.whl < /dev/null
sudo apt install -y python3-pyscard < /dev/null
```


The wxPython link has to be changed for the good one that fits your distro. Check [here in the list](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/) for your distro.

For 18.04 systems, [the whl for 18.04-cp36](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-18.04/wxPython-4.1.1-cp36-cp36m-linux_x86_64.whl) has to be used.

For Ubuntu from version 20.04 and 21.04 [this whl for cp38](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/wxPython-4.2.0-cp38-cp38-linux_x86_64.whl) can be used. The systemd package might be required to be installed for libsdl2. 3.9 for 21.04?

For Ubuntu from version 22.04 [this whl for cp310](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04/wxPython-4.2.0-cp310-cp310-linux_x86_64.whl) can be used. The systemd package might be required to be installed for libsdl2.

All the wxPython wheel binaries are provided for the AMD64 architecture. To run on any others CPU architecture, the wxPython has to be compiled from sources.

In such cases, calling *pip3 install wxPython==4.2.0* will download the source archive and will attempt to build it for you. If you have the required compiler and dependent libraries installed, then this will be a feasible approach, although it can take some time to do the build. The end result will be the same as if there was a binary wheel available. Pip can also be told to just build the wheel and not do the install. This way you can reuse the wheel file for different Python environments or on other similar machines, without needing to rebuild for each one. [This web page](https://wxpython.org/blog/2017-08-17-builds-for-linux-with-pip/index.html) can help you in such process.

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
