#!/usr/bin/env python3
"""测试对话框"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from auth_module import AuthService, LoginDialog, RegisterDialog, ForgotPasswordDialog

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试对话框")
        self.setGeometry(100, 100, 400, 300)
        
        # 创建认证服务
        self.auth_service = AuthService()
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 测试登录对话框按钮
        test_login_btn = QPushButton("测试登录对话框")
        test_login_btn.clicked.connect(self.test_login_dialog)
        layout.addWidget(test_login_btn)
        
        # 测试注册对话框按钮
        test_register_btn = QPushButton("测试注册对话框")
        test_register_btn.clicked.connect(self.test_register_dialog)
        layout.addWidget(test_register_btn)
        
        # 测试忘记密码对话框按钮
        test_forgot_btn = QPushButton("测试忘记密码对话框")
        test_forgot_btn.clicked.connect(self.test_forgot_dialog)
        layout.addWidget(test_forgot_btn)
        
    def test_login_dialog(self):
        try:
            dialog = LoginDialog(self, self.auth_service)
            dialog.exec()
        except Exception as e:
            print(f"登录对话框错误: {e}")
            import traceback
            traceback.print_exc()
            
    def test_register_dialog(self):
        try:
            dialog = RegisterDialog(self, self.auth_service)
            dialog.exec()
        except Exception as e:
            print(f"注册对话框错误: {e}")
            import traceback
            traceback.print_exc()
            
    def test_forgot_dialog(self):
        try:
            dialog = ForgotPasswordDialog(self)
            dialog.exec()
        except Exception as e:
            print(f"忘记密码对话框错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())