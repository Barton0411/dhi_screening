#!/bin/bash
# 创建 DMG 安装包脚本

APP_NAME="DHI筛查助手"
VERSION="4.02"
VOLUME_NAME="${APP_NAME} v${VERSION}"
DMG_NAME="${APP_NAME}-v${VERSION}-macOS.dmg"
SOURCE_DIR="dist"

# 检查应用是否存在
if [ ! -d "${SOURCE_DIR}/${APP_NAME}.app" ]; then
    echo "错误：未找到 ${SOURCE_DIR}/${APP_NAME}.app"
    echo "请先运行 ./build_macos.sh 生成应用程序"
    exit 1
fi

# 检查 create-dmg 是否安装
if ! command -v create-dmg &> /dev/null; then
    echo "错误：未找到 create-dmg"
    echo "请先安装：brew install create-dmg"
    exit 1
fi

# 删除旧的 DMG
rm -f "${DMG_NAME}"

echo "创建 DMG 安装包..."

# 创建 DMG
create-dmg \
    --volname "${VOLUME_NAME}" \
    --volicon "whg3r-qi1nv-001.icns" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "${APP_NAME}.app" 175 120 \
    --hide-extension "${APP_NAME}.app" \
    --app-drop-link 425 120 \
    --background "docs/dmg-background.png" \
    --no-internet-enable \
    "${DMG_NAME}" \
    "${SOURCE_DIR}/"

# 如果没有背景图片，使用简化版本
if [ ! -f "docs/dmg-background.png" ]; then
    echo "未找到背景图片，使用默认样式..."
    rm -f "${DMG_NAME}"
    
    create-dmg \
        --volname "${VOLUME_NAME}" \
        --volicon "whg3r-qi1nv-001.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "${APP_NAME}.app" 175 120 \
        --hide-extension "${APP_NAME}.app" \
        --app-drop-link 425 120 \
        --no-internet-enable \
        "${DMG_NAME}" \
        "${SOURCE_DIR}/"
fi

if [ -f "${DMG_NAME}" ]; then
    echo "✅ DMG 创建成功：${DMG_NAME}"
    echo "文件大小：$(du -h ${DMG_NAME} | cut -f1)"
    
    # 询问是否要签名
    echo ""
    echo "如果您有开发者证书，可以对 DMG 进行签名："
    echo "  codesign --force --sign \"Developer ID Application: 您的名字 (TEAM_ID)\" ${DMG_NAME}"
    echo ""
    echo "公证 DMG："
    echo "  xcrun notarytool submit ${DMG_NAME} --apple-id your@email.com --team-id TEAM_ID --password APP_PASSWORD --wait"
else
    echo "❌ DMG 创建失败"
    exit 1
fi