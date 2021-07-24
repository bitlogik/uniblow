#!/usr/bin/env bash

# Build uniblow Debian 10 binary package release


if ! (cat /etc/os-release | grep -E "10 \(buster\)" > /dev/null ) then
  echo "This Uniblow building script only runs on Debian 10."
  exit 1
fi

function is_installed {
  if [ $(dpkg-query -W -f='${Status}' $1 2>/dev/null | grep -c "ok installed") -eq 0 ]; then
      echo 'not'
    fi
}

softs_req=('libsdl2-2.0-0' 'python3-venv' 'python3-pip' 'python3-pyscard')

for softr in "${softs_req[@]}"; do
  if [ "$(is_installed $softr)" == 'not' ]; then
    echo ERROR :
    echo $softr needs to be installed
    echo run sudo apt -y install $softr 
    exit 1
  fi
done

rm -Rf dist

echo Initializing venv ...
python3 -m venv --system-site-packages unibenvi
source unibenvi/bin/activate

echo Installing pip dependencies ...
python -m pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/debian-10/wxPython-4.1.1-cp37-cp37m-linux_x86_64.whl wxPython < /dev/null
python -m pip install -U pip setuptools-rust < /dev/null

python setup.py install
python -m pip install pyinstaller==4.4

echo Building package ...
python -OO -m PyInstaller package/uniblow.spec
deactivate

echo Compilation done.
echo Binary result is in the dist folder.
