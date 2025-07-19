#!/bin/bash
# DHI筛查助手 macOS 卸载脚本

echo "=========================================="
echo "DHI筛查助手 卸载程序"
echo "=========================================="
echo ""
echo "此脚本将删除："
echo "1. 应用程序"
echo "2. 应用数据和设置"
echo "3. 缓存和日志文件"
echo ""
read -p "确定要卸载吗？(y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "开始卸载..."
    
    # 1. 删除应用程序
    if [ -d "/Applications/DHI筛查助手.app" ]; then
        echo "删除应用程序..."
        rm -rf "/Applications/DHI筛查助手.app"
    fi
    
    # 2. 删除应用支持文件
    if [ -d "$HOME/Library/Application Support/DHI筛查助手" ]; then
        echo "删除应用数据..."
        rm -rf "$HOME/Library/Application Support/DHI筛查助手"
    fi
    
    # 3. 删除偏好设置
    echo "删除偏好设置..."
    rm -f "$HOME/Library/Preferences/com.yili.dhi.screening.plist"
    rm -f "$HOME/Library/Preferences/DHI.ProteinScreening.plist"
    
    # 4. 删除缓存
    if [ -d "$HOME/Library/Caches/DHI筛查助手" ]; then
        echo "删除缓存..."
        rm -rf "$HOME/Library/Caches/DHI筛查助手"
    fi
    
    # 5. 删除日志
    if [ -d "$HOME/Library/Logs/DHI筛查助手" ]; then
        echo "删除日志..."
        rm -rf "$HOME/Library/Logs/DHI筛查助手"
    fi
    
    # 6. 删除认证相关文件
    if [ -d "$HOME/.protein_screening" ]; then
        echo "删除认证数据..."
        rm -rf "$HOME/.protein_screening"
    fi
    
    # 7. 清理 Dock 图标（如果有）
    echo "清理 Dock..."
    defaults write com.apple.dock persistent-apps -array-add 2>/dev/null
    killall Dock 2>/dev/null
    
    echo ""
    echo "✅ 卸载完成！"
    echo ""
    echo "如果您使用了其他工具（如 AppCleaner）安装，"
    echo "可能还有一些残留文件需要手动清理。"
else
    echo "已取消卸载。"
fi