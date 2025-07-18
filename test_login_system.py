#!/usr/bin/env python3
"""
登录系统测试脚本
测试登录、注册、单设备限制等功能
"""

import sys
import time
import threading
import requests
from PyQt6.QtWidgets import QApplication
from auth_module import AuthService, LoginDialog, RegisterDialog

# 测试配置
TEST_SERVER_URL = "http://localhost:8000"
TEST_USERS = [
    {"username": "test_user1", "password": "test123", "invite_code": "TEST2024"},
    {"username": "test_user2", "password": "test456", "invite_code": "TEST2024"}
]

def test_server_health():
    """测试服务器健康状态"""
    print("1. 测试服务器健康状态...")
    try:
        response = requests.get(f"{TEST_SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接服务器: {e}")
        return False

def test_user_registration():
    """测试用户注册"""
    print("\n2. 测试用户注册...")
    auth = AuthService(TEST_SERVER_URL)
    
    for user in TEST_USERS:
        success, message = auth.register(
            user["username"], 
            user["password"], 
            user["invite_code"]
        )
        if success:
            print(f"✅ 用户 {user['username']} 注册成功")
        else:
            if "用户名已存在" in message:
                print(f"⚠️  用户 {user['username']} 已存在")
            else:
                print(f"❌ 用户 {user['username']} 注册失败: {message}")

def test_normal_login():
    """测试正常登录"""
    print("\n3. 测试正常登录...")
    auth = AuthService(TEST_SERVER_URL)
    
    user = TEST_USERS[0]
    success, message, _ = auth.login(user["username"], user["password"])
    
    if success:
        print(f"✅ 用户 {user['username']} 登录成功")
        print(f"   Session Token: {auth.session_token[:20]}...")
        return auth
    else:
        print(f"❌ 登录失败: {message}")
        return None

def test_single_device_restriction():
    """测试单设备登录限制"""
    print("\n4. 测试单设备登录限制...")
    
    # 第一个设备登录
    auth1 = AuthService(TEST_SERVER_URL)
    user = TEST_USERS[0]
    success1, message1, _ = auth1.login(user["username"], user["password"])
    
    if success1:
        print(f"✅ 设备1登录成功")
        
        # 第二个设备尝试登录
        auth2 = AuthService(TEST_SERVER_URL)
        auth2.device_id = "test-device-2"  # 模拟不同设备
        
        success2, message2, extra = auth2.login(user["username"], user["password"])
        
        if not success2 and extra and extra.get("need_force_login"):
            print(f"✅ 正确检测到账号已在其他设备登录")
            
            # 测试强制登录
            success3, message3, _ = auth2.login(user["username"], user["password"], force=True)
            if success3:
                print(f"✅ 强制登录成功")
                
                # 验证第一个设备被踢下线
                if not auth1.heartbeat():
                    print(f"✅ 设备1已被踢下线")
                else:
                    print(f"❌ 设备1未被正确踢下线")
            else:
                print(f"❌ 强制登录失败: {message3}")
        else:
            print(f"❌ 单设备限制未生效")
    else:
        print(f"❌ 设备1登录失败: {message1}")

def test_heartbeat_mechanism():
    """测试心跳机制"""
    print("\n5. 测试心跳机制...")
    auth = AuthService(TEST_SERVER_URL)
    
    user = TEST_USERS[1]
    success, message, _ = auth.login(user["username"], user["password"])
    
    if success:
        print(f"✅ 登录成功")
        
        # 发送心跳
        heartbeat_success = auth.heartbeat()
        if heartbeat_success:
            print(f"✅ 心跳发送成功")
        else:
            print(f"❌ 心跳发送失败")
        
        # 测试会话超时（需要等待较长时间，这里只是演示）
        print("   (会话超时测试需要等待3分钟以上，跳过)")
    else:
        print(f"❌ 登录失败: {message}")

def test_logout():
    """测试注销功能"""
    print("\n6. 测试注销功能...")
    auth = AuthService(TEST_SERVER_URL)
    
    user = TEST_USERS[0]
    success, message, _ = auth.login(user["username"], user["password"], force=True)
    
    if success:
        print(f"✅ 登录成功")
        
        # 注销
        auth.logout()
        print(f"✅ 注销成功")
        
        # 验证会话已失效
        if not auth.heartbeat():
            print(f"✅ 会话已正确失效")
        else:
            print(f"❌ 会话未正确失效")
    else:
        print(f"❌ 登录失败: {message}")

