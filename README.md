[![CodeFactor](https://www.codefactor.io/repository/github/opennumismat/open-numismat/badge)](https://www.codefactor.io/repository/github/opennumismat/open-numismat)
[![GitHub release](https://img.shields.io/github/release/opennumismat/open-numismat.svg)](https://github.com/opennumismat/open-numismat/releases/)
[![GitHub all releases](https://img.shields.io/github/downloads/opennumismat/open-numismat/total.svg)](https://hanadigital.github.io/grev/?user=OpenNumismat&repo=open-numismat)
[![GitHub release (latest by date)](https://img.shields.io/github/downloads/opennumismat/open-numismat/latest/total.svg)](https://hanadigital.github.io/grev/?user=OpenNumismat&repo=open-numismat)
![GitHub commits since latest release (by date)](https://img.shields.io/github/commits-since/OpenNumismat/open-numismat/latest)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/OpenNumismat/open-numismat)
[![GitHub license](https://img.shields.io/github/license/opennumismat/open-numismat.svg)](https://github.com/opennumismat/open-numismat/blob/master/COPYING)


# OpenNumismat
http://opennumismat.github.io/

OpenNumismat, is intended primarily for registering a collection of coins. But
it is also suitable for other types of collectibles - stamps, postcards, badges
and more exotic things.

Since all components are cross-platform, then OpenNumismat has builds for
Windows, Linux (Debian/Ubuntu), macOS.

![Main window](http://opennumismat.github.io/images/screenMain.png)

## Requirements
Main Windows version based on:
* Python 3.11.3
* PySide6 6.5.0
* Jinja2 3.1.2 (for reports)
* openpyxl 3.1.2 (for import/export to Excel)
* pywin32-306 (for saving report as Word Document)
* lxml 4.9.2 (for importing from Tellico)
* python-dateutil 2.8.2 (for importing from Excel)
* pyinstaller 5.10.1 (for deploy)
* Inno Setup 6.2.1 (for deploy)

Debian/Ubuntu version depends on following packages: 
* python3
* python3-pyqt5
* python3-pyqt5.qtsql
* libqt5sql5-sqlite
* python3-pyqt5.qtwebkit
* python3-jinja2
* python3-matplotlib
* python3-numpy
* python3-lxml
* python3-xlrd
* python3-dateutil
* python3-xlwt (suggests)
* python3-pyqt5.webengine (suggests)

For running from source code and development requirements can be installed like so:
`pip3 install -r requirements.txt`

## Building
Befor building installation package may be necessary:
* compile translations file with: `python3 tools/build_resources.py`
* create `OpenNumismat/private_keys.py` with content: `MAPS_API_KEY = '<your Google API key>'`

#### For Windows
    pip3 install pyinstaller
    SET PYTHONOPTIMIZE=1
    pyinstaller --clean --noconfirm open-numismat.spec
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" tools\setup.iss

#### For Windows portable version
    pip3 install cx_Freeze
    SET PORTABLE=YES
    "C:\Python34\python.exe" setup.py build_exe

#### For macOS
    python3 setup.py bdist_mac
    cd build
    mkdir vol
    VERSION=$(grep Version ../OpenNumismat/version.py | grep -o -E "\d+.\d+.\d+")
    mv OpenNumismat-$VERSION.app vol/OpenNumismat.app
    ln -s /Applications vol/Applications
    hdiutil create OpenNumismat-$VERSION.dmg -volname "OpenNumismat-$VERSION" -srcfolder vol -fs HFS+ -size 500m -format UDZO

#### For Linux
    sudo apt-get install devscripts debhelper python3-setuptools dh-python
    debuild
