# DHI筛查助手 v4.02 打包检查清单

## 打包前准备

### 代码与依赖
- [x] 代码中Mac架构兼容性检查完成
- [x] requirements.txt完整性验证通过
- [x] 所有第三方库都是跨平台的
- [x] Mac特定代码已做平台检测（open命令）

### 文档更新
- [x] README.md 已更新到v4.01
- [x] 操作说明.md 已更新到v4.01
- [x] CHANGELOG.md 记录了版本历史
- [x] config.yaml 版本号更新到4.02

### 版本控制
- [x] Git版本4.02提交完成
- [x] 创建标签 v4.02
- [x] GitHub推送完成

## macOS打包配置

### 准备工作
- [x] 创建 DHI_Screening_System_macOS.spec 配置文件
- [x] 创建 build_macos.sh 打包脚本
- [ ] 图标文件 whg3r-qi1nv-001.ico（需要转换为icns）
- [ ] 开发者证书准备（Developer ID Application: 王波臻）
- [ ] Team ID 获取

### 打包步骤
1. **安装依赖**
   ```bash
   source .venv/bin/activate
   pip install pyinstaller
   ```

2. **执行打包**
   ```bash
   ./build_macos.sh
   ```

3. **代码签名**（如有证书）
   ```bash
   codesign --force --deep --sign "Developer ID Application: 王波臻 (TEAM_ID)" \
            --options runtime dist/DHI筛查助手.app
   ```

4. **创建DMG**（可选）
   ```bash
   brew install create-dmg  # 如未安装
   # 打包脚本会提示是否创建DMG
   ```

## Windows打包配置

### GitHub Actions配置
- [x] 创建 .github/workflows/build-windows.yml
- [x] 使用 onedir 模式（非onefile）
- [x] 配置版本信息文件生成
- [x] 配置Inno Setup安装包生成

### 触发构建
1. **推送标签触发**
   ```bash
   git tag v4.02
   git push origin v4.02
   ```

2. **手动触发**
   - 在GitHub Actions页面手动运行工作流

## 测试检查项

### 功能测试
- [ ] 登录功能（连接阿里云数据库）
- [ ] 文件上传（ZIP和Excel）
- [ ] DHI基础筛选
- [ ] 尿素氮追踪分析
- [ ] 慢性乳房炎筛查
- [ ] 隐性乳房炎监测
- [ ] Excel导出功能
- [ ] 图表显示（中文菜单）

### 平台测试
- [ ] macOS 10.14+ 测试
- [ ] Windows 10 测试
- [ ] Windows 11 测试
- [ ] 中文显示正常
- [ ] 文件路径处理正确

## 发布准备

### macOS发布
- [ ] 应用程序签名验证
- [ ] DMG文件创建
- [ ] 公证流程（如需要）
- [ ] 最终测试

### Windows发布
- [ ] GitHub Actions构建成功
- [ ] 安装包下载测试
- [ ] 安装流程测试
- [ ] 卸载测试

## 注意事项

1. **图标处理**
   - macOS需要icns格式
   - Windows使用ico格式
   - PyInstaller可以自动转换，但最好预先准备

2. **路径处理**
   - 确保使用os.path.join()处理路径
   - 避免硬编码路径分隔符

3. **临时文件**
   - temp目录会在用户数据目录创建
   - 确保有写入权限

4. **数据库连接**
   - 确保阿里云数据库配置正确
   - 考虑网络连接异常处理

5. **调试信息**
   - 生产版本设置 debug: false
   - 移除敏感信息输出

---

最后更新：2025-07-19