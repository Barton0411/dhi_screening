#!/usr/bin/env python3
"""
诊断脚本 - 检查系统各组件是否正常
"""

import os
# 禁用localhost的代理
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

import requests
import pymysql
import sys

print("🔍 蛋白质筛选系统诊断")
print("=" * 50)

# 1. 检查服务器是否运行
print("\n1. 检查认证服务器...")
try:
    response = requests.get("http://localhost:8000/health", timeout=3)
    if response.status_code == 200:
        print("✅ 服务器运行正常")
    else:
        print(f"❌ 服务器响应异常: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ 无法连接到服务器")
    print("   请运行: cd session_server && python server.py")
    sys.exit(1)
except Exception as e:
    print(f"❌ 服务器检查失败: {e}")
    sys.exit(1)

# 2. 检查阿里云数据库连接
print("\n2. 检查阿里云数据库连接...")
ALIYUN_DB_CONFIG = {
    'host': 'defectgene-new.mysql.polardb.rds.aliyuncs.com',
    'port': 3306,
    'user': 'defect_genetic_checking',
    'password': 'Jaybz@890411',
    'database': 'bull_library',
    'charset': 'utf8mb4'
}

try:
    connection = pymysql.connect(**ALIYUN_DB_CONFIG)
    print("✅ 数据库连接成功")
    
    # 检查表结构
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE 'id-pw'")
        if cursor.fetchone():
            print("✅ 用户表 'id-pw' 存在")
            
            # 统计用户数
            cursor.execute("SELECT COUNT(*) FROM `id-pw`")
            count = cursor.fetchone()[0]
            print(f"   用户数量: {count}")
        else:
            print("❌ 用户表 'id-pw' 不存在")
    
    connection.close()
    
except pymysql.err.OperationalError as e:
    print(f"❌ 数据库连接失败: {e}")
    if "Can't connect" in str(e):
        print("\n可能的原因：")
        print("1. 网络无法访问阿里云")
        print("2. 防火墙阻止了连接")
        print("3. 数据库服务未启动")
    elif "Access denied" in str(e):
        print("\n可能的原因：")
        print("1. 用户名或密码错误")
        print("2. 用户权限不足")
except Exception as e:
    print(f"❌ 数据库检查失败: {type(e).__name__}: {e}")

# 3. 测试登录接口
print("\n3. 测试登录接口...")
test_data = {
    "username": "test_user",
    "password": "test_password",
    "device_id": "test_device_001",
    "force_login": False
}

try:
    response = requests.post(
        "http://localhost:8000/login",
        json=test_data,
        timeout=10
    )
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print("✅ 登录接口正常（测试账号不存在是预期的）")
        else:
            print(f"✅ 登录接口正常，返回: {data['message']}")
    elif response.status_code == 500:
        print("❌ 服务器内部错误")
        try:
            error_data = response.json()
            print(f"   错误详情: {error_data.get('detail', '未知错误')}")
        except:
            print(f"   响应内容: {response.text}")
    elif response.status_code == 502:
        print("❌ Bad Gateway - 服务器可能崩溃了")
    else:
        print(f"❌ 意外的状态码: {response.status_code}")
        print(f"   响应内容: {response.text}")
        
except Exception as e:
    print(f"❌ 登录测试失败: {type(e).__name__}: {e}")

print("\n" + "=" * 50)
print("诊断完成！")

# 建议
print("\n建议：")
if response.status_code == 502:
    print("1. 重启服务器: cd session_server && python server.py")
    print("2. 检查服务器日志中的错误信息")
    print("3. 确保已安装 pymysql: pip install pymysql")