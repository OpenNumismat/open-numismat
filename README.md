# open-numismat
OpenNumismat, is intended primarily for registering a collection of coins. But it is also suitable for other types of collectibles - stamps, postcards, badges and more exotic things.

The application is written in Python, data is stored using a SQLite database, PyQt is used for the interface, data access and much more, Jinja2 is used for generating reports, and Matplotlib is used to build statistics graphs. Despite my initial skepticism, this was enough to ensure acceptable performance — several thousand image records are processed without any noticeable brakes.
Since all components are cross-platform, then OpenNumismat has builds for Windows, Linux (Debian / Ubuntu), macOS.
# Requirement

| Name | For |
| ------ | ------ |
| Python 3.4.4 |  |
| PyQt5 5.5.1 |  |
| Jinja2 2.10 | reports |
| Matplotlib 2.1.0 | statistics |
| xlwt-future 0.8.0 | exporting to Excel |
| pywin32-219 | saving report as Word Document |
| lxml 3.4.1 | importing from CoinsCollector 2.6 and Tellico |
| xlrd 1.1.0 | importing from Excel |
| python-dateutil 2.6.1 | importing from Excel |
| Firebird 2.0 | importing from Numizmat 2.1 |
| pyfirebirdsql 0.9.12 | importing from Numizmat 2.1
| pyodbc 3.0.10 | importing from Cabinet 2.0.2.0, 2011 and CoinManage 2011 |
| DBISAM ODBC-TRIAL 4.3 | importing from Cabinet 2.0.2.0, 2011 |
| Visual FoxPro ODBC Driver, Microsoft Access Database Engine, Microsoft Access or any other
   software with ODBC {Microsoft Access Driver (*.mdb)} | importing from CoinManage 2011 |
| cx_Freeze 4.3.4 | deploy |
| Inno Setup 5.5.9 | deploy |
| Delphi Delphi XE2 | building CdrToXml.dll, importing from CoinsCollector 2.6 |

### Deploying

Run:
```sh
$ python setup.py build_exe
```
And compile setup*.iss with Inno Setup
