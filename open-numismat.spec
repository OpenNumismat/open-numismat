# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

include_files = [
            ("COPYING", "."),
            ("OpenNumismat/icons", "icons"),
            ("OpenNumismat/translations", "translations"),
            ("OpenNumismat/templates", "templates"),
            ("OpenNumismat/db", "db"),
            ("OpenNumismat/opennumismat.mplstyle", "."),
        ]

a = Analysis(['open-numismat.py'],
             pathex=['d:\\OpenNumismat\\open-numismat'],
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
          icon='OpenNumismat/icons/main.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='OpenNumismat')

import shutil

binDir = "dist/OpenNumismat/mpl-data/"
shutil.rmtree(binDir + "fonts")
shutil.rmtree(binDir + "images")
shutil.rmtree(binDir + "sample_data")
shutil.rmtree(binDir + "stylelib")
binDir = "dist/OpenNumismat/PyQt5/Qt/"
shutil.rmtree(binDir + "qml")
shutil.rmtree(binDir + "translations")
binDir = "dist/OpenNumismat/PyQt5/Qt/plugins/"
shutil.rmtree(binDir + "audio")
shutil.rmtree(binDir + "bearer")
shutil.rmtree(binDir + "mediaservice")
shutil.rmtree(binDir + "playlistformats")
shutil.rmtree(binDir + "position")
shutil.rmtree(binDir + "sensorgestures")
shutil.rmtree(binDir + "sensors")

from pathlib import Path
for p in Path("dist/OpenNumismat/").glob("api-ms-win-*.dll"):
    p.unlink()
for p in Path("dist/OpenNumismat/").glob("Qt5Quick3D*.dll"):
    p.unlink()

import os
for f in ("opengl32sw.dll", "Qt5Bluetooth.dll", "Qt5DBus.dll", "Qt5Designer.dll",
          "Qt5Location.dll", "Qt5Multimedia.dll", "Qt5MultimediaWidgets.dll", "Qt5Network.dll",
          "Qt5Nfc.dll", "Qt5OpenGL.dll", "Qt5QuickParticles.dll", "Qt5QuickTemplates2.dll",
          "Qt5QmlWorkerScript.dll"
          ):
    f = "dist/OpenNumismat/" + f
    os.remove(f)

for f in ("QtBluetooth.pyd", "QtDBus.pyd", "QtDesigner.pyd",
          "QtLocation.pyd", "QtMultimedia.pyd", "QtMultimediaWidgets.pyd", "QtNetwork.pyd",
          "QtNfc.pyd", "QtOpenGL.pyd", "QtPositioning.pyd",
          "QtQml.pyd", "QtQuick.pyd", "QtQuick3D.pyd", "QtQuickWidgets.pyd"):
    f = "dist/OpenNumismat/PyQt5/" + f
    os.remove(f)
