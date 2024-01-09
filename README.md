[![CodeFactor](https://www.codefactor.io/repository/github/opennumismat/open-numismat/badge)](https://www.codefactor.io/repository/github/opennumismat/open-numismat)
[![GitHub release](https://img.shields.io/github/release/opennumismat/open-numismat.svg)](https://github.com/opennumismat/open-numismat/releases/)
[![GitHub all releases](https://img.shields.io/github/downloads/opennumismat/open-numismat/total.svg)](https://hanadigital.github.io/grev/?user=OpenNumismat&repo=open-numismat)
[![GitHub release (latest by date)](https://img.shields.io/github/downloads/opennumismat/open-numismat/latest/total.svg)](https://hanadigital.github.io/grev/?user=OpenNumismat&repo=open-numismat)
![GitHub commits since latest release (by date)](https://img.shields.io/github/commits-since/OpenNumismat/open-numismat/latest)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/OpenNumismat/open-numismat)
[![GitHub license](https://img.shields.io/github/license/opennumismat/open-numismat.svg)](https://github.com/opennumismat/open-numismat/blob/master/COPYING)
[![Latest build](https://github.com/OpenNumismat/ImageEditor/actions/workflows/snapshot.yml/badge.svg)](https://github.com/OpenNumismat/open-numismat/releases/tag/latest)


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
* Python 3.11.6
* PySide6 6.5.3
* Jinja2 3.1.2 (for reports)
* openpyxl 3.1.2 (for import/export to Excel)
* pywin32-306 (for saving report as Word Document)
* lxml 4.9.3 (for importing from Tellico, Collection Studio and ANS)
* python-dateutil 2.8.2 (for importing from Excel)
* pyinstaller 6.1.0 (for deploy)
* Inno Setup 6.2.1 (for deploy)

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
    pip3 install pyinstaller
    SET PYTHONOPTIMIZE=1
    pyinstaller --clean --noconfirm open-numismat-portable.spec

#### For macOS
    pyinstaller --clean --noconfirm open-numismat.spec
    cd dist
    mkdir vol
    VERSION=$(grep Version ../OpenNumismat/version.py | grep -o -E "\d+.\d+.\d+")
    mv OpenNumismat.app vol
    ln -s /Applications vol/Applications
    hdiutil create OpenNumismat-$VERSION-macos11.dmg -volname "OpenNumismat-$VERSION" -srcfolder vol -fs HFSX -format UDZO -imagekey zlib-level=9

#### For Linux
    sudo apt install dpkg devscripts debhelper dh-python dh-virtualenv
    debuild -b -us -uc
