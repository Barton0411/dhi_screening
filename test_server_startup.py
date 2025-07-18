#!/usr/bin/env python3
"""测试服务器启动"""

import sys
import os

print("检查服务器启动环境...")
print(f"Python版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")

# 检查服务器文件
server_file = "session_server/server.py"
if os.path.exists(server_file):
    print(f"✅ 找到服务器文件: {server_file}")
else:
    print(f"❌ 找不到服务器文件: {server_file}")

# 尝试导入必要模块
try:
    import fastapi
    print("✅ FastAPI 已安装")
except ImportError:
    print("❌ FastAPI 未安装 - 运行: pip install fastapi")

try:
    import uvicorn
    print("✅ Uvicorn 已安装")
except ImportError:
    print("❌ Uvicorn 未安装 - 运行: pip install uvicorn")

try:
    import pymysql
    print("✅ PyMySQL 已安装")
except ImportError:
    print("❌ PyMySQL 未安装 - 运行: pip install pymysql")

# 尝试启动服务器
print("\n尝试导入服务器模块...")
try:
    sys.path.insert(0, 'session_server')
    import server
    print("✅ 服务器模块导入成功")
    
    # 测试数据库连接
    print("\n测试阿里云数据库连接...")
    try:
        conn = server.get_aliyun_connection()
        print("✅ 成功连接到阿里云数据库")
        conn.close()
    except Exception as e:
        print(f"❌ 连接阿里云数据库失败: {e}")
        
except Exception as e:
    print(f"❌ 导入服务器模块失败: {e}")
    import traceback
    traceback.print_exc()