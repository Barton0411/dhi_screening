#!/usr/bin/env python3
"""检查依赖是否已安装"""

import sys
import importlib

print(f"Python 版本: {sys.version}")
print("-" * 60)

dependencies = [
    "fastapi",
    "uvicorn", 
    "pymysql",
    "pydantic",
    "PyQt6"
]

missing = []

for dep in dependencies:
    try:
        importlib.import_module(dep)
        print(f"✅ {dep} 已安装")
    except ImportError:
        print(f"❌ {dep} 未安装")
        missing.append(dep)

if missing:
    print("\n需要安装以下依赖：")
    print(f"pip install {' '.join(missing)}")
else:
    print("\n✅ 所有依赖都已安装")