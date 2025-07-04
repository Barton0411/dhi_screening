# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[('config.yaml', '.'), ('rules.yaml', '.'), ('models.py', '.'), ('data_processor.py', '.'), ('requirements.txt', '.'), ('whg3r-qi1nv-001.ico', '.')],
    hiddenimports=['PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui', 'PyQt6.QtPrintSupport', 'yaml', 'openpyxl', 'openpyxl.workbook', 'openpyxl.worksheet', 'openpyxl.reader', 'openpyxl.writer', 'pandas', 'pandas.core', 'pandas.io', 'pandas.io.excel', 'xlrd', 'xlsxwriter', 'dateutil', 'dateutil.parser', 'logging.handlers', 'zipfile', 'tempfile', 'shutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'IPython', 'jupyter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DHI蛋白筛查系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['whg3r-qi1nv-001.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DHI蛋白筛查系统',
)
