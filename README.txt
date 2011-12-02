Requirement:
 * Python 3.2
 * PyQt 4.8.6
 * lxml 2.3 (for auction parsing)
 * pyodbc 3.0.1 (for importing)
 * Firebird 2.1 (for importing from Numizmat 2.1)
 * Firebird ODBC Driver 2.0 (for importing from Numizmat 2.1)
 * cx_Freeze 4.2.3 (for deploy)
 * pywin32 216 (for deploy)
 * Inno Setup 5.4.2 (for deploy)

Deploying:
Run `python i18n.py` and fill translations
Run `python setup.py`
Compile setup*.iss with Inno Setup
