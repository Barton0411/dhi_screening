#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse
from datetime import datetime

def main():
    """主函数 - 启动DHI蛋白筛查系统桌面应用程序"""
    
    print("=" * 60)
    print("🥛 DHI筛查助手 v2.6 - 桌面版")
    print("=" * 60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 导入PyQt6相关模块
        from desktop_app import DHIDesktopApp
        
        print("🚀 启动桌面应用程序...")
        
        # 创建并运行应用程序
        app = DHIDesktopApp()
        exit_code = app.run()
        
        print(f"\n✅ 应用程序已退出，退出代码: {exit_code}")
        return exit_code
        
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("请安装PyQt6: pip install PyQt6")
        return 1
        
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())