# Uniblow development on Windows

The following instructions commands are given to run uniblow **from the source** on the Windows system. This can also be used for development purpose.

There are specific instructions and scripts to build uniblow binaries for the
Windows, Debian and MacOS platforms in the [Build document](Build.md).

In Windows, you can easily [run the binaries provided](https://uniblow.org/get). The following instructions here are only to run Uniblow from the Python source code, for development purpose.

### Install dependencies

- For the GUI, Install WxPython.
  
  - Install [Python3.9](https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe),
  
  - Then run `python -m pip install wxPython==4.2.0`

- Download the Uniblow source code
  
  with git : `git clone https://github.com/bitlogik/uniblow.git`
  
  Zip without git : [Download here](https://github.com/bitlogik/uniblow/archive/refs/heads/master.zip)

### Install and run uniblow

- In the uniblow directory, install the uniblow package and its dependencies (or use venv)
  
  - `python setup.py install --user`

- Run with `python uniblow.py -v`

The '-v' argument enables the debug logging output for more verbose terminal
output.
