#!/bin/bash
# DHI筛查助手 v4.02 - macOS打包脚本
# 伊利液奶奶科院

set -e  # 遇到错误立即停止

VERSION="4.02"
APP_NAME="DHI筛查助手"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=========================================="
echo "DHI筛查助手 v${VERSION} macOS打包脚本"
echo "=========================================="

# 1. 清理旧文件
echo "清理旧文件..."
rm -rf "${SCRIPT_DIR}/build" "${SCRIPT_DIR}/dist"

# 2. 检查虚拟环境
if [ ! -d "${SCRIPT_DIR}/.venv" ]; then
    echo "错误：未找到虚拟环境 .venv"
    echo "请先创建虚拟环境并安装依赖："
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "  pip install pyinstaller"
    exit 1
fi

# 3. 激活虚拟环境
echo "激活虚拟环境..."
source "${SCRIPT_DIR}/.venv/bin/activate"

# 4. 检查PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "安装PyInstaller..."
    pip install pyinstaller
fi

# 5. 执行打包
echo "开始打包..."
pyinstaller DHI_Screening_System_macOS.spec

# 6. 检查打包结果
if [ -d "dist/${APP_NAME}.app" ]; then
    echo "✅ 打包成功！"
    echo "应用程序位置: dist/${APP_NAME}.app"
    
    # 7. 显示应用信息
    echo ""
    echo "应用信息："
    du -sh "dist/${APP_NAME}.app"
    
    # 8. 代码签名提示
    echo ""
    echo "下一步：代码签名"
    echo "如果您有开发者证书，请运行："
    echo "  codesign --force --deep --sign \"Developer ID Application: 您的名字 (TEAM_ID)\" \\"
    echo "           --options runtime \"dist/${APP_NAME}.app\""
    echo ""
    echo "验证签名："
    echo "  codesign --verify --verbose \"dist/${APP_NAME}.app\""
    echo "  spctl --assess --verbose \"dist/${APP_NAME}.app\""
else
    echo "❌ 打包失败！"
    exit 1
fi

# 9. 创建DMG（可选）
read -p "是否创建DMG安装包？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v create-dmg &> /dev/null; then
        echo "创建DMG..."
        create-dmg \
            --volname "${APP_NAME} ${VERSION}" \
            --window-pos 200 120 \
            --window-size 600 400 \
            --icon-size 100 \
            --icon "${APP_NAME}.app" 175 120 \
            --hide-extension "${APP_NAME}.app" \
            --app-drop-link 425 120 \
            "${APP_NAME}-${VERSION}.dmg" \
            "dist/"
        echo "✅ DMG创建成功: ${APP_NAME}-${VERSION}.dmg"
    else
        echo "未安装create-dmg，跳过DMG创建"
        echo "安装方法: brew install create-dmg"
    fi
fi

echo ""
echo "打包完成！"