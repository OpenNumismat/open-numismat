# OpenNumismat
OpenNumismat is a desktop application for coin collecting.

## Requirements
 * Python 3.4.4
 * PyQt5 5.5.1
 * Jinja2 2.10 (for reports)
 * Matplotlib 2.1.0 (for statistics)
 * xlwt-future 0.8.0 (for exporting to Excel)
 * pywin32-219 (for saving report as Word Document)
 * lxml 3.4.1 (for importing from Tellico)
 * xlrd 1.1.0 (for importing from Excel)
 * python-dateutil 2.6.1 (for importing from Excel)
 * pyodbc 3.0.10 (for importing from Cabinet 2.0.2.0, 2011 and CoinManage 2011)
 * DBISAM ODBC-TRIAL 4.3 (for importing from Cabinet 2.0.2.0, 2011)
 * Visual FoxPro ODBC Driver, Microsoft Access Database Engine, Microsoft Access or any other
   software with ODBC {Microsoft Access Driver (*.mdb)} (for importing from CoinManage 2011)
 * cx_Freeze 4.3.4 (for deploy)
 * Inno Setup 5.6.1 (for deploy)

Note: For the ODBC driver mentioned above for CoinManage, [this one](https://www.microsoft.com/en-us/download/details.aspx?id=13255) works well.

These requirements can be installed like so:

    pip install -r requirements.txt

## Development
To run it after installing requirements, just do:

    python open-numismat.py

## Deploying

    python setup.py build_exe

Compile setup*.iss with Inno Setup
