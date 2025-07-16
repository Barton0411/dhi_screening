#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试QScrollArea修复效果 - 固定12条数据高度
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QScrollArea
from PyQt6.QtCore import Qt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desktop_app import MainWindow

def test_scroll_area():
    """测试QScrollArea修复效果"""
    print("🧪 测试QScrollArea修复效果 - 固定12条数据高度...")
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = MainWindow()
    
    # 获取基础数据标签页
    basic_data_tab = main_window.tab_widget.widget(0)
    
    # 查找所有QScrollArea
    scroll_areas = []
    
    def find_scroll_areas(widget):
        if isinstance(widget, QScrollArea):
            scroll_areas.append(widget)
            print(f"✅ 找到QScrollArea: 固定高度={widget.height()}px")
        
        for child in widget.findChildren(QWidget):
            find_scroll_areas(child)
    
    find_scroll_areas(basic_data_tab)
    
    if scroll_areas:
        print(f"✅ 共找到 {len(scroll_areas)} 个QScrollArea")
        
        # 检查第一个QScrollArea的配置
        scroll_area = scroll_areas[0]
        print(f"📏 QScrollArea配置:")
        print(f"   固定高度: {scroll_area.height()}px")
        print(f"   垂直滚动策略: {scroll_area.verticalScrollBarPolicy()}")
        print(f"   水平滚动策略: {scroll_area.horizontalScrollBarPolicy()}")
        print(f"   框架形状: {scroll_area.frameShape()}")
        print(f"   是否可调整大小: {scroll_area.widgetResizable()}")
        
        # 计算期望的高度
        single_file_height = main_window.get_dpi_scaled_size(36)  # 单个文件标签高度
        spacing = main_window.get_dpi_scaled_size(6)  # 间距
        expected_height = (single_file_height + spacing) * 12  # 12条数据的总高度
        
        print(f"📏 高度验证:")
        print(f"   单个文件标签高度: {single_file_height}px")
        print(f"   间距: {spacing}px")
        print(f"   期望总高度: {expected_height}px")
        print(f"   实际总高度: {scroll_area.height()}px")
        print(f"   状态: {'✅ 通过' if scroll_area.height() == expected_height else '❌ 失败'}")
        
        # 模拟添加多个文件标签来测试滚动效果
        print("\n🧪 模拟添加多个文件标签...")
        for i in range(15):  # 添加15个文件，超过12个
            filename = f"test_file_{i+1}.xlsx"
            file_tag = main_window.create_file_tag(filename)
            main_window.file_tags_layout.addWidget(file_tag)
        
        print(f"✅ 已添加15个文件标签（超过12个）")
        print(f"   文件标签布局中的组件数量: {main_window.file_tags_layout.count()}")
        print(f"   应该显示滚动条: {'是' if main_window.file_tags_layout.count() > 12 else '否'}")
        
    else:
        print("❌ 未找到QScrollArea")
    
    # 显示窗口
    main_window.show()
    print("\n👀 请检查:")
    print("   1. 文件列表区域是否固定为12条数据的高度")
    print("   2. 上传超过12个文件时是否出现滚动条")
    print("   3. 滚动条是否正常工作")
    print("   4. 文件标签是否清晰易读")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_scroll_area() 