# OneDrive自动上传配置指南

本指南将帮助您配置GitHub Actions自动将构建好的EXE文件上传到OneDrive。

## 步骤1: 获取OneDrive访问Token

### 方法1: 使用rclone配置（推荐）

1. **下载rclone**
   ```bash
   # Windows
   https://downloads.rclone.org/rclone-current-windows-amd64.zip
   
   # macOS  
   brew install rclone
   
   # Linux
   curl https://rclone.org/install.sh | sudo bash
   ```

2. **配置OneDrive**
   ```bash
   rclone config
   ```

3. **按照提示操作**
   ```
   n) New remote
   name> onedrive
   Type of storage> onedrive
   client_id> [回车使用默认]
   client_secret> [回车使用默认]
   region> 1 (Microsoft Cloud Global)
   Edit advanced config? n
   Use auto config? y [这会打开浏览器进行授权]
   ```

4. **完成授权后，查看配置**
   ```bash
   rclone config show onedrive
   ```

5. **复制token字段的内容**
   - 在配置输出中找到`token = {...}`部分
   - 复制整个JSON token内容（包括大括号）

### 方法2: 手动获取（高级用户）

1. 访问 [Microsoft Graph Explorer](https://developer.microsoft.com/zh-cn/graph/graph-explorer)
2. 使用您的Microsoft账户登录
3. 授权必要的权限：Files.ReadWrite.All
4. 获取访问令牌

## 步骤2: 配置GitHub Secrets

1. **进入仓库设置**
   - 打开GitHub仓库页面
   - 点击 `Settings` 选项卡
   - 左侧菜单选择 `Secrets and variables` → `Actions`

2. **添加新的Secret**
   - 点击 `New repository secret`
   - Name: `ONEDRIVE_TOKEN`
   - Value: 粘贴您在步骤1中获取的完整token内容
   - 点击 `Add secret`

## 步骤3: 测试上传

1. **手动触发构建**
   - 进入仓库的 `Actions` 页面
   - 选择 `Build Windows EXE and Upload to OneDrive` workflow
   - 点击 `Run workflow` 按钮

2. **检查构建日志**
   - 查看 `Configure OneDrive and Upload` 步骤
   - 确认上传成功的消息

3. **验证OneDrive**
   - 登录您的OneDrive
   - 查看 `DHI_Screening_System/releases/` 目录
   - 应该能看到按时间戳命名的新文件夹

## 上传目录结构

```
OneDrive/
└── DHI_Screening_System/
    └── releases/
        └── v3.3_20250716_143022/  # 时间戳格式
            ├── DHI_Screening_System_v3.3.exe
            ├── [其他依赖文件]
            ├── README.md
            ├── CHANGELOG.md
            ├── whg3r-qi1nv-001.ico
            └── version_info.txt
```

## 故障排除

### 问题1: Token过期
- **现象**: 上传时提示认证失败
- **解决**: 重新执行步骤1获取新token，更新GitHub Secret

### 问题2: 权限不足
- **现象**: 上传时提示权限错误
- **解决**: 确保OneDrive账户有足够空间，token权限正确

### 问题3: 网络连接问题
- **现象**: 上传超时或连接失败
- **解决**: GitHub Actions会自动重试，也可以从Artifacts下载

## 备用方案

如果OneDrive上传失败，系统会自动：
1. 将文件保存为GitHub Actions Artifacts
2. 保留30天供下载
3. 在构建日志中显示下载链接

## 安全说明

- Token只存储在GitHub Secrets中，不会在日志中显示
- Token有有效期，过期后需要更新
- 建议定期检查和轮换访问令牌
- 不要在公共位置共享token内容

## 技术支持

如有问题请：
1. 检查GitHub Actions构建日志
2. 验证OneDrive账户状态
3. 确认token配置正确
4. 联系技术支持团队 