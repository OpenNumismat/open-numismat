# -*- mode: python ; coding: utf-8 -*-

import PyInstaller.config
PyInstaller.config.CONF['distpath'] = "./dist/OpenNumismat"

block_cipher = None

a = Analysis(
    ['open-numismat-portable.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OpenNumismat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='icons/main.ico',
    version='file_version_info.txt',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


import os
import shutil

from OpenNumismat.version import Version, AppName


shutil.copytree('OpenNumismat/db', 'dist/OpenNumismat/db')
shutil.copytree('OpenNumismat/templates', 'dist/OpenNumismat/templates')
shutil.copytree('OpenNumismat/translations', 'dist/OpenNumismat/translations')
shutil.copy('COPYING', 'dist/OpenNumismat/COPYING')

if os.path.exists(AppName + '-' + Version + '.zip'):
    os.remove(AppName + '-' + Version + '.zip')
shutil.make_archive(AppName + '-' + Version, 'zip', 'dist/')
