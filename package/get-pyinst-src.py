

# Download PyInstaller source in pyinstaller-VERSION.zip
# python3 get-pyinst-src.py VERSION

import sys, urllib.request
pyinstver = sys.argv[1]
print(pyinstver)
url = f"https://github.com/pyinstaller/pyinstaller/archive/refs/tags/v{pyinstver}.zip"
urllib.request.urlretrieve(url, f"pyinstaller-{pyinstver}.zip")
