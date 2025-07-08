#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DHI筛查分析系统 v3.0 - cx_Freeze打包脚本
伊利液奶奶科院

cx_Freeze对跨平台支持更好，可以在Mac上生成Windows exe
"""

import sys
from cx_Freeze import setup, Executable

# 定义应用信息
APP_NAME = "DHI筛查分析系统_v3.0"
APP_VERSION = "3.0"
APP_DESCRIPTION = "伊利液奶奶科院 - DHI数据分析与乳房炎监测系统"

# 包含的文件
include_files = [
    "config.yaml",
    "rules.yaml", 
    "whg3r-qi1nv-001.ico",
    "README.md",
    "DHI_精准筛查助手-操作说明.md",
    "使用指南.md",
    "需求说明.md"
]

# 需要包含的包
packages = [
    "PyQt6",
    "pandas",
    "numpy", 
    "openpyxl",
    "yaml",
    "dateutil",
    "pyqtgraph",
    "pydantic",
    "logging",
    "threading",
    "datetime",
    "pathlib",
    "json",
    "csv",
    "math",
    "statistics",
    "re",
    "hashlib",
    "uuid"
]

# 需要排除的包（减小体积）
excludes = [
    "tkinter",
    "matplotlib",
    "IPython", 
    "jupyter",
    "notebook",
    "scipy",
    "sklearn",
    "PIL",
    "cv2",
    "torch",
    "tensorflow",
    "test",
    "tests",
    "unittest",
    "doctest"
]

# 构建选项
build_exe_options = {
    "packages": packages,
    "excludes": excludes,
    "include_files": include_files,
    "optimize": 2,
    "include_msvcrt": True,  # Windows运行时
}

# 创建可执行文件
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Windows GUI应用

executable = Executable(
    script="desktop_app.py",
    base=base,
    target_name=APP_NAME + (".exe" if sys.platform == "win32" else ""),
    icon="whg3r-qi1nv-001.ico"
)

# 设置信息
setup(
    name=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    author="伊利液奶奶科院",
    options={"build_exe": build_exe_options},
    executables=[executable]
) 