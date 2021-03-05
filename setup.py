#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Uniblow : setup data
# Copyright (C) 2021  BitLogiK

from setuptools import setup, find_packages
from pip._internal import main as pipmain
from version import VERSION

with open("README.md") as readme_file:
    readme = readme_file.read()


pipmain(["install", "https://github.com/eosnewyork/eospy/archive/master.zip"])

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
        "cryptography==3.4.6",
        "ecdsa==0.16.1",
        "pysha3==1.0.2",
        "qrcode==6.1",
        "PyNaCl==1.4.0",
    ],
    package_data={"gui": ["uniblow.ico"]},
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
