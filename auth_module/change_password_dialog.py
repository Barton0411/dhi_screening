"""
修改密码对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class ChangePasswordDialog(QDialog):
    """修改密码对话框"""
    
    def __init__(
        self, parent=None, username=None, auth_service=None, required=False
    ):
        super().__init__(parent)
        self.username = username
        self.auth_service = auth_service or getattr(parent, "auth_service", None)
        self.required = required
        self.setWindowTitle("首次登录必须修改密码" if required else "修改密码")
        
        # 设置窗口标志 - 移除 WindowStaysOnTopHint 以避免 macOS 问题
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self._setup_ui()
        self._setup_styles()

        # 让控件的实际尺寸决定窗口下限。macOS/Retina 下字体与输入框的
        # sizeHint 会高于 Windows，固定 300px 高度会导致内容互相覆盖。
        self.layout().activate()
        content_height = self.sizeHint().height()
        self.setMinimumSize(440, max(430, content_height))
        self.resize(440, max(450, content_height))
        
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(32, 24, 32, 24)
        
        # 标题
        self.title_label = QLabel("首次登录必须修改密码" if self.required else "修改密码")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)
        
        # 用户名显示
        self.user_label = None
        if self.username:
            self.user_label = QLabel(f"当前用户: {self.username}")
            self.user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.user_label)
        
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
        self.cancel_btn.setVisible(not self.required)
        
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
                padding: 9px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                color: #333;
                min-height: 24px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                outline: none;
            }
            QPushButton {
                padding: 10px 24px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
                min-height: 30px;
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

    def reject(self):
        if self.required:
            QMessageBox.warning(self, "必须修改密码", "完成密码修改后才能继续使用")
            return
        super().reject()

    def closeEvent(self, event):
        if self.required:
            event.ignore()
            QMessageBox.warning(self, "必须修改密码", "完成密码修改后才能继续使用")
            return
        super().closeEvent(event)
