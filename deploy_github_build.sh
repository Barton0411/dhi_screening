#!/bin/bash
# DHI筛查分析系统 v3.0 - GitHub Actions一键部署脚本
# 伊利液奶奶科院

echo "🚀 部署GitHub Actions Windows构建..."
echo "伊利液奶奶科院 - DHI筛查分析系统 v3.0"
echo "========================================"

# 检查git状态
if ! git status &>/dev/null; then
    echo "❌ 请先初始化git仓库"
    echo "运行: git init && git remote add origin <your-repo-url>"
    exit 1
fi

# 检查是否有远程仓库
if ! git remote get-url origin &>/dev/null; then
    echo "❌ 请先设置GitHub远程仓库"
    echo "运行: git remote add origin <your-github-repo-url>"
    exit 1
fi

# 显示当前状态
echo "📁 当前项目状态:"
echo "   分支: $(git branch --show-current)"
echo "   远程: $(git remote get-url origin)"

# 添加所有文件
echo "📦 添加项目文件..."
git add .

# 提交更改
echo "💾 提交更改..."
git commit -m "添加Windows EXE构建配置 - 伊利液奶奶科院"

# 推送到GitHub
echo "🔗 推送到GitHub..."
git push origin main || git push origin master

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 配置已成功推送到GitHub！"
    echo ""
    echo "🎯 下一步操作："
    echo "1. 访问GitHub仓库的 'Actions' 标签页"
    echo "2. 点击 'Build Windows EXE' 工作流"
    echo "3. 点击 'Run workflow' 手动触发构建"
    echo "4. 等待构建完成（约5-10分钟）"
    echo "5. 在 'Artifacts' 中下载生成的Windows EXE"
    echo ""
    echo "📦 预期输出："
    echo "   - DHI筛查分析系统_v3.0_Windows.zip"
    echo "   - 解压后包含完整的Windows应用程序"
    echo ""
    echo "🏢 版权所有: 伊利液奶奶科院"
else
    echo "❌ 推送失败，请检查网络连接和GitHub权限"
    exit 1
fi
