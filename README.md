# OpenNumismat
http://opennumismat.github.io/

OpenNumismat, is intended primarily for registering a collection of coins. But
it is also suitable for other types of collectibles - stamps, postcards, badges
and more exotic things.

Since all components are cross-platform, then OpenNumismat has builds for
Windows, Linux (Debian/Ubuntu), macOS.

## Requirements
Main Windows version based on:
 * Python 3.4.4
 * PyQt5 5.5.1
 * Jinja2 2.10 (for reports)
 * Matplotlib 2.1.0 (for statistics)
 * xlwt-future 0.8.0 (for exporting to Excel)
 * pywin32-219 (for saving report as Word Document)
 * lxml 3.4.1 (for importing from Tellico)
 * xlrd 1.1.0 (for importing from Excel)
 * python-dateutil 2.6.1 (for importing from Excel)
 * Visual FoxPro ODBC Driver, Microsoft Access Database Engine, Microsoft Access or any other
   software with ODBC {Microsoft Access Driver (*.mdb)} (for importing from CoinManage 2021)
 * cx_Freeze 4.3.4 (for deploy)
 * Inno Setup 5.6.1 (for deploy)

For running from source and development requirements can be installed like so:
    pip install -r requirements.txt

## Deploying
    python setup.py build_exe

Compile setup*.iss with Inno Setup
