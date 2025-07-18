# 蛋白质筛选系统登录功能部署指南

## 一、系统架构概述

本系统采用客户端-服务器架构，包含：
- **客户端**：PyQt6 桌面应用程序
- **服务端**：FastAPI 会话管理服务器
- **数据库**：SQLite（本地）+ 阿里云 MySQL（用户验证）

## 二、服务端部署

### 1. 本地测试环境

```bash
# 进入服务器目录
cd session_server

# 安装依赖
pip install -r requirements.txt

# 启动服务器
python server.py
# 或使用启动脚本
./start_server.sh
```

服务器默认运行在 `http://localhost:8000`

### 2. 云服务器部署（推荐）

#### 阿里云 ECS 部署步骤：

1. **准备服务器**
   - 最低配置：1核2G内存
   - 操作系统：Ubuntu 20.04+ 或 CentOS 7+
   - 开放端口：8000（或自定义）

2. **安装 Python 环境**
   ```bash
   # Ubuntu
   sudo apt update
   sudo apt install python3.9 python3-pip python3-venv
   
   # CentOS
   sudo yum install python39 python39-pip
   ```

3. **部署服务**
   ```bash
   # 创建项目目录
   mkdir -p /opt/protein_screening
   cd /opt/protein_screening
   
   # 上传 session_server 文件夹
   # 使用 scp、rsync 或其他工具
   
   # 创建虚拟环境
   python3 -m venv venv
   source venv/bin/activate
   
   # 安装依赖
   pip install -r session_server/requirements.txt
   
   # 安装进程管理器
   pip install supervisor
   ```

4. **配置 Supervisor（保持服务运行）**
   
   创建配置文件 `/etc/supervisor/conf.d/session_server.conf`：
   ```ini
   [program:session_server]
   command=/opt/protein_screening/venv/bin/python /opt/protein_screening/session_server/server.py
   directory=/opt/protein_screening/session_server
   user=www-data
   autostart=true
   autorestart=true
   redirect_stderr=true
   stdout_logfile=/var/log/session_server.log
   environment=PATH="/opt/protein_screening/venv/bin"
   ```

5. **启动服务**
   ```bash
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start session_server
   ```

6. **配置 Nginx 反向代理（可选）**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $http_host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

### 3. 使用 Docker 部署（推荐）

创建 `Dockerfile`：
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY session_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY session_server/ .

EXPOSE 8000

CMD ["python", "server.py"]
```

部署命令：
```bash
# 构建镜像
docker build -t protein-session-server .

# 运行容器
docker run -d \
  --name session-server \
  -p 8000:8000 \
  -v $(pwd)/sessions.db:/app/sessions.db \
  --restart unless-stopped \
  protein-session-server
```

## 三、客户端配置

### 1. 设置服务器地址

客户端通过环境变量配置服务器地址：

```bash
# Windows
set AUTH_SERVER_URL=http://your-server:8000

# Linux/Mac
export AUTH_SERVER_URL=http://your-server:8000
```

或在启动脚本中设置：

```python
# 修改 desktop_app.py 中的默认地址
server_url = os.environ.get("AUTH_SERVER_URL", "http://your-server:8000")
```

### 2. 打包客户端

使用 PyInstaller 打包：

```bash
# 安装打包工具
pip install pyinstaller

# 打包（包含登录模块）
pyinstaller --name="蛋白质筛选系统" \
  --windowed \
  --icon=icon.ico \
  --add-data="auth_module:auth_module" \
  --add-data="config.yaml:." \
  --add-data="rules.yaml:." \
  main.py
```

## 四、邀请码管理

### 1. 初始邀请码

服务器启动时会自动创建以下测试邀请码：
- TEST2024
- WELCOME123
- BETA2024

### 2. 创建新邀请码

使用 API 创建：
```bash
curl -X POST "http://localhost:8000/invite-codes" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "NEWCODE2024",
    "max_uses": 30,
    "expires_days": 30
  }'
```

### 3. 查看邀请码状态

```bash
curl "http://localhost:8000/invite-codes"
```

## 五、安全建议

1. **HTTPS 配置**
   - 使用 Let's Encrypt 免费证书
   - 配置 Nginx SSL

2. **防火墙设置**
   ```bash
   # 只允许特定端口
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

3. **数据库备份**
   ```bash
   # 定期备份 SQLite 数据库
   cp sessions.db sessions_backup_$(date +%Y%m%d).db
   ```

4. **日志监控**
   - 查看服务日志：`tail -f /var/log/session_server.log`
   - 设置日志轮转

## 六、故障排查

### 常见问题

1. **客户端无法连接服务器**
   - 检查服务器是否运行：`curl http://server:8000/health`
   - 检查防火墙设置
   - 确认环境变量 `AUTH_SERVER_URL` 设置正确

2. **心跳失败**
   - 检查网络连接
   - 查看服务器日志
   - 确认会话未超时

3. **注册失败**
   - 检查邀请码是否有效
   - 确认用户名未被占用
   - 查看服务器错误日志

## 七、监控与维护

### 1. 健康检查脚本

创建 `health_check.py`：
```python
import requests
import smtplib
from email.mime.text import MIMEText

def check_health():
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            send_alert("Session server is down!")
    except:
        send_alert("Session server is not responding!")

def send_alert(message):
    # 配置邮件发送
    pass

if __name__ == "__main__":
    check_health()
```

### 2. 定时任务

添加到 crontab：
```bash
# 每5分钟检查一次
*/5 * * * * /opt/protein_screening/venv/bin/python /opt/protein_screening/health_check.py
```

## 八、性能优化

1. **数据库优化**
   - 定期清理过期会话
   - 添加索引优化查询

2. **服务器优化**
   - 使用 uvicorn workers 提高并发
   - 配置适当的超时时间

3. **客户端优化**
   - 实现断线重连机制
   - 缓存登录状态

## 九、更新部署

1. 备份当前版本
2. 停止服务：`sudo supervisorctl stop session_server`
3. 更新代码
4. 重启服务：`sudo supervisorctl start session_server`
5. 验证功能正常

## 十、联系支持

如遇到问题，请联系：
- 技术支持邮箱：[support@example.com]
- 项目文档：[项目 Wiki 链接]