
# Building uniblow

This document provides specific instructions and scripts to build uniblow binaries for the Windows, Debian and MacOS platforms.

## Windows 10

* Install [Python 3.8](https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe)

* Get the [source files](https://github.com/bitlogik/uniblow/archive/refs/heads/master.zip), unzip.
    * You can alternatively clone this repository using your favorite Git client.

* Start the **Build-Windows** batch script in the *package* directory, double-click on this bat file to start it.

The pysha3 library may require the Microsoft Visual C++ 14.x build tools.

## Debian Buster

* Install required packages
```
sudo apt update
sudo apt install -y libsdl2-2.0-0 python3-venv python3-pip python3-pyscard
```

* Get the source files
```
BRANCH=master
curl -LOJ https://github.com/bitlogik/uniblow/archive/$BRANCH.tar.gz
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
bash package/Build-Debian.sh
```

## MacOS

* Install prerequisites, your MacOS system needs :

    -   [Python 3.9
    pkg](https://www.python.org/ftp/python/3.9.6/python-3.9.6-macos11.pkg)
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
