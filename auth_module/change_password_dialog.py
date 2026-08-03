"""
修改密码对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class ChangePasswordDialog(QDialog):
    """修改密码对话框"""
    
    def __init__(self, parent=None, username=None, auth_service=None):
        super().__init__(parent)
        self.username = username
        self.auth_service = auth_service or getattr(parent, "auth_service", None)
        self.setWindowTitle("修改密码")
        self.setFixedSize(400, 300)
        
        # 设置窗口标志 - 移除 WindowStaysOnTopHint 以避免 macOS 问题
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self._setup_ui()
        self._setup_styles()
        
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # 标题
        title = QLabel("修改密码")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 用户名显示
        if self.username:
            user_label = QLabel(f"当前用户: {self.username}")
            user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(user_label)
        
        # 添加间距
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        # 旧密码
        self.old_password_label = QLabel("旧密码:")
        self.old_password_input = QLineEdit()
        self.old_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_password_input.setPlaceholderText("请输入当前密码")
        layout.addWidget(self.old_password_label)
        layout.addWidget(self.old_password_input)
        
        # 新密码
        self.new_password_label = QLabel("新密码:")
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("请输入新密码 (至少6个字符)")
        layout.addWidget(self.new_password_label)
        layout.addWidget(self.new_password_input)
        
        # 确认新密码
        self.confirm_password_label = QLabel("确认新密码:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("请再次输入新密码")
        layout.addWidget(self.confirm_password_label)
        layout.addWidget(self.confirm_password_input)
        
        # 添加弹性间距
        layout.addStretch()
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.change_btn = QPushButton("修改密码")
        self.change_btn.clicked.connect(self.change_password)
        self.change_btn.setDefault(True)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.change_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def _setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
                font-size: 14px;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                color: #333;
                min-height: 25px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                outline: none;
            }
            QPushButton {
                padding: 12px 24px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
    def validate_inputs(self) -> tuple[bool, str]:
        """验证输入"""
        old_password = self.old_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not old_password:
            return False, "请输入旧密码"
        
        if not new_password:
            return False, "请输入新密码"
            
        if len(new_password) < 6:
            return False, "新密码长度至少6个字符"
            
        if new_password != confirm_password:
            return False, "两次输入的新密码不一致"
            
        if old_password == new_password:
            return False, "新密码不能与旧密码相同"
            
        return True, ""
    
    def change_password(self):
        """修改密码"""
        # 验证输入
        valid, error_msg = self.validate_inputs()
        if not valid:
            QMessageBox.warning(self, "输入错误", error_msg)
            return
        
        old_password = self.old_password_input.text()
        new_password = self.new_password_input.text()
        
        if not self.auth_service:
            QMessageBox.critical(self, "修改失败", "登录状态已失效，请重新登录")
            return

        success, message = self.auth_service.change_password(old_password, new_password)
        if success:
            QMessageBox.information(self, "修改成功", "密码修改成功，请在下次登录时使用新密码")
            self.accept()
        else:
            QMessageBox.warning(self, "修改失败", message)
