#!/usr/bin/env python3
"""
DHI筛查助手 - 一键启动脚本
"""

import subprocess
import sys
import os

def main():
    """启动主程序"""
    print("🚀 启动DHI筛查助手...")
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, "main.py")
    
    # 检查main.py是否存在
    if not os.path.exists(main_script):
        print(f"❌ 找不到主程序文件: {main_script}")
        return 1
    
    # 使用当前Python解释器运行主程序
    try:
        subprocess.run([sys.executable, main_script], check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ 程序运行失败: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
        return 0

if __name__ == "__main__":
    sys.exit(main())