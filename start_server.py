#!/usr/bin/env python3
"""启动认证服务器"""

import subprocess
import sys
import os
import time

def main():
    print("🚀 启动认证服务器...")
    
    # 切换到服务器目录
    server_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_server")
    os.chdir(server_dir)
    
    # 使用当前Python解释器启动服务器
    python_executable = sys.executable
    
    try:
        # 启动服务器
        print(f"使用 {python_executable} 启动服务器...")
        subprocess.run([python_executable, "server.py"])
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())