Requirement:
 * Python 3.2
 * PyQt 4.8.4
 * lxml 2.3 (for auction parsing)
 * cx_Freeze 4.2.3 (for deploy)
 * pywin32 216 (for deploy)

Deploying:
Run `python setup.py build`
Copy:
 * <project>/src/icons to build/<platform>/icons
 * <>/Python32/Lib/site-packages/PyQt4/plugins/imageformats to build/<platform>/imageformats
 * <>/Python32/Lib/site-packages/PyQt4/plugins/sqldrivers/qsqlite4.dll to build/<platform>/sqldrivers/qsqlite4.dll
