import sys

from cx_Freeze import setup, Executable

sys.path.append('../src')
import version

base = None
if sys.platform == "win32":
    base = "Win32GUI"

buildOptions = dict(
        compressed = True,
        includes = ["lxml._elementpath", "gzip", "inspect"])

setup(
        name = version.AppName,
        version = version.Version,
		options = dict(build_exe = buildOptions),
        executables = [Executable("../src/main.py", base=base, targetName=version.AppName+".exe")])
