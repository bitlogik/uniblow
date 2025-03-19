Uniblow development on MacOS
============================

The following instructions commands are given to run uniblow **from the source**
on the MacOS 11-13 system. This can also be used for development purpose.

There are specific instructions and scripts to build uniblow binaries for the
Windows, Debian and MacOS platforms in the [Build document](Build.md).

#### Install prerequisites

You MacOS system needs :

- [Python 3.9 pkg](https://www.python.org/ftp/python/3.11.9/python-3.11.9-macos11.pkg) installed
- XCode and developer tools

#### Prepare system

Update the Python certificates, in the Terminal.

```
cd /Applications/Python\ 3.11/
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
python -m pip install swig
python -m pip install wxPython>=4.2.0
python -m pip install -e .
```

#### Run uniblow

```
python uniblow.py
```

The '-v' argument added enables the debug logging output for more verbose terminal
output.

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