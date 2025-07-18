#!/usr/bin/env python3
"""简单测试注册对话框"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("1. 导入 PyQt6...")
    from PyQt6.QtWidgets import QApplication, QDialog
    print("   成功")
    
    print("2. 导入 auth_service...")
    from auth_module.auth_service import AuthService
    print("   成功")
    
    print("3. 导入 register_dialog...")
    from auth_module.register_dialog import RegisterDialog
    print("   成功")
    
    print("4. 创建 QApplication...")
    app = QApplication(sys.argv)
    print("   成功")
    
    print("5. 创建 AuthService...")
    auth_service = AuthService()
    print("   成功")
    
    print("6. 创建 RegisterDialog...")
    dialog = RegisterDialog(None, auth_service)
    print("   成功")
    
    print("7. 显示对话框...")
    dialog.show()
    print("   成功")
    
    print("\n所有导入和创建都成功！")
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()