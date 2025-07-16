#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有区域的左对齐修复效果
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QFormLayout, QSpinBox, QComboBox
from PyQt6.QtCore import Qt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desktop_app import MainWindow

def test_all_alignment_fix():
    """测试所有区域的左对齐修复效果"""
    print("🧪 测试所有区域的左对齐修复效果...")
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = MainWindow()
    
    print("✅ 窗口已创建，请手动测试以下区域的左对齐效果:")
    print("   1. 基础数据标签页 - 基础筛选条件区域")
    print("   2. 乳腺炎筛查标签页 - 慢性感染牛识别标准区域")
    print("   3. 乳腺炎筛查标签页 - 处置办法配置区域（淘汰、禁配隔离等）")
    print("   4. 检查所有标签和控件是否都左对齐")
    print("   5. 验证文件标签名称是否完整显示")
    
    # 显示窗口
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_all_alignment_fix() 