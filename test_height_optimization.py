#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
界面高度优化测试 - 验证拖拽区域和文件列表展示区域的高度调整
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QScrollArea
from PyQt6.QtCore import Qt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desktop_app import MainWindow

def test_height_optimization():
    """测试界面高度优化效果"""
    print("🧪 开始测试界面高度优化...")
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = MainWindow()
    
    # 获取基础数据标签页
    basic_data_tab = main_window.tab_widget.widget(0)  # 第一个标签页是基础数据
    
    # 查找拖拽区域和滚动区域
    drop_area = None
    scroll_area = None
    
    def find_widgets(widget):
        nonlocal drop_area, scroll_area
        
        # 查找拖拽区域（通过固定高度特征）
        if (hasattr(widget, 'height') and 
            widget.height() > 0 and
            widget.height() >= 100):  # 拖拽区域应该有较大高度
            style = widget.styleSheet()
            if (style and 
                "border: 2px dashed #007bff" in style and
                "background-color: #f8f9fa" in style):
                drop_area = widget
                print(f"✅ 找到拖拽区域，高度: {widget.height()}px")
        
        # 查找滚动区域（QScrollArea）
        if isinstance(widget, QScrollArea):
            scroll_area = widget
            print(f"✅ 找到滚动区域，最大高度: {widget.maximumHeight()}px")
        
        # 递归查找子组件
        for child in widget.findChildren(QWidget):
            find_widgets(child)
    
    find_widgets(basic_data_tab)
    
    # 验证拖拽区域高度
    if drop_area:
        expected_height = main_window.get_dpi_scaled_size(150)
        actual_height = drop_area.height()
        print(f"📏 拖拽区域高度验证:")
        print(f"   期望高度: {expected_height}px")
        print(f"   实际高度: {actual_height}px")
        print(f"   状态: {'✅ 通过' if actual_height >= expected_height else '❌ 失败'}")
    else:
        print("❌ 未找到拖拽区域")
    
    # 验证滚动区域
    if scroll_area:
        expected_max_height = main_window.get_dpi_scaled_size(200)
        actual_max_height = scroll_area.maximumHeight()
        print(f"📏 滚动区域最大高度验证:")
        print(f"   期望最大高度: {expected_max_height}px")
        print(f"   实际最大高度: {actual_max_height}px")
        print(f"   状态: {'✅ 通过' if actual_max_height >= expected_max_height else '❌ 失败'}")
        
        # 检查滚动策略
        vertical_policy = scroll_area.verticalScrollBarPolicy()
        horizontal_policy = scroll_area.horizontalScrollBarPolicy()
        print(f"📏 滚动策略验证:")
        print(f"   垂直滚动: {'✅ 按需显示' if vertical_policy == Qt.ScrollBarPolicy.ScrollBarAsNeeded else '❌ 策略错误'}")
        print(f"   水平滚动: {'✅ 始终隐藏' if horizontal_policy == Qt.ScrollBarPolicy.ScrollBarAlwaysOff else '❌ 策略错误'}")
    else:
        print("❌ 未找到滚动区域")
    
    # 测试文件标签创建
    test_filename = "test_file.xlsx"
    file_tag = main_window.create_file_tag(test_filename)
    
    if file_tag:
        expected_tag_height = main_window.get_dpi_scaled_size(36)
        actual_tag_height = file_tag.maximumHeight()
        print(f"📏 文件标签高度验证:")
        print(f"   期望高度: {expected_tag_height}px")
        print(f"   实际高度: {actual_tag_height}px")
        print(f"   状态: {'✅ 通过' if actual_tag_height >= expected_tag_height else '❌ 失败'}")
    else:
        print("❌ 文件标签创建失败")
    
    # 显示窗口进行视觉验证
    main_window.show()
    print("\n👀 请检查界面效果:")
    print("   1. 拖拽区域是否足够大（约150px高度）")
    print("   2. 文件列表区域是否有滚动条（上传多个文件时）")
    print("   3. 文件标签是否清晰易读")
    print("   4. 上传多个文件时是否不再被压缩")
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    test_height_optimization() 