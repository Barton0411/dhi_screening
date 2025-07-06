#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动测试脚本 - 验证核心模块是否正常工作
"""

import sys
import os

def test_imports():
    """测试核心模块导入"""
    try:
        print("🔍 测试核心模块导入...")
        
        # 测试基础依赖
        import pandas as pd
        print(f"✅ pandas: {pd.__version__}")
        
        import yaml
        print("✅ PyYAML: 正常")
        
        from PyQt6.QtCore import QT_VERSION_STR
        print(f"✅ PyQt6: {QT_VERSION_STR}")
        
        # 测试项目核心模块
        from data_processor import DataProcessor
        print("✅ DataProcessor: 导入成功")
        
        from models import FilterConfig
        print("✅ FilterConfig: 导入成功")
        
        # 测试配置文件读取
        processor = DataProcessor()
        print("✅ DataProcessor: 初始化成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_gui_import():
    """测试GUI组件导入（但不启动）"""
    try:
        print("\n🖥️ 测试GUI组件导入...")
        
        # 只导入不创建应用实例
        from PyQt6.QtWidgets import QApplication
        from desktop_app import DHIDesktopApp
        
        print("✅ GUI组件导入成功")
        return True
        
    except Exception as e:
        print(f"❌ GUI组件导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🥛 DHI筛查助手 - 启动测试")
    print("=" * 60)
    
    # 测试模块导入
    if not test_imports():
        return 1
    
    # 测试GUI导入
    if not test_gui_import():
        return 1
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！应用程序可以正常启动")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())