# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

include_files = [
            ("COPYING", "."),
            ("OpenNumismat/translations", "translations"),
            ("OpenNumismat/templates", "templates"),
            ("OpenNumismat/db", "db"),
            ("OpenNumismat/opennumismat.mplstyle", "."),
        ]

a = Analysis(['open-numismat.py'],
             pathex=[],
             binaries=[],
             datas=include_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='OpenNumismat',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon='icons/main.ico',
          version='file_version_info.txt')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='OpenNumismat')
app = BUNDLE(coll,
         name='OpenNumismat.app',
         icon='OpenNumismat.icns',
         version='1.8.17',
         info_plist={'NSPrincipalClass': 'NSApplication'},
         bundle_identifier=None)


import os
import shutil
import sys

WIN32 = sys.platform == "win32"
DARWIN = sys.platform == "darwin"

if WIN32:
    bin_dir = "dist/OpenNumismat/"
    pyd_ext = ".pyd"
else:
    bin_dir = "dist/OpenNumismat.app/Contents/MacOS/"
    pyd_ext = ".abi3.so"

for sub_folder in ("fonts", "images", "sample_data", "stylelib"):
    shutil.rmtree(bin_dir + "matplotlib/mpl-data/" + sub_folder)
for sub_folder in ("qml", "translations"):
    shutil.rmtree(bin_dir + "PyQt5/Qt5/" + sub_folder)
for sub_folder in ("audio", "bearer", "geoservices", "mediaservice",
                "playlistformats", "position", "sensorgestures", "sensors"):
    shutil.rmtree(bin_dir + "PyQt5/Qt5/plugins/" + sub_folder, ignore_errors=True)

for f in ("QtBluetooth", "QtDBus", "QtDesigner",
          "QtLocation", "QtMultimedia", "QtMultimediaWidgets",
          "QtNfc", "QtOpenGL", "QtPositioning",
          "QtQml", "QtQuick", "QtQuick3D", "QtQuickWidgets"):
    try:
        os.remove(bin_dir + "PyQt5/" + f + pyd_ext)
    except OSError:
        pass

if WIN32:
    for f in ("opengl32sw.dll", "Qt5Bluetooth.dll", "Qt5DBus.dll", "Qt5Designer.dll",
              "Qt5Location.dll", "Qt5Multimedia.dll", "Qt5MultimediaWidgets.dll",
              "Qt5Nfc.dll", "Qt5OpenGL.dll", "Qt5QuickParticles.dll", "Qt5QuickTemplates2.dll",
              "Qt5QmlWorkerScript.dll", "Qt5Quick3D.dll", "Qt5Quick3DAssetImport.dll",
              "Qt5Quick3DRender.dll", "Qt5Quick3DRuntimeRender.dll", "Qt5Quick3DUtils.dll"
              ):
        try:
            os.remove(bin_dir + f)
        except OSError:
            pass
else:
    for f in ("QtBluetooth", "QtDesigner",
              "QtLocation", "QtMultimedia", "QtMultimediaWidgets",
              "QtNfc", "QtOpenGL", "QtQuickParticles", "QtQuickTemplates2",
              "QtQmlWorkerScript", "QtQuick3D", "QtQuick3DAssetImport",
              "QtQuick3DRender", "QtQuick3DRuntimeRender", "QtQuick3DUtils"
              ):
        os.remove(bin_dir + f)
