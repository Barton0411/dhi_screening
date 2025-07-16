#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
界面高度优化测试
测试按钮、输入框、进度条等元素的高度统一性
"""

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QSpinBox, QDateEdit, 
                             QProgressBar, QLabel, QFrame)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

class HeightTestWindow(QMainWindow):
    """高度测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("界面高度优化测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 测试区域1：按钮高度统一性
        self.create_button_test_area(main_layout)
        
        # 测试区域2：输入框高度统一性
        self.create_input_test_area(main_layout)
        
        # 测试区域3：进度条高度
        self.create_progress_test_area(main_layout)
        
        # 测试区域4：文件标签高度
        self.create_file_tag_test_area(main_layout)
        
        # 测试区域5：拖放区域高度
        self.create_drop_area_test(main_layout)
    
    def get_dpi_scaled_size(self, base_size: int) -> int:
        """获取DPI缩放后的尺寸"""
        # 简化的DPI缩放计算
        return int(base_size * 1.0)  # 可以根据实际DPI调整
    
    def create_button_test_area(self, parent_layout):
        """创建按钮测试区域"""
        group = QFrame()
        group.setFrameStyle(QFrame.Shape.StyledPanel)
        group.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 8px; padding: 10px; }")
        
        layout = QVBoxLayout(group)
        
        # 标题
        title = QLabel("🔘 按钮高度统一性测试")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 按钮行
        button_layout = QHBoxLayout()
        
        # 不同样式的按钮
        button_styles = {
            'primary': "background-color: #007bff; color: white; border: none; border-radius: 5px; padding: 8px 16px; font-weight: bold; min-height: 32px;",
            'success': "background-color: #28a745; color: white; border: none; border-radius: 5px; padding: 8px 16px; font-weight: bold; min-height: 32px;",
            'danger': "background-color: #dc3545; color: white; border: none; border-radius: 5px; padding: 8px 16px; font-weight: bold; min-height: 32px;",
            'secondary': "background-color: #6c757d; color: white; border: none; border-radius: 5px; padding: 8px 16px; font-weight: bold; min-height: 32px;"
        }
        
        for style_name, style in button_styles.items():
            btn = QPushButton(f"{style_name.title()} 按钮")
            btn.setStyleSheet(style)
            button_layout.addWidget(btn)
        
        layout.addLayout(button_layout)
        parent_layout.addWidget(group)
    
    def create_input_test_area(self, parent_layout):
        """创建输入框测试区域"""
        group = QFrame()
        group.setFrameStyle(QFrame.Shape.StyledPanel)
        group.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 8px; padding: 10px; }")
        
        layout = QVBoxLayout(group)
        
        # 标题
        title = QLabel("📝 输入框高度统一性测试")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 输入框行
        input_layout = QHBoxLayout()
        
        # 统一样式
        input_style = """
            QSpinBox, QDateEdit {
                border: 2px solid #ced4da;
                border-radius: 4px;
                padding: 6px 12px;
                background-color: white;
                min-height: 28px;
                color: #495057;
            }
            QSpinBox:focus, QDateEdit:focus {
                border-color: #007bff;
                outline: none;
                border-width: 2px;
            }
        """
        
        # 数字输入框
        spinbox = QSpinBox()
        spinbox.setRange(1, 99)
        spinbox.setValue(1)
        spinbox.setStyleSheet(input_style)
        input_layout.addWidget(QLabel("数字:"))
        input_layout.addWidget(spinbox)
        
        # 日期输入框
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        date_edit.setStyleSheet(input_style)
        input_layout.addWidget(QLabel("日期:"))
        input_layout.addWidget(date_edit)
        
        input_layout.addStretch()
        layout.addLayout(input_layout)
        parent_layout.addWidget(group)
    
    def create_progress_test_area(self, parent_layout):
        """创建进度条测试区域"""
        group = QFrame()
        group.setFrameStyle(QFrame.Shape.StyledPanel)
        group.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 8px; padding: 10px; }")
        
        layout = QVBoxLayout(group)
        
        # 标题
        title = QLabel("📊 进度条高度测试")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 进度条
        progress_bar = QProgressBar()
        progress_bar.setValue(43)
        progress_bar.setMaximumHeight(self.get_dpi_scaled_size(6))
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #e9ecef;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """)
        
        layout.addWidget(progress_bar)
        parent_layout.addWidget(group)
    
    def create_file_tag_test_area(self, parent_layout):
        """创建文件标签测试区域"""
        group = QFrame()
        group.setFrameStyle(QFrame.Shape.StyledPanel)
        group.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 8px; padding: 10px; }")
        
        layout = QVBoxLayout(group)
        
        # 标题
        title = QLabel("🏷️ 文件标签高度测试")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 文件标签
        tag_widget = QWidget()
        tag_widget.setMaximumHeight(self.get_dpi_scaled_size(24))
        tag_widget.setStyleSheet("""
            QWidget {
                background-color: #e9f4ff;
                border: 1px solid #007bff;
                border-radius: 10px;
                margin: 1px;
            }
        """)
        
        tag_layout = QHBoxLayout(tag_widget)
        tag_layout.setContentsMargins(8, 2, 8, 2)
        tag_layout.setSpacing(4)
        
        # 文件图标
        file_icon = QLabel("📄")
        file_icon.setStyleSheet("background: transparent; border: none; font-size: 10px;")
        tag_layout.addWidget(file_icon)
        
        # 文件名
        file_label = QLabel("测试文件.xlsx")
        file_label.setStyleSheet("background: transparent; border: none; font-size: 10px; color: #0056b3;")
        tag_layout.addWidget(file_label)
        
        tag_layout.addStretch()
        layout.addWidget(tag_widget)
        parent_layout.addWidget(group)
    
    def create_drop_area_test(self, parent_layout):
        """创建拖放区域测试"""
        group = QFrame()
        group.setFrameStyle(QFrame.Shape.StyledPanel)
        group.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 8px; padding: 10px; }")
        
        layout = QVBoxLayout(group)
        
        # 标题
        title = QLabel("📁 拖放区域高度测试")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 拖放区域
        drop_area = QWidget()
        drop_area.setFixedHeight(self.get_dpi_scaled_size(32))
        drop_area.setStyleSheet("""
            QWidget {
                border: 1px dashed #007bff;
                border-radius: 4px;
                background-color: #f8f9fa;
                margin: 1px;
            }
            QWidget:hover {
                background-color: #e9f4ff;
                border-color: #0056b3;
            }
        """)
        
        drop_layout = QHBoxLayout(drop_area)
        drop_layout.setContentsMargins(8, 4, 8, 4)
        drop_layout.setSpacing(8)
        
        # 上传图标
        upload_icon = QLabel("📤")
        upload_icon.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        drop_layout.addWidget(upload_icon)
        
        # 文字信息
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        
        upload_text = QLabel("拖拽或点击选择DHI Excel文件")
        upload_text.setStyleSheet("font-size: 11px; color: #6c757d; background: transparent; border: none;")
        text_layout.addWidget(upload_text)
        
        format_hint = QLabel("支持 .xlsx, .xls 格式")
        format_hint.setStyleSheet("font-size: 9px; color: #9ca3af; background: transparent; border: none;")
        text_layout.addWidget(format_hint)
        
        drop_layout.addWidget(text_widget)
        drop_layout.addStretch()
        
        layout.addWidget(drop_area)
        parent_layout.addWidget(group)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建测试窗口
    window = HeightTestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 