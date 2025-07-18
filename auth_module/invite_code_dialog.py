"""
邀请码管理对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog,
    QHeaderView, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import requests
import os

# 禁用localhost的代理
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

class InviteCodeDialog(QDialog):
    """邀请码管理对话框"""
    
    def __init__(self, parent=None, server_url="http://localhost:8000"):
        super().__init__(parent)
        self.server_url = server_url
        self.setWindowTitle("邀请码管理")
        self.setFixedSize(800, 600)
        
        # 设置窗口标志 - 移除 WindowStaysOnTopHint 以避免 macOS 问题
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self._setup_ui()
        self._setup_styles()
        self.load_invite_codes()
        
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = QLabel("邀请码管理")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("创建邀请码")
        self.create_btn.clicked.connect(self.create_invite_code)
        toolbar_layout.addWidget(self.create_btn)
        
        self.batch_create_btn = QPushButton("批量创建")
        self.batch_create_btn.clicked.connect(self.batch_create_codes)
        toolbar_layout.addWidget(self.batch_create_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_invite_codes)
        toolbar_layout.addWidget(self.refresh_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "邀请码", "已使用/总数", "剩余次数", "创建时间", "过期时间", "状态", "备注"
        ])
        
        # 设置表格样式
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.table)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
        
        self.setLayout(layout)
        
    def _setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
                color: #333;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                color: #333;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
    def load_invite_codes(self):
        """加载邀请码列表"""
        try:
            response = requests.get(f"{self.server_url}/invite-codes", timeout=10)
            if response.status_code == 200:
                data = response.json()
                codes = data.get("codes", [])
                
                self.table.setRowCount(len(codes))
                
                for i, code in enumerate(codes):
                    # 邀请码
                    self.table.setItem(i, 0, QTableWidgetItem(code['code']))
                    
                    # 使用情况
                    usage = f"{code['used_count']}/{code['max_uses']}"
                    self.table.setItem(i, 1, QTableWidgetItem(usage))
                    
                    # 剩余次数
                    remaining = code['max_uses'] - code['used_count']
                    self.table.setItem(i, 2, QTableWidgetItem(str(remaining)))
                    
                    # 创建时间
                    created_at = code['created_at'][:10] if code['created_at'] else "N/A"
                    self.table.setItem(i, 3, QTableWidgetItem(created_at))
                    
                    # 过期时间
                    expires_at = code['expires_at'][:10] if code['expires_at'] else "永久"
                    self.table.setItem(i, 4, QTableWidgetItem(expires_at))
                    
                    # 状态
                    status_code = code.get('status', 1)
                    if status_code == 1:
                        status = "可用" if remaining > 0 else "已用完"
                        color = Qt.GlobalColor.darkGreen if remaining > 0 else Qt.GlobalColor.red
                    elif status_code == 2:
                        status = "已使用"
                        color = Qt.GlobalColor.red
                    else:
                        status = "已过期"
                        color = Qt.GlobalColor.gray
                    
                    item = QTableWidgetItem(status)
                    item.setForeground(color)
                    self.table.setItem(i, 5, item)
                    
                    # 备注
                    remark = code.get('remark', '')
                    self.table.setItem(i, 6, QTableWidgetItem(remark))
                    
            else:
                QMessageBox.warning(self, "错误", f"获取邀请码失败: {response.status_code}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接服务器失败: {str(e)}")
    
    def create_invite_code(self):
        """创建单个邀请码"""
        code, ok = QInputDialog.getText(
            self, 
            "创建邀请码", 
            "请输入邀请码:"
        )
        
        if ok and code:
            # 询问最大使用次数
            max_uses, ok = QInputDialog.getInt(
                self,
                "设置使用次数",
                "最大使用次数:",
                30, 1, 1000
            )
            
            if ok:
                # 询问备注
                remark, ok_remark = QInputDialog.getText(
                    self,
                    "设置备注",
                    "备注说明 (可选):"
                )
                
                try:
                    response = requests.post(
                        f"{self.server_url}/invite-codes",
                        json={
                            "code": code,
                            "max_uses": max_uses,
                            "remark": remark if ok_remark else ""
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        QMessageBox.information(self, "成功", "邀请码创建成功")
                        self.load_invite_codes()
                    else:
                        QMessageBox.warning(self, "失败", "邀请码创建失败，可能已存在")
                        
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"创建失败: {str(e)}")
    
    def batch_create_codes(self):
        """批量创建邀请码"""
        # 创建批量创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("批量创建邀请码")
        dialog.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        # 前缀输入
        prefix_label = QLabel("邀请码前缀:")
        layout.addWidget(prefix_label)
        prefix_input = QInputDialog()
        prefix, ok = QInputDialog.getText(
            self,
            "批量创建",
            "邀请码前缀:"
        )
        
        if ok and prefix:
            # 数量输入
            count, ok = QInputDialog.getInt(
                self,
                "批量创建",
                "创建数量:",
                10, 1, 100
            )
            
            if ok:
                # 创建邀请码
                success_count = 0
                for i in range(1, count + 1):
                    code = f"{prefix}{i:04d}"
                    try:
                        response = requests.post(
                            f"{self.server_url}/invite-codes",
                            json={
                                "code": code,
                                "max_uses": 30
                            },
                            timeout=5
                        )
                        if response.status_code == 200:
                            success_count += 1
                    except:
                        pass
                
                QMessageBox.information(
                    self, 
                    "完成", 
                    f"成功创建 {success_count}/{count} 个邀请码"
                )
                self.load_invite_codes()