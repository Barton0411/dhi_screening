#!/bin/bash
# 修复 PyQt6 兼容性问题

echo "修复 PyQt6 兼容性问题..."

# 卸载当前版本
pip uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip

# 清理缓存
pip cache purge

# 重新安装兼容版本
pip install PyQt6==6.5.0 PyQt6-Qt6==6.5.0 PyQt6-sip==13.5.1

echo "修复完成！"