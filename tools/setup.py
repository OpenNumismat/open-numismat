import os, shutil, sys
from cx_Freeze import Executable, Freezer

sys.path.append('../src')
import version

if os.path.exists("dist"):
    shutil.rmtree("dist")

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [Executable("../src/main.py", targetName=version.AppName+".exe")]
freezer = Freezer(executables,
    includes = ["lxml._elementpath", "gzip", "inspect"],
    excludes = ["win32api", "win32pipe", "win32con"],
    compress = True,
    replacePaths = [('..\\src\\', '')],
    icon = '../src/icons/main.ico',
    base = base)
freezer.Freeze()

shutil.copytree("../src/icons", "dist/icons")
shutil.copy("../COPYING", "dist")
shutil.copy("lang_ru.qm", "dist")
import PyQt4
shutil.copytree(PyQt4.__path__[0]+"/plugins/imageformats", "dist/imageformats")
os.mkdir("dist/sqldrivers")
shutil.copy(PyQt4.__path__[0]+"/plugins/sqldrivers/qsqlite4.dll", "dist/sqldrivers")
shutil.copy(PyQt4.__path__[0]+"/translations/qt_ru.qm", "dist")
