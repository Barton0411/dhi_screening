"""
忘记密码对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import pymysql

class ForgotPasswordDialog(QDialog):
    """忘记密码对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("忘记密码")
        self.setFixedSize(380, 480)
        
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
        layout.setSpacing(15)
        layout.setContentsMargins(35, 30, 35, 30)
        
        # 标题
        title = QLabel("重置密码")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 说明文字
        info_label = QLabel("请输入您的工号和姓名来验证身份")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(info_label)
        
        # 添加间距
        layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        # 工号输入
        self.employee_id_label = QLabel("工号:")
        self.employee_id_input = QLineEdit()
        self.employee_id_input.setPlaceholderText("请输入您的工号")
        layout.addWidget(self.employee_id_label)
        layout.addWidget(self.employee_id_input)
        
        # 姓名输入
        self.name_label = QLabel("姓名:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入您的姓名")
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        
        # 新密码输入
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
        button_layout.setSpacing(10)  # 设置按钮间距
        
        self.reset_btn = QPushButton("重置密码")
        self.reset_btn.clicked.connect(self.reset_password)
        self.reset_btn.setDefault(True)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
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
                margin-bottom: 5px;
                margin-top: 8px;
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
            QPushButton#cancelBtn {
                background-color: #f0f0f0;
                color: #333;
            }
            QPushButton#cancelBtn:hover {
                background-color: #e0e0e0;
            }
            QPushButton#cancelBtn:pressed {
                background-color: #d0d0d0;
            }
        """)
        
    def validate_inputs(self) -> tuple[bool, str]:
        """验证输入"""
        employee_id = self.employee_id_input.text().strip()
        name = self.name_input.text().strip()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not employee_id:
            return False, "请输入工号"
        
        if not name:
            return False, "请输入姓名"
            
        if not new_password:
            return False, "请输入新密码"
            
        if len(new_password) < 6:
            return False, "新密码长度至少6个字符"
            
        if new_password != confirm_password:
            return False, "两次输入的密码不一致"
            
        return True, ""
    
    def reset_password(self):
        """重置密码"""
        # 验证输入
        valid, error_msg = self.validate_inputs()
        if not valid:
            QMessageBox.warning(self, "输入错误", error_msg)
            return
        
        employee_id = self.employee_id_input.text().strip()
        name = self.name_input.text().strip()
        new_password = self.new_password_input.text()
        
        # 连接阿里云数据库
        connection = None
        try:
            # 阿里云数据库配置
            ALIYUN_DB_CONFIG = {
                'host': 'defectgene-new.mysql.polardb.rds.aliyuncs.com',
                'port': 3306,
                'user': 'defect_genetic_checking',
                'password': 'Jaybz@890411',
                'database': 'bull_library',
                'charset': 'utf8mb4'
            }
            
            connection = pymysql.connect(**ALIYUN_DB_CONFIG)
            
            with connection.cursor() as cursor:
                # 验证工号和姓名是否匹配
                sql = "SELECT * FROM `id-pw` WHERE ID=%s AND name=%s"
                cursor.execute(sql, (employee_id, name))
                
                if not cursor.fetchone():
                    QMessageBox.warning(self, "验证失败", "工号和姓名不匹配")
                    return
                
                # 更新密码
                sql = "UPDATE `id-pw` SET PW=%s WHERE ID=%s"
                cursor.execute(sql, (new_password, employee_id))
                connection.commit()
                
                QMessageBox.information(self, "成功", "密码重置成功！")
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重置密码失败: {str(e)}")
        finally:
            if connection:
                connection.close()