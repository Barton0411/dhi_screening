"""
登录对话框 - 支持记住密码和单设备登录
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QWidget, QCheckBox, QSpacerItem,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QColor
from pathlib import Path  
import logging
try:
    from .simple_auth_service import SimpleAuthService as AuthService
except ImportError:
    try:
        from .simple_auth_service_v2 import SimpleAuthService as AuthService
    except ImportError:
        from .auth_service import AuthService
from .register_dialog import RegisterDialog

class LoginDialog(QDialog):
    """用户登录对话框"""
    
    # 登录成功信号
    login_successful = pyqtSignal(str)  # 传递用户名
    
    def __init__(self, parent=None, auth_service=None):
        """
        初始化登录对话框
        
        Args:
            parent: 父窗口
            auth_service: 认证服务实例
        """
        super().__init__(parent)
        print("LoginDialog.__init__ 开始")
        self.auth_service = auth_service or AuthService()
        self.setWindowTitle("用户登录 - DHI筛查助手")
        self.setFixedSize(380, 360)
        
        # 设置窗口标志 - 添加置顶标志
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # 确保窗口始终置顶
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)
        
        # 设置窗口图标
        icon_path = Path(__file__).parent.parent / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self._setup_ui()
        self._setup_styles()
        self._load_saved_credentials()
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(35, 30, 35, 25)
        
        # 标题
        title = QLabel("欢迎使用DHI筛查助手")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #333; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # 添加一些间距
        layout.addSpacerItem(QSpacerItem(20, 25, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        # 账号输入
        self.username_label = QLabel("账号:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        
        # 密码输入
        self.password_label = QLabel("密码:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("请输入密码")
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        
        # 记住密码和忘记密码行
        remember_forgot_layout = QHBoxLayout()
        
        self.remember_checkbox = QCheckBox("记住密码")
        remember_forgot_layout.addWidget(self.remember_checkbox)
        
        remember_forgot_layout.addStretch()
        
        self.forgot_password_label = QLabel("<a href='#'>忘记密码？</a>")
        self.forgot_password_label.setOpenExternalLinks(False)
        self.forgot_password_label.linkActivated.connect(self.show_forgot_password)
        self.forgot_password_label.setCursor(Qt.CursorShape.PointingHandCursor)
        remember_forgot_layout.addWidget(self.forgot_password_label)
        
        layout.addLayout(remember_forgot_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # 设置按钮间距
        
        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.login)
        self.login_button.setDefault(True)
        
        self.register_button = QPushButton("注册")
        self.register_button.setObjectName("registerBtn")
        # 使用 lambda 添加调试
        self.register_button.clicked.connect(lambda: self.on_register_clicked())
        print(f"注册按钮已创建并连接")
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)
        layout.addLayout(button_layout)
        
        # 等待提示
        self.waiting_label = QLabel("正在连接服务器...")
        self.waiting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.waiting_label.hide()
        layout.addWidget(self.waiting_label)
        
        self.setLayout(layout)
        
        # 设置回车键登录
        self.password_input.returnPressed.connect(self.login)
        
    def _setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 8px;
            }
            QLabel {
                color: #333;
                font-size: 14px;
                margin-bottom: 2px;
                margin-top: 3px;
            }
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 14px;
                background-color: #f8f9fa;
                color: #333;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 1px solid #007AFF;
                background-color: white;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #999;
            }
            QPushButton {
                padding: 8px 20px;
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: 500;
                min-width: 100px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #0051D5;
            }
            QPushButton:pressed {
                background-color: #0041AB;
            }
            QPushButton#registerBtn {
                background-color: #f0f0f0;
                color: #333;
            }
            QPushButton#registerBtn:hover {
                background-color: #e0e0e0;
            }
            QPushButton#registerBtn:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #c0c0c0;
                color: #888;
            }
            QCheckBox {
                font-size: 14px;
                color: #666;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #007AFF;
                border-color: #007AFF;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+PHBhdGggZD0iTTkgMTYuMTdMNC44MyAxMmwtMS40MiAxLjQxTDkgMTkgMjEgN2wtMS40MS0xLjQxeiIvPjwvc3ZnPg==);
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #007AFF;
            }
            /* 忘记密码链接样式 */
            QLabel a {
                color: #007AFF;
                text-decoration: none;
            }
            QLabel a:hover {
                text-decoration: underline;
                color: #0051D5;
            }
        """)
        
    def _load_saved_credentials(self):
        """加载保存的凭证"""
        creds = self.auth_service.load_credentials()
        if creds:
            self.username_input.setText(creds.get("username", ""))
            if creds.get("remember") and creds.get("password"):
                self.password_input.setText(creds.get("password", ""))
                self.remember_checkbox.setChecked(True)
            else:
                self.remember_checkbox.setChecked(False)
    
    def show_waiting(self, message: str = "正在连接服务器..."):
        """显示等待提示"""
        self.waiting_label.setText(message)
        self.waiting_label.show()
        self.login_button.setEnabled(False)
        self.register_button.setEnabled(False)
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.remember_checkbox.setEnabled(False)
        
    def hide_waiting(self):
        """隐藏等待提示"""
        self.waiting_label.hide()
        self.login_button.setEnabled(True)
        self.register_button.setEnabled(True)
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.remember_checkbox.setEnabled(True)
        
    def login(self):
        """处理登录"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入账号和密码")
            return
        
        self.show_waiting("正在验证登录信息...")
        
        # 使用定时器异步处理登录
        QTimer.singleShot(100, lambda: self._process_login(username, password))
        
    def _process_login(self, username: str, password: str, force: bool = False):
        """处理登录逻辑"""
        success, message, extra = self.auth_service.login(username, password, force)
        
        if success:
            # 保存凭证
            self.auth_service.save_credentials(
                username, 
                password, 
                self.remember_checkbox.isChecked()
            )
            
            # 发送登录成功信号
            self.login_successful.emit(username)
            self.accept()
        else:
            self.hide_waiting()
            
            # 检查是否需要强制登录
            if extra and extra.get("need_force_login"):
                reply = QMessageBox.question(
                    self, 
                    "登录冲突",
                    f"该账号已在其他设备登录。\n是否强制登录并踢掉其他设备？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # 强制登录
                    self.show_waiting("正在强制登录...")
                    QTimer.singleShot(100, lambda: self._process_login(username, password, True))
                else:
                    # 清空密码框
                    self.password_input.clear()
                    self.password_input.setFocus()
            else:
                # 其他错误
                QMessageBox.warning(self, "登录失败", message)
                self.password_input.clear()
                self.password_input.setFocus()
    
    def show_register(self):
        """显示注册对话框"""
        try:
            print("点击了注册按钮")
            print("开始创建 RegisterDialog...")
            dialog = RegisterDialog(self, self.auth_service)
            print("RegisterDialog 创建成功")
            print("准备显示对话框...")
            result = dialog.exec()
            print(f"对话框返回结果: {result}")
            if result == QDialog.DialogCode.Accepted:
                # 注册成功后自动填充用户名
                username = dialog.get_username()
                if username:
                    self.username_input.setText(username)
                    self.password_input.setFocus()
                    QMessageBox.information(self, "注册成功", "注册成功，请使用您的密码登录")
        except Exception as e:
            print(f"显示注册对话框时出错: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"无法打开注册窗口: {str(e)}")
    
    def get_username(self) -> str:
        """获取登录的用户名"""
        return self.auth_service.username
    
    def on_register_clicked(self):
        """处理注册按钮点击"""
        print("on_register_clicked 被调用")
        self.show_register()
    
    def show_forgot_password(self):
        """显示忘记密码对话框"""
        try:
            print("点击了忘记密码链接")
            print("开始导入 ForgotPasswordDialog...")
            from .forgot_password_dialog import ForgotPasswordDialog
            print("ForgotPasswordDialog 导入成功")
            print("开始创建对话框...")
            dialog = ForgotPasswordDialog(self)
            print("ForgotPasswordDialog 创建成功")
            print("准备显示对话框...")
            dialog.exec()
            print("对话框关闭")
        except Exception as e:
            print(f"显示忘记密码对话框时出错: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"无法打开忘记密码窗口: {str(e)}")

# 便捷函数
def show_login_dialog(parent=None, auth_service=None) -> tuple[bool, str]:
    """
    显示登录对话框
    
    Args:
        parent: 父窗口
        auth_service: 认证服务实例
        
    Returns:
        (是否登录成功, 用户名)
    """
    dialog = LoginDialog(parent, auth_service)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return True, dialog.get_username()
    return False, None