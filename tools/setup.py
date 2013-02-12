import os, shutil, sys
from cx_Freeze import Executable, Freezer

sys.path.append('..')
from OpenNumismat import version

if os.path.exists("dist"):
    shutil.rmtree("dist")

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [Executable("../open-numismat.py", targetName=version.AppName + ".exe")]
freezer = Freezer(executables,
    includes=["lxml._elementpath", "gzip", "inspect", "PyQt4.QtNetwork"],
    excludes=["unittest"],
    compress=True,
    replacePaths=[('..\\OpenNumismat\\', '')],
    icon='../OpenNumismat/icons/main.ico',
    base=base)
freezer.Freeze()

shutil.copy("../OpenNumismat/Collection/Import/CdrToXml/Cdr2Xml.dll", "dist")
shutil.copytree("../OpenNumismat/icons", "dist/icons")
shutil.copytree("../OpenNumismat/templates", "dist/templates")
shutil.copytree("../OpenNumismat/db", "dist/db")
shutil.copy("../COPYING", "dist")
shutil.copy("../OpenNumismat/lang_ru.qm", "dist")
shutil.copy("../OpenNumismat/lang_es.qm", "dist")
import PyQt4
shutil.copytree(PyQt4.__path__[0] + "/plugins/imageformats", "dist/imageformats")
os.mkdir("dist/sqldrivers")
shutil.copy(PyQt4.__path__[0] + "/plugins/sqldrivers/qsqlite4.dll", "dist/sqldrivers")
shutil.copy(PyQt4.__path__[0] + "/translations/qt_ru.qm", "dist")
shutil.copy(PyQt4.__path__[0] + "/translations/qt_es.qm", "dist")
