#!/usr/bin/env bash

# Build uniblow Debian/Ubuntu binary package release


if ! (cat /etc/os-release | grep -E "20\.04(\.[0-9]+)? LTS \(Focal Fossa\)" > /dev/null ) then
  echo "This Uniblow building script only runs on Ubuntu 18.04."
  exit 1
fi

function is_installed {
  if [ $(dpkg-query -W -f='${Status}' $1 2>/dev/null | grep -c "ok installed") -eq 0 ]; then
      echo 'not'
    fi
}

softs_req=('libnotify4' 'libgtk-3-0' 'libpcsclite-dev' 'libsdl2-dev' 'python3-venv' 'python3-pip')

for softr in "${softs_req[@]}"; do
  if [ "$(is_installed $softr)" == 'not' ]; then
    echo ERROR :
    echo $softr needs to be installed
    echo run sudo apt install -y $softr 
    exit 1
  fi
done

rm -Rf dist

echo Initializing the venv ...
python3 -m venv --system-site-packages unibenvi
source unibenvi/bin/activate
python -m pip install -U pip

echo Installing pip dependencies ...

python -m pip install https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/wxPython-4.2.0-cp38-cp38-linux_x86_64.whl
python -m pip install -U pip

python setup.py install
python -m pip install pyinstaller==4.10

echo Building package ...
python -OO -m PyInstaller package/uniblow.spec
deactivate

echo Compilation done.
echo Binary result is in the dist folder.