def test_invite_code_limit():
    """测试邀请码使用限制"""
    print("\n7. 测试邀请码使用限制...")
    
    # 这个测试需要创建多个用户来测试邀请码限制
    # 由于需要30个用户才能达到限制，这里只做简单演示
    
    try:
        response = requests.get(f"{TEST_SERVER_URL}/invite-codes")
        if response.status_code == 200:
            codes = response.json()["codes"]
            for code in codes:
                print(f"   邀请码 {code['code']}: 已使用 {code['used_count']}/{code['max_uses']}")
            print("✅ 邀请码状态查询成功")
        else:
            print("❌ 无法获取邀请码信息")
    except Exception as e:
        print(f"❌ 查询邀请码失败: {e}")

def test_credential_storage():
    """测试凭证存储功能"""
    print("\n8. 测试凭证存储功能...")
    auth = AuthService(TEST_SERVER_URL)
    
    # 保存凭证
    auth.save_credentials("test_user", "test_password", remember=True)
    print("✅ 凭证保存成功")
    
    # 加载凭证
    creds = auth.load_credentials()
    if creds and creds.get("username") == "test_user":
        print("✅ 凭证加载成功")
        if creds.get("remember") and creds.get("password"):
            print("✅ 密码记忆功能正常")
    else:
        print("❌ 凭证加载失败")
    
    # 清除凭证
    auth.clear_credentials()
    if not auth.load_credentials():
        print("✅ 凭证清除成功")
    else:
        print("❌ 凭证清除失败")

def test_gui_components():
    """测试 GUI 组件（需要手动交互）"""
    print("\n9. 测试 GUI 组件...")
    print("   这是一个交互式测试，需要手动操作")
    print("   按 Ctrl+C 跳过此测试")
    
    try:
        app = QApplication(sys.argv)
        
        # 测试登录对话框
        print("\n   a) 测试登录对话框")
        print("      - 尝试空用户名/密码登录")
        print("      - 尝试错误的用户名/密码")
        print("      - 测试记住密码功能")
        print("      - 点击注册按钮")
        
        auth_service = AuthService(TEST_SERVER_URL)
        login_dialog = LoginDialog(None, auth_service)
        result = login_dialog.exec()
        
        if result == LoginDialog.DialogCode.Accepted:
            print(f"   ✅ 登录成功: {login_dialog.get_username()}")
        else:
            print("   ⚠️  用户取消登录")
        
    except KeyboardInterrupt:
        print("\n   ⚠️  GUI测试已跳过")
    except Exception as e:
        print(f"\n   ❌ GUI测试失败: {e}")

def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("蛋白质筛选系统 - 登录功能测试")
    print("=" * 50)
    
    # 检查服务器
    if not test_server_health():
        print("\n⚠️  请先启动会话管理服务器:")
        print("   cd session_server")
        print("   python server.py")
        return
    
    # 运行测试
    test_user_registration()
    test_normal_login()
    test_single_device_restriction()
    test_heartbeat_mechanism()
    test_logout()
    test_invite_code_limit()
    test_credential_storage()
    
    # GUI 测试（可选）
    print("\n是否进行 GUI 测试? (y/n): ", end="")
    if input().lower() == 'y':
        test_gui_components()
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)

def stress_test_concurrent_login():
    """压力测试：并发登录"""
    print("\n压力测试：10个用户并发登录...")
    
    def login_worker(user_id):
        auth = AuthService(TEST_SERVER_URL)
        username = f"stress_test_user_{user_id}"
        password = "test123"
        
        # 先注册
        auth.register(username, password, "TEST2024")
        
        # 然后登录
        success, message, _ = auth.login(username, password)
        if success:
            print(f"   线程 {user_id}: 登录成功")
            # 发送几次心跳
            for i in range(3):
                time.sleep(1)
                auth.heartbeat()
            auth.logout()
        else:
            print(f"   线程 {user_id}: 登录失败 - {message}")
    
    threads = []
    for i in range(10):
        t = threading.Thread(target=login_worker, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    print("✅ 压力测试完成")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stress":
        stress_test_concurrent_login()
    else:
        run_all_tests()