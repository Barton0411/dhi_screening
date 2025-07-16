#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试标签页宽度调整效果 - 确保标签名称完整显示
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QTabWidget
from PyQt6.QtCore import Qt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desktop_app import MainWindow

def test_tab_width_fix():
    """测试标签页宽度调整效果"""
    print("🧪 测试标签页宽度调整效果...")
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = MainWindow()
    
    print("✅ 窗口已创建，请手动测试以下标签页的宽度:")
    print("   1. 主标签页:")
    print("      - 基础数据")
    print("      - DHI基础筛选") 
    print("      - 慢性乳房炎筛查")
    print("      - 隐性乳房炎监测")
    print("   2. 筛选结果标签页内的次级标签页:")
    print("      - 📊 DHI基础筛选")
    print("      - 🏥 慢性乳房炎筛查")
    print("      - 👁️ 隐形乳房炎监测")
    print("   3. 检查所有标签名称是否完整显示，没有被截断")
    print("   4. 验证标签页宽度是否足够容纳中文文本")
    
    # 显示窗口
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_tab_width_fix() 