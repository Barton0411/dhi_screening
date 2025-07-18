#!/bin/bash
# 启动会话管理服务器脚本

echo "启动 Protein Screening 会话管理服务器..."

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "警告: 未检测到虚拟环境，建议在虚拟环境中运行"
fi

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 启动服务器
echo "启动服务器..."
python server.py