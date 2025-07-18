#!/usr/bin/env python3
"""测试注册功能"""

import requests
import json

# 测试服务器地址
SERVER_URL = "http://localhost:8000"

def test_register(employee_id, password, invite_code, name, company):
    """测试注册"""
    print(f"\n测试注册:")
    print(f"  工号: {employee_id}")
    print(f"  姓名: {name}")
    print(f"  公司: {company}")
    print(f"  邀请码: {invite_code}")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/register",
            json={
                "username": employee_id,
                "password": password,
                "invite_code": invite_code,
                "name": name,
                "company": company
            },
            timeout=10
        )
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                print(f"✅ 注册成功: {data['message']}")
            else:
                print(f"❌ 注册失败: {data['message']}")
        else:
            print(f"❌ 服务器错误: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 错误: {e}")

def check_server():
    """检查服务器状态"""
    print("检查服务器状态...")
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接服务器: {e}")
        return False

if __name__ == "__main__":
    # 先检查服务器
    if not check_server():
        print("\n请先启动服务器:")
        print("cd session_server && python server.py")
        exit(1)
    
    # 测试注册
    print("\n" + "="*50)
    print("请输入注册信息:")
    
    employee_id = input("工号: ").strip()
    name = input("姓名: ").strip()
    company = input("公司名: ").strip()
    invite_code = input("邀请码: ").strip()
    password = input("密码: ").strip()
    
    test_register(employee_id, password, invite_code, name, company)