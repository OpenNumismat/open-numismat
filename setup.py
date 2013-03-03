#!/usr/bin/env python3
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
- Importing from CoinsCollector, Numizmat 2, Cabinet, CoinManage 2011, 2013
  and Collection Studio 3.65 (additional software may be required)
- Support languages (English, Russian, Ukrainian, Spanish)
- Cross-platform: Windows, Linux. Potential support for MacOS (from source
  code)

OpenNumismat based on PyQt framework with SQLite database engine to store data
collection.
"""


###############################################################################
# IMPORTS
###############################################################################

import os
import sys

from setuptools import find_packages

try:
    from cx_Freeze import setup, Executable
    cx_Freeze_available = True
except ImportError:
    from setuptools import setup
    cx_Freeze_available = False

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
    "name": version.AppName,
    "version": version.Version,
    "author": version.Author,
    "author_email": version.EMail,
    "description": "Coin collecting software for organize and manage your own "
                   "catalogue",
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
        '*.js', '*.htm', '*.html', '*.css', '*.qm', '*.db', '*.ref']},
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
    import PyQt4

    base = None
    if sys.platform == "win32":
        base = "Win32GUI"

    if sys.platform == "win32":
        qt_dir = PyQt4.__path__[0]
        executable_ext = '.exe'
    else:
        # Path to Qt on MacPorts
        qt_dir = '/opt/local/share/qt4'
        executable_ext = ''

    executable = Executable("open-numismat.py", base=base, compress=True,
                            icon='OpenNumismat/icons/main.ico',
                            targetName=version.AppName + executable_ext)

    translation_files = []
    for translation in ['ru', 'uk', 'es']:
        translation_files.append(("OpenNumismat/lang_%s.qm" % translation,
                                  "lang_%s.qm" % translation))
        translation_files.append(("OpenNumismat/qt_%s.qm" % translation,
                                  "qt_%s.qm" % translation))
    include_files = translation_files + [
            "COPYING",
            ("OpenNumismat/icons", "icons"),
            ("OpenNumismat/templates", "templates"),
            ("OpenNumismat/db", "db"),
            (qt_dir + "/plugins/imageformats", "imageformats")
        ]
    if sys.platform == "win32":
        include_files.append(
                ("OpenNumismat/Collection/Import/CdrToXml/Cdr2Xml.dll", "Cdr2Xml.dll"))
        include_files.append(
                (qt_dir + "/plugins/sqldrivers/qsqlite4.dll", "sqldrivers/qsqlite4.dll"))
    else:
        include_files.append(
                (qt_dir + "/plugins/sqldrivers/libqsqlite.dylib", "sqldrivers/libqsqlite.dylib"))

        include_files.append(("/opt/local/lib/libsqlite3.0.dylib", "libsqlite3.0.dylib"))
        include_files.append(("/opt/local/lib/libjpeg.9.dylib", "libjpeg.9.dylib"))
        include_files.append(("/opt/local/lib/libmng.1.dylib", "libmng.1.dylib"))
        include_files.append(("/opt/local/lib/libtiff.5.dylib", "libtiff.5.dylib"))
    build_exe_options = {
            "excludes": ["unittest"],
            "includes": ["lxml._elementpath", "gzip", "inspect", "PyQt4.QtNetwork"],
            "include_files": include_files,
            "replace_paths": [(os.path.dirname(__file__) + os.sep, '')]
    }

    params["executables"] = [executable]
    params["options"] = {"build_exe": build_exe_options,
                         "bdist_mac": {"bundle_iconfile": "OpenNumismat.icns"}}


###############################################################################
# SETUP
###############################################################################

setup(**params)

# Post bdist_mac
if sys.platform == "darwin":
    import shutil

    bundleName = version.AppName + '-' + version.Version + '.app'
    binDir = 'build/' + bundleName + '/Contents/MacOS/'
    shutil.copy("OpenNumismat.icns", "build/" + bundleName + "/Contents/Resources")
    os.remove(binDir + "imageformats/libqsvg.dylib")

    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtCore.framework/Versions/4/QtCore",
            "@executable_path/QtCore",
            binDir + "sqldrivers/libqsqlite.dylib"]))
    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtSql.framework/Versions/4/QtSql",
            "@executable_path/QtSql",
            binDir + "sqldrivers/libqsqlite.dylib"]))
    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/lib/libsqlite3.0.dylib",
            "@executable_path/libsqlite3.0.dylib",
            binDir + "sqldrivers/libqsqlite.dylib"]))

    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtCore.framework/Versions/4/QtCore",
            "@executable_path/QtCore",
            binDir + "imageformats/libqgif.dylib"]))
    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtGui.framework/Versions/4/QtGui",
            "@executable_path/QtGui",
            binDir + "imageformats/libqgif.dylib"]))

    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtCore.framework/Versions/4/QtCore",
            "@executable_path/QtCore",
            binDir + "imageformats/libqico.dylib"]))
    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtGui.framework/Versions/4/QtGui",
            "@executable_path/QtGui",
            binDir + "imageformats/libqico.dylib"]))

    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtCore.framework/Versions/4/QtCore",
            "@executable_path/QtCore",
            binDir + "imageformats/libqjpeg.dylib"]))
    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtGui.framework/Versions/4/QtGui",
            "@executable_path/QtGui",
            binDir + "imageformats/libqjpeg.dylib"]))
    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/lib/libjpeg.9.dylib",
            "@executable_path/libjpeg.9.dylib",
            binDir + "imageformats/libqjpeg.dylib"]))

    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtCore.framework/Versions/4/QtCore",
            "@executable_path/QtCore",
            binDir + "imageformats/libqmng.dylib"]))
    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtGui.framework/Versions/4/QtGui",
            "@executable_path/QtGui",
            binDir + "imageformats/libqmng.dylib"]))
    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/lib/libmng.1.dylib",
            "@executable_path/libmng.1.dylib",
            binDir + "imageformats/libqmng.dylib"]))

    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtCore.framework/Versions/4/QtCore",
            "@executable_path/QtCore",
            binDir + "imageformats/libqtga.dylib"]))
    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtGui.framework/Versions/4/QtGui",
            "@executable_path/QtGui",
            binDir + "imageformats/libqtga.dylib"]))

    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtCore.framework/Versions/4/QtCore",
            "@executable_path/QtCore",
            binDir + "imageformats/libqtiff.dylib"]))
    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/Library/Frameworks/QtGui.framework/Versions/4/QtGui",
            "@executable_path/QtGui",
            binDir + "imageformats/libqtiff.dylib"]))
    os.system(' '.join(["install_name_tool", "-change",
            "/opt/local/lib/libtiff.5.dylib",
            "@executable_path/libtiff.5.dylib",
            binDir + "imageformats/libqtiff.dylib"]))


###############################################################################
# MAIN
###############################################################################

if __name__ == '__main__':
    print("Setup for OpenNumismat")
