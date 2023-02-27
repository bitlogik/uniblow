
# Building uniblow

This document provides specific instructions and scripts to build uniblow binaries for the Windows, Ubuntu/Debian and MacOS platforms.

## Windows 10

* Install [Python 3.9](https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe)

* Install Microsoft Visual C++ 14.x build tools. Required for bootloader installer and pysha3 library compilation.

* Get the [source files](https://github.com/bitlogik/uniblow/archive/refs/heads/master.zip), unzip.
    * You can alternatively clone this repository using your favorite Git client.

* Start the **Build-Windows** batch script in the *package* directory, double-click on this bat file to start it.


## Linux (Ubuntu 18.04)

Requires Python >=3.7

* Install required packages
```
sudo add-apt-repository universe
sudo apt update
sudo apt install -y libnotify4 libgtk-3-0 libpcsclite-dev libsdl2-2.0-0 python3-venv python3-pip
```

* Get the source files
```
BRANCH=master
wget -O uniblow-$BRANCH.tar.gz https://github.com/bitlogik/uniblow/archive/$BRANCH.tar.gz
tar -xzf uniblow-$BRANCH.tar.gz
cd uniblow-$BRANCH
```

Or using Git

```
BRANCH=master
git clone https://github.com/bitlogik/uniblow.git
cd uniblow
git checkout $BRANCH
```


* Start the build script
```
bash package/Build-Linux.sh
```

## MacOS

* Install prerequisites, your MacOS system needs :

    -   [Python 3.9
    pkg](https://www.python.org/ftp/python/3.9.9/python-3.9.9-macos11.pkg)
    installed

    -   XCode and developer tools

* Get the uniblow source
```
git clone https://github.com/bitlogik/uniblow.git
cd uniblow
```

* Build uniblow
```
./package/Build-Mac.sh
```
