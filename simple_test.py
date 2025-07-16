#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试QScrollArea
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QScrollArea
from PyQt6.QtCore import Qt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desktop_app import MainWindow

def simple_test():
    """简单测试"""
    print("🧪 简单测试QScrollArea...")
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = MainWindow()
    
    # 显示窗口
    main_window.show()
    
    print("✅ 窗口已显示，请手动测试:")
    print("   1. 点击'浏览文件'按钮选择多个文件")
    print("   2. 观察文件列表区域是否有滚动条")
    print("   3. 检查上传多个文件时是否不再被压缩")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    simple_test() 