#!/bin/bash
# 一键启动脚本

echo "🚀 启动蛋白质筛选系统..."
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 未找到虚拟环境，请先创建虚拟环境"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 检查依赖
echo "📦 检查依赖..."
pip install -q -r requirements.txt
pip install -q -r session_server/requirements.txt

# 启动服务器
echo ""
echo "🌐 启动认证服务器..."
cd session_server
python server.py &
SERVER_PID=$!
cd ..

# 等待服务器启动
echo "⏳ 等待服务器启动..."
sleep 3

# 检查服务器是否运行
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 服务器已启动"
else
    echo "❌ 服务器启动失败"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# 启动客户端
echo ""
echo "🖥️  启动客户端应用..."
python main.py

# 清理
echo ""
echo "🧹 关闭服务器..."
kill $SERVER_PID 2>/dev/null

echo "👋 程序已退出"