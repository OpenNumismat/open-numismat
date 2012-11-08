Requirement:
 * Python 3.2.3
 * PyQt 4.9.5
 * lxml 2.3 (for auction parsing and importing from CoinsCollector 2.6)
 * Firebird 2.0 (for importing from Numizmat 2.1)
 * nakagami/pyfirebirdsql 0.7.0 (for importing from Numizmat 2.1)
 * pyodbc 3.0.2 (for importing from Cabinet 2.0.2.0, 2011 and CoinManage 2011)
 * DBISAM ODBC-TRIAL 4.3 (for importing from Cabinet 2.0.2.0, 2011)
 * Visual FoxPro ODBC Driver, Microsoft Access Database Engine, Microsoft Access or any other
   software with ODBC {Microsoft Access Driver (*.mdb)} (for importing from CoinManage 2011)
 * cx_Freeze 4.3 (for deploy)
 * Inno Setup 5.5.2 (for deploy)
 * Delphi Delphi XE2 (for building CdrToXml.dll for importing from CoinsCollector 2.6)

Deploying:
Run `python i18n.py` and fill translations
Run `python setup.py`
Compile setup*.iss with Inno Setup
