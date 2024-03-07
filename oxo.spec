# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/home/azouiten/ostorlab/src/ostorlab/main.py'],
    pathex=[],
    binaries=[],
    datas=[('/home/azouiten/ostorlab/*', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["docker", "alembic"],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='oxo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
