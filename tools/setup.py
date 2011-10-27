import sys

from cx_Freeze import Executable, Freezer

sys.path.append('../src')
import version

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [Executable("../src/main.py", base=base, targetName=version.AppName+".exe")]
freezer = Freezer(executables,
            includes = ["lxml._elementpath", "gzip", "inspect"],
            excludes = ["win32api", "win32pipe", "win32con"],
            compress = True,
            base = base)
freezer.Freeze()
