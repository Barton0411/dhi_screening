#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试左对齐效果
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QFormLayout, QSpinBox, QComboBox
from PyQt6.QtCore import Qt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desktop_app import MainWindow

def test_alignment_simple():
    """简单测试左对齐效果"""
    print("🧪 简单测试左对齐效果...")
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = MainWindow()
    
    print("✅ 窗口已创建，请手动测试:")
    print("   1. 切换到乳腺炎筛查标签页")
    print("   2. 查看处置办法配置区域（淘汰、禁配隔离等）")
    print("   3. 检查标签和控件是否左对齐")
    print("   4. 对比基础数据标签页的筛选条件是否也左对齐")
    
    # 显示窗口
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_alignment_simple() 