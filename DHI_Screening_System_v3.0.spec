# -*- mode: python ; coding: utf-8 -*-
# DHI筛查分析系统 v3.0 - PyInstaller配置文件
# 伊利液奶奶科院

# 应用信息
APP_NAME = 'DHI_Screening_System_v3.0'
APP_VERSION = '3.0'
APP_DESCRIPTION = '伊利液奶奶科院 - DHI数据分析与乳房炎监测系统'

# 分析配置
a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.yaml', '.'),
        ('rules.yaml', '.'), 
        ('whg3r-qi1nv-001.ico', '.'),
        ('README.md', '.'),
        ('DHI_精准筛查助手-操作说明.md', '.'),
        ('使用指南.md', '.'),
        ('需求说明.md', '.')
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'pandas',
        'numpy',
        'openpyxl',
        'yaml',
        'pyqtgraph',
        'pydantic',
        'dateutil',
        'logging',
        'threading',
        'datetime',
        'pathlib',
        'json',
        'csv',
        'math',
        'statistics',
        'hashlib',
        'uuid'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'test',
        'tests',
        'unittest'
    ],
    noarchive=False,
    optimize=2,
)

# Python包配置
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 可执行文件配置 (onedir模式)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # onedir模式关键配置
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI应用，无控制台
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='whg3r-qi1nv-001.ico'
)

# 文件收集配置 (onedir模式)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME  # 输出文件夹名称
)
