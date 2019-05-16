#!/usr/bin/env python3
#
# This file is part of OpenNumismat (http://opennumismat.github.io/).
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

"""**OpenNumismat** is a handy and reliable application aimed at coin lovers,
numismatists or amateurs looking to create a numismatics collection.

With **OpenNumismat**, you will be able to create, organize and manage your own
coin catalogue with detailed description and photos for each of the items.

Main features:

- More than 60 customizable fields to describe the coin
- Up to 7 photos coins (insert image from file, clipboard, download from the
  Web at URL)
- The grouping, filters and sorting to facilitate the retrieval of coins in the
  catalog
- Generate and print reports, saving as HTML, PDF, MS Word
- Export customized lists as MS Excel, HTML and CSV
- Duplication of coins to quickly add a similar coin
- Batch edit coins
- Ability to add and customize the lists to display the required data
- Does not require additional software to work with a database
- Importing from Cabinet, CoinManage 2011, 2013, 2015, Collection Studio,
  Tellico (additional software may be required), uCoin.net
- Support languages: English, Russian, Ukrainian, Spanish, French, Hungarian,
  Portuguese, German, Greek, Czech, Italian, Polish, Catalan, Dutch, Bulgarian,
  Latvian
- Cross-platform: Windows, Linux, MacOS X

.. image:: http://opennumismat.github.io/images/screenMain.png

OpenNumismat based on PyQt framework with SQLite database engine to store data
collection.
"""


###############################################################################
# IMPORTS
###############################################################################

import os
import shutil
import sys

from setuptools import find_packages

try:
    from cx_Freeze import setup, Executable
    cx_Freeze_available = True
except ImportError:
    from setuptools import setup
    cx_Freeze_available = False

###############################################################################
# VALIDATE THE NEEDED MODULES
###############################################################################

