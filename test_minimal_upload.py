#!/usr/bin/env python3
"""
极简文件上传界面测试
用于对比找出空间占用过大的原因
"""

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QProgressBar)
from PyQt6.QtCore import Qt

class MinimalUploadTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("极简上传界面测试")
        self.setGeometry(100, 100, 600, 400)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # 1. 极简卡片 - 无标题栏版本
        simple_card = QWidget()
        simple_card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        
        # 卡片内容
        card_layout = QVBoxLayout(simple_card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(4)
        
        # 拖放区域 - 最小版本
        drop_area = QWidget()
        drop_area.setFixedHeight(40)
        drop_area.setStyleSheet("""
            QWidget {
                border: 1px dashed #007bff;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
        """)
        
        drop_layout = QHBoxLayout(drop_area)
        drop_layout.setContentsMargins(8, 4, 8, 4)
        
        drop_icon = QLabel("📤")
        drop_text = QLabel("拖拽文件到此处")
        drop_text.setStyleSheet("color: #6c757d; font-size: 11px;")
        
        drop_layout.addWidget(drop_icon)
        drop_layout.addWidget(drop_text)
        drop_layout.addStretch()
        
        card_layout.addWidget(drop_area)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        
        upload_btn = QPushButton("浏览文件")
        upload_btn.setMaximumHeight(24)
        process_btn = QPushButton("开始处理")
        process_btn.setMaximumHeight(24)
        
        btn_layout.addWidget(upload_btn)
        btn_layout.addWidget(process_btn)
        btn_layout.addStretch()
        
        card_layout.addLayout(btn_layout)
        
        # 进度条
        progress = QProgressBar()
        progress.setMaximumHeight(4)
        progress.setVisible(False)
        card_layout.addWidget(progress)
        
        main_layout.addWidget(simple_card)
        
        # 2. 对比用的标准卡片（带标题栏）
        standard_card = QWidget()
        standard_card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin: 2px;
            }
        """)
        
        standard_main_layout = QVBoxLayout(standard_card)
        standard_main_layout.setContentsMargins(0, 0, 0, 0)
        standard_main_layout.setSpacing(0)
        
        # 标题栏
        title_widget = QWidget()
        title_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
                border-radius: 8px 8px 0 0;
                padding: 2px 4px;
            }
        """)
        
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(2, 2, 2, 2)
        
        title_label = QLabel("📁 标准卡片（对比用）")
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333; background: transparent;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        standard_main_layout.addWidget(title_widget)
        
        # 标准卡片内容
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 内容高度测试
        content_label = QLabel("这里放内容区域 - 用于对比高度差异")
        content_label.setStyleSheet("padding: 20px; background-color: #f9f9f9;")
        content_layout.addWidget(content_label)
        
        standard_main_layout.addWidget(content_widget)
        main_layout.addWidget(standard_card)
        
        # 添加说明
        info_label = QLabel("对比测试：上方是极简版本，下方是标准版本")
        info_label.setStyleSheet("color: #666; font-size: 12px; padding: 10px;")
        main_layout.addWidget(info_label)
        
        main_layout.addStretch()

def main():
    app = QApplication(sys.argv)
    window = MinimalUploadTest()
    window.show()
    
    print("极简上传界面测试启动")
    print("请对比两个版本的高度差异，找出空间占用问题")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 