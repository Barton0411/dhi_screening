# 登录功能使用说明

## 快速开始

### 1. 启动会话管理服务器

```bash
cd session_server
python server.py
```

服务器将在 http://localhost:8000 运行

### 2. 启动客户端应用

```bash
# 设置服务器地址（可选，默认为 localhost:8000）
export AUTH_SERVER_URL=http://localhost:8000

# 运行应用
python main.py
```

### 3. 登录或注册

- **首次使用**：点击"注册"按钮创建新账号
  - 需要有效的邀请码（默认测试邀请码：TEST2024, WELCOME123, BETA2024）
  - 用户名：3-20个字符，只能包含字母、数字和下划线
  - 密码：至少6个字符

- **已有账号**：输入用户名和密码登录
  - 可以勾选"记住密码"方便下次登录

## 功能特点

1. **单设备登录限制**
   - 同一账号只能在一台设备上登录
   - 如果账号已在其他设备登录，会提示是否强制登录

2. **会话管理**
   - 自动心跳保持会话活跃（每90秒）
   - 超过3分钟无心跳会自动登出

3. **邀请码系统**
   - 每个邀请码限制使用30次
   - 可设置邀请码过期时间

## 管理工具

### 查看邀请码

```bash
python manage_invite_codes.py list
```

### 创建新邀请码

```bash
# 创建单个邀请码
python manage_invite_codes.py create MYCODE2024 --max-uses 50

# 批量创建
python manage_invite_codes.py batch VIP 10 --max-uses 100
```

### 测试功能

```bash
# 运行测试脚本
python test_login_system.py

# 压力测试
python test_login_system.py --stress
```

## 部署说明

详细部署指南请参考 [deploy_guide.md](deploy_guide.md)

## 常见问题

### 1. 无法连接到服务器

- 检查服务器是否运行：`curl http://localhost:8000/health`
- 确认环境变量 `AUTH_SERVER_URL` 设置正确
- 检查防火墙设置

### 2. 登录后被踢下线

- 可能是同一账号在其他设备登录
- 检查网络连接是否稳定
- 查看服务器日志了解详情

### 3. 邀请码无效

- 使用管理工具查看邀请码状态
- 确认邀请码未过期且还有剩余使用次数

## 开发者信息

- 认证模块位置：`auth_module/`
- 服务器代码：`session_server/`
- 配置文件：通过环境变量配置

## 安全提示

1. 生产环境请使用 HTTPS
2. 定期备份数据库
3. 妥善保管邀请码
4. 定期更换数据库密码