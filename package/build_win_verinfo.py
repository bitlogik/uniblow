# -*- coding: utf8 -*-

# UNIBLOW  :  Build Windows FileInfo parameters
# Copyright (C) 2021-2022 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


import datetime


def get_win32_filetime():
    diff = datetime.datetime.now() - datetime.datetime(1601, 1, 1)
    return int((diff / datetime.timedelta(microseconds=1)) * 10)


def int_to_32bpair(integ):
    return (integ >> 32, integ & 0xFFFFFFFF)


def now_time_filetime():
    return int_to_32bpair(get_win32_filetime())


def ver_str_to_comma(verstr):
    return ", ".join(verstr.split("."))


def fill_version_info(file_name, version_str, file_desc, comment):
    with open("package/version_info_form", "r", encoding="utf-8") as fverinfoform:
        versioninfo_content = fverinfoform.read()
    ver_commas = ver_str_to_comma(version_str)
    year = datetime.datetime.today().year
    versioninfo_new = versioninfo_content.format(
        version_str,
        ver_commas,
        year,
        file_desc,
        comment,
        now_time_filetime(),
        file_name,
    )
    with open("package/version_info", "w", encoding="utf-8") as fverinfo:
        fverinfo.write(versioninfo_new)
