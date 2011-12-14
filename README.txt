Requirement:
 * Python 3.2
 * PyQt 4.8.6
 * lxml 2.3 (for auction parsing and importing from CoinsCollector 2.6)
 * Firebird 2.0 (for importing from Numizmat 2.1)
 * nakagami/pyfirebirdsql 0.6.4 (for importing from Numizmat 2.1)
 * pyodbc 3.0.1 (for importing from Cabinet 2.0.2.0, 2011)
 * DBISAM ODBC-TRIAL 4.3 (for importing from Cabinet 2.0.2.0, 2011)
 * cx_Freeze 4.2.3 (for deploy)
 * pywin32 216 (for deploy)
 * Inno Setup 5.4.2 (for deploy)
 * Delphi Delphi XE2 (for building CdrToXml.dll for importing from CoinsCollector 2.6)

Deploying:
Run `python i18n.py` and fill translations
Run `python setup.py`
Compile setup*.iss with Inno Setup
