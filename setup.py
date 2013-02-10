#!/usr/bin/python3
#
# This file is part of OpenNumismat (http://code.google.com/p/open-numismat/).
#
# OpenNumismat is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# any later version.
#
# OpenNumismat is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenNumismat; If not, see <http://www.gnu.org/licenses/>.


###############################################################################
# DOCS
###############################################################################

"""**OpenNumismat** is an application for coins collectors and numismatists. You can create and manage your own catalogue with detailed description and photos of coins.

Main features:

- More than 60 customizable fields to describe the coin
- Up to 7 photos coins (insert image from file, clipboard, download from the Web at URL)
- The grouping, filters and sorting to facilitate the retrieval of coins in the catalog
- Generate and print reports, saving as HTML, PDF, MS Word
- Export customized lists as MS Excel, HTML and CSV
- Duplication of coins to quickly add a similar coin
- Batch edit coins
- Ability to add and customize the lists to display the required data
- Does not require additional software to work with a database
- Importing from CoinsCollector, Numizmat 2, Cabinet and CoinManage 2011, 2013, Collection Studio 3.65 (additional software may be required)
- Support languages (English, Russian, Spanish)
- Potential support for Linux and MacOS (from source code) 

OpenNumismat based on PyQt framework with SQLite database engine to store data collection.
"""


###############################################################################
# IMPORTS
###############################################################################

import os
import sys

from setuptools import setup, find_packages

from OpenNumismat import version

###############################################################################
# VALIDATE THE NEEDED MODULES
###############################################################################

# This modules can't be easy installed
# Syntax: [(module, url of the tutorial)...]
NEEDED_MODULES = [("PyQt4",
        "http://www.riverbankcomputing.co.uk/software/pyqt/intro"), ]
if sys.platform == 'win32':
    NEEDED_MODULES.append(('win32com',
            "http://sourceforge.net/projects/pywin32/files/pywin32/"))


for mn, urlm in NEEDED_MODULES:
    try:
        __import__(mn)
    except ImportError:
        print("Module '%s' not found. For more details: '%s'.\n" % (mn, urlm))
        sys.exit(1)


dependencies = ['lxml', 'jinja2']
if sys.platform == 'win32':
    dependencies.append("xlwt3")


data_files = []
for dirname, dirnames, filenames in os.walk('OpenNumismat/templates'):
    for filename in filenames:
        data_files.append((dirname,
                           [os.path.join(dirname, filename), ]))

###############################################################################
# PRE-SETUP
###############################################################################

# Common
params = {
    "name": version.AppName,
    "version": version.Version,
    "author": "Vitaly Ignatov",
    "description": "An application for coins collectors and numismatists",
    "long_description": __doc__,
    "url": version.Web,
    "license": "GPLv3",
    "keywords": "numismatics, coins, qt, pyqt, collecting, cataloging",
    "classifiers": ["Development Status :: 5 - Production/Stable",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Natural Language :: English",
            "Natural Language :: Russian",
            "Natural Language :: Spanish",
            "Intended Audience :: End Users/Desktop",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3.2"],

    "install_requires": dependencies,

    # include all resources
    "include_package_data": True,
    "package_data": {'': ['*.png', '*.gif', '*.jpg', '*.ico',
        '*.js', '*.htm', '*.html', '*.css', '*.qm']},
    "data_files": data_files,

    "py_modules": ['open-numismat', ],

    "packages": find_packages() + [
        'OpenNumismat/icons'],

    # auto create scripts
    "entry_points": {
        'console_scripts': [
            'open-numismat = OpenNumismat:main',
        ],
        'gui_scripts': [
            'open-numismat = OpenNumismat:main',
        ]
    }
}


###############################################################################
# SETUP
###############################################################################

setup(**params)


###############################################################################
# MAIN
###############################################################################

if __name__ == '__main__':
    print("Setup for OpenNumismat")
