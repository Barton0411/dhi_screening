#!/bin/bash
# 启动认证服务器

echo "🚀 启动DHI筛查助手认证服务器..."

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  警告：未在虚拟环境中运行"
fi

# 安装依赖（如果需要）
echo "📦 检查依赖..."
pip install -q fastapi uvicorn pymysql 2>/dev/null

# 启动服务器
echo "🌐 启动服务器..."
cd session_server
python server.py