# This modules can't be easy installed
# Syntax: [(module, url of the tutorial)...]
NEEDED_MODULES = [("PyQt5",
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

dependencies = ['lxml', 'jinja2', 'matplotlib', 'numpy', 'xlrd', 'python-dateutil']
if sys.platform == 'win32' or sys.platform == "darwin":
    dependencies.append("xlwt")


# data_files = []
# for dirname, dirnames, filenames in os.walk('OpenNumismat/templates'):
#    for filename in filenames:
#        data_files.append((dirname,
#                           [os.path.join(dirname, filename), ]))

templates_packages = []
for dirname, dirnames, filenames in os.walk('OpenNumismat/templates'):
    if filenames:
        templates_packages.append(dirname)

###############################################################################
# PRE-SETUP
###############################################################################

# Common
params = {
    "name": 'OpenNumismat',
    "version": '1.8.2',
    "author": 'Vitaly Ignatov',
    "author_email": 'opennumismat@gmail.com',
    "description": 'OpenNumismat',
    "long_description": __doc__,
    "url": 'http://opennumismat.github.io/',
    "license": "GPLv3",
    "keywords": "numismatics, coins, qt, pyqt, collecting, cataloging",
    "classifiers": ["Development Status :: 5 - Production/Stable",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Natural Language :: English",
            "Natural Language :: Russian",
            "Natural Language :: Spanish",
            "Natural Language :: Ukranian",
            "Natural Language :: Hungarian",
            "Natural Language :: Portuguese",
            "Natural Language :: French",
            "Natural Language :: German",
            "Natural Language :: Greek",
            "Natural Language :: Czech",
            "Natural Language :: Italian",
            "Natural Language :: Polish",
            "Natural Language :: Catalan",
            "Natural Language :: Dutch",
            "Natural Language :: Bulgarian",
            "Natural Language :: Latvian",
            "Intended Audience :: End Users/Desktop",
            "Operating System :: OS Independent",
            "Operating System :: POSIX :: Linux",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: MacOS :: MacOS X",
            "Environment :: X11 Applications :: Qt",
            "Environment :: Win32 (MS Windows)",
            "Environment :: MacOS X",
            "Programming Language :: Python :: 3.4"],

    "install_requires": dependencies,

    # include all resources
    "include_package_data": True,
    "package_data": {'': ['*.png', '*.gif', '*.jpg', '*.ico',
        '*.js', '*.htm', '*.html', '*.css', '*.qm', '*.db', '*.ref',
        '*.mplstyle']},
#    "data_files": data_files,

    "py_modules": ['open-numismat', ],

    "packages": find_packages() + [
        'OpenNumismat/icons',
        'OpenNumismat/db'] +
          templates_packages,

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

if cx_Freeze_available:
    import PyQt5

    base = None
    if sys.platform == "win32":
        base = "Win32GUI"

    if sys.platform == "win32":
        qt_dir = PyQt5.__path__[0]
        executable_ext = '.exe'
    else:
        # Path to Qt on MacPorts
        qt_dir = '/opt/local/libexec/qt5'
        executable_ext = ''

    executable = Executable("open-numismat.py", base=base,
                            icon='OpenNumismat/icons/main.ico',
                            targetName=params['name'] + executable_ext)

    translation_files = []
    f = open('tools/langs')
    langs = [x.strip('\n') for x in f.readlines()]

    for lang in langs:
        if lang == 'en':
            continue

        translation_files.append(("OpenNumismat/lang_%s.qm" % lang,
                                  "lang_%s.qm" % lang))
        if os.path.isfile("OpenNumismat/qtbase_%s.qm" % lang):
            translation_files.append(("OpenNumismat/qtbase_%s.qm" % lang,
                                  "qtbase_%s.qm" % lang))
    include_files = translation_files + [
            "COPYING",
            ("OpenNumismat/icons", "icons"),
            ("OpenNumismat/templates", "templates"),
            ("OpenNumismat/db", "db"),
            (qt_dir + "/plugins/imageformats", "imageformats"),
            ("OpenNumismat/opennumismat.mplstyle", "opennumismat.mplstyle"),
        ]
    if sys.platform == "win32":
        include_files.append(
                (qt_dir + "/plugins/sqldrivers/qsqlite.dll", "sqldrivers/qsqlite.dll"))
    elif sys.platform == "darwin":
        include_files.append(
                (qt_dir + "/plugins/sqldrivers/libqsqlite.dylib", "sqldrivers/libqsqlite.dylib"))

        include_files.append(("/opt/local/lib/libsqlite3.0.dylib", "libsqlite3.0.dylib"))
        include_files.append(("/opt/local/lib/libjpeg.9.dylib", "libjpeg.9.dylib"))
        include_files.append(("/opt/local/lib/libmng.2.dylib", "libmng.2.dylib"))
        include_files.append(("/opt/local/lib/libtiff.5.dylib", "libtiff.5.dylib"))
        include_files.append(("/opt/local/lib/liblcms2.dylib", "liblcms2.dylib"))
    build_exe_options = {
            "excludes": [],
            "includes": ["lxml._elementpath", "gzip", "inspect", "PyQt5.QtNetwork",
                         "PyQt5.QtWebKit", "numpy.core._methods", "numpy.lib.format",
                         "matplotlib.backends.backend_ps", "matplotlib.backends.backend_pdf",
                         "matplotlib.backends.backend_svg"],
            "include_files": include_files,
            "replace_paths": [(os.path.dirname(__file__) + os.sep, '')],
            "include_msvcr": True  # skip error msvcr100.dll missing
    }
    if sys.platform == "darwin":
        build_exe_options["packages"] = ["xlwt", "asyncio"]

    params["executables"] = [executable]
    params["options"] = {"build_exe": build_exe_options,
                         "bdist_mac": {"iconfile": "OpenNumismat.icns"}}


###############################################################################
# SETUP
###############################################################################

setup(**params)

if sys.platform == "win32":
    binDir = 'build/exe.win32-3.4/'
    shutil.rmtree(binDir + "mpl-data/sample_data")
    shutil.rmtree(binDir + "mpl-data/images")
    shutil.rmtree(binDir + "mpl-data/fonts")

# Post bdist_mac
if sys.platform == "darwin":
    bundleName = params['name'] + '-' + params['version'] + '.app'
    binDir = 'build/' + bundleName + '/Contents/MacOS/'
    shutil.copy("qt.conf", binDir)
    shutil.copy("OpenNumismat.icns", "build/" + bundleName + "/Contents/Resources")

###############################################################################
# MAIN
###############################################################################

if __name__ == '__main__':
    print("Setup for OpenNumismat")
