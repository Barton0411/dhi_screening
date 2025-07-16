#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试UI对齐修复效果 - 文件标签文本显示和处置办法配置区域对齐
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QScrollArea
from PyQt6.QtCore import Qt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desktop_app import MainWindow

def test_ui_alignment_fix():
    """测试UI对齐修复效果"""
    print("🧪 测试UI对齐修复效果...")
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = MainWindow()
    
    # 获取基础数据标签页
    basic_data_tab = main_window.tab_widget.widget(0)
    
    # 获取乳腺炎筛查标签页（包含处置办法配置）
    mastitis_tab = main_window.tab_widget.widget(2)  # 第三个标签页
    
    print("✅ 窗口已创建，请手动测试:")
    print("   1. 在基础数据标签页上传多个文件，检查文件标签名称是否完整显示")
    print("   2. 切换到乳腺炎筛查标签页，检查处置办法配置区域是否左对齐")
    print("   3. 观察文件标签是否支持文本换行")
    print("   4. 确认处置办法配置区域的标签和控件都左对齐")
    
    # 显示窗口
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_ui_alignment_fix() 