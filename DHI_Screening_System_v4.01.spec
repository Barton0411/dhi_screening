# -*- mode: python ; coding: utf-8 -*-
# DHI筛查助手 v4.01 - PyInstaller配置文件
# 伊利液奶奶科院

# 应用信息
APP_NAME = 'DHI_Screening_System_v4.01'
APP_VERSION = '4.01'
APP_DESCRIPTION = '伊利液奶奶科院 - DHI数据分析与乳房炎监测系统'

# 分析配置
a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[
        # 确保包含Python运行时DLL
    ],
    datas=[
        ('config.yaml', '.'),
        ('rules.yaml', '.'), 
        ('whg3r-qi1nv-001.ico', '.'),
        ('README.md', '.'),
        ('操作说明.md', '.'),
        ('mastitis_monitoring.py', '.'),
        ('data_processor.py', '.'),
        ('models.py', '.'),
        ('urea_tracker.py', '.'),
        ('progress_manager.py', '.'),
        ('chart_localization.py', '.'),
        ('auth_module', 'auth_module')
    ],
    hiddenimports=[
        # PyQt6 GUI库
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        
        # 数据处理库
        'pandas',
        'pandas._libs.tslibs.base',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.timestamps',
        
        # NumPy核心模块 (修复docstring错误)
        'numpy',
        'numpy.core',
        'numpy.core._multiarray_umath',
        'numpy.core._multiarray_tests',
        'numpy.core.multiarray',
        'numpy.core.numeric',
        'numpy.core.umath',
        'numpy.core._string_helpers',
        'numpy.core._dtype_ctypes',
        'numpy.core._internal',
        'numpy.linalg',
        'numpy.linalg.lapack_lite',
        'numpy.linalg._umath_linalg',
        'numpy.random',
        'numpy.random._common',
        'numpy.random._pickle',
        'numpy.random.bit_generator',
        'numpy.random.mtrand',
        'numpy.random._generator',
        'numpy.random._mt19937',
        'numpy.random._pcg64',
        'numpy.random._philox',
        'numpy.random._sfc64',
        
        # 其他库
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.styles.fills',
        'openpyxl.styles.fonts', 
        'openpyxl.styles.alignment',
        'openpyxl.styles.borders',
        'openpyxl.utils',
        'openpyxl.utils.dataframe',
        'openpyxl.workbook',
        'openpyxl.worksheet',
        'yaml',
        'pyqtgraph',
        'pydantic',
        'dateutil',
        
        # 本地模块 (解决动态导入)
        'mastitis_monitoring',
        'data_processor',
        'models',
        'logging',
        'threading',
        'datetime',
        'pathlib',
        'json',
        'csv',
        'math',
        'statistics',
        'hashlib',
        'uuid',
        'typing_extensions',
        
        # 系统和运行时库
        'ctypes',
        'ctypes.util',
        'platform',
        'subprocess',
        'tempfile',
        'shutil',
        'zipfile',
        'socket',
        
        # Excel处理引擎
        'xlrd',
        'xlrd.biffh',
        'xlrd.book',
        'xlrd.sheet',
        
        # PyQt6额外模块
        'PyQt6.QtPrintSupport',
        'PyQt6.sip',
        
        # 编码和本地化
        'encodings',
        'encodings.utf_8',
        'encodings.cp1252',
        'encodings.ascii',
        'locale',
        
        # 新增模块
        'progress_manager',
        'chart_localization',
        'urea_tracker'
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
