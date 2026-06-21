# -*- mode: python ; coding: utf-8 -*-
import os
import sys

a = Analysis(
    ['C:\\Users\\13122\\Desktop\\bofang\\math\\main.py'],
    pathex=[],
    binaries=[],
    datas=[(os.path.join(os.getcwd(), 'resources'), 'resources')],
    hiddenimports=['pygame', 'pygame_gui'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MathSimulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_excludes=[],
    name='MathSimulator',
)
