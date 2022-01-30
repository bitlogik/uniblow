#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Uniblow : setup data
# Copyright (C) 2021  BitLogiK


from setuptools import setup, find_packages
from version import VERSION

with open("README.md") as readme_file:
    readme = readme_file.read()


setup(
    name="Uniblow",
    version=VERSION,
    description="a UNiversal BLOckchain Wallet",
    long_description=readme + "\n\n",
    long_description_content_type="text/markdown",
    keywords="blockchain wallet bitcoin cryptography security",
    author="BitLogiK",
    author_email="contact@bitlogik.fr",
    url="https://github.com/bitlogik/uniblow",
    license="GPLv3",
    python_requires=">=3.6",
    install_requires=[
        "wxPython==4.1.1",
        "cryptography>=3.3",
        "pysha3==1.0.2",
        "qrcode==6.1",
        "PyNaCl==1.5.0",
        "pyweb3==0.1.3",
        "OpenPGPpy==0.4",
        "hidapi==0.11.0.post2",
        "pyWalletConnect==1.1.4",
    ],
    package_data={
        "gui": [
            "uniblow.ico",
            "good.bmp",
            "bad.bmp",
            "GenSeed.png",
            "GenSeeddn.png",
            "copy.png",
            "copydn.png",
            "histo.png",
            "histodn.png",
            "SeekAssets.png",
            "SeekAssetsdn.png",
            "send.png",
            "senddn.png",
            "swipe.png",
            "swipedn.png",
        ]
    },
    include_package_data=False,
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Office/Business :: Financial",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(),
    zip_safe=False,
)
