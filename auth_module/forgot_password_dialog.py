"""安全的密码找回说明，不允许桌面客户端直接重置他人密码。"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout


class ForgotPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("找回密码")
        self.setFixedSize(380, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(20)

        title = QLabel("需要重置密码？")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        message = QLabel(
            "为保护账号安全，请联系管理员核验身份并重置密码。\n"
            "客户端不会要求或显示数据库、认证服务等内部信息。"
        )
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)

        close_button = QPushButton("知道了")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
