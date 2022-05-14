
import sys
import os.path
from webbrowser import open as wopen


def file_path(fpath):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, fpath)
    return fpath


def show_history(history_url):
    wopen(history_url, new=1, autoraise=True)
