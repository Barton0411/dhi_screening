# DHI筛查助手项目状态

更新时间：2026-08-03

## 当前目标与版本

- 仓库：`Barton0411/dhi_screening`
- 本次发布版本：`v4.02.25`
- 发布目标：保留现有账号，恢复安全登录与邀请码注册；加入 Windows/macOS 自动更新；在 GitHub Release 和阿里云 OSS 同步留档。
- 单一版本源：`VERSION`。`version.py`、启动页、PyInstaller spec、Inno Setup 和 GitHub Actions 均读取或校验它。

## 认证现状

- 桌面客户端通过 HTTPS 调用 `https://api.genepop.com`：
  - `POST /api/auth/login`
  - `POST /api/auth/register`
  - `POST /api/auth/change-password`
  - `POST /api/auth/verify`
  - `GET /health`
- 原有账号仍使用认证服务后的同一账号库，无需重新注册。
- 新账号继续使用邀请码提交注册申请。
- 登录页提供“原账号密码登录”和“伊起牛登录”。伊起牛密码与上游令牌不会持久化，认证成功后通过 `/api/auth/yqn/exchange` 换取软件 JWT。
- 迁移前的 40 个原账号首次登录均返回受限 JWT，必须先修改自己的密码；完成前普通受保护接口和主界面均不可用。改密成功后服务端返回正常 JWT，并清除本机保存的旧密码。
- 修改密码由 JWT 限定只能修改当前账号；伊起牛登录不走本地改密。
- 忘记密码不再允许客户端凭“工号+姓名”直接重置，改为联系管理员核验身份。
- `simple_auth_service.py` 和兼容入口 `simple_auth_service_v2.py` 均不再包含数据库连接能力。

## 自动更新与发布

- 客户端启动时读取 OSS：
  `https://genetic-improve.oss-cn-beijing.aliyuncs.com/tools/dhi-screening/latest/version.json`
- 清单按平台提供 Windows EXE 与 macOS DMG 的 HTTPS 地址、文件大小和 SHA-256。
- 客户端只接受固定 OSS 域名和固定对象前缀；下载完成后必须同时通过大小和 SHA-256 校验才启动安装。
- 标签 `v*` 触发 `.github/workflows/release.yml`：
  1. Windows 和 macOS 并行构建；
  2. 汇总安装包并生成 `version.json`、`SHA256SUMS.txt`、发布说明；
  3. 先发布 OSS 不可变版本目录；
  4. 两个平台文件都成功后最后更新 OSS `latest/version.json`；
  5. 创建 GitHub Release。
- OSS 路径：
  - 不可变版本：`tools/dhi-screening/releases/v<版本>/`
  - 最新指针：`tools/dhi-screening/latest/version.json`

## 发布前后检查

1. `python -m unittest discover -s tests -v`
2. `python -m compileall` 检查认证、更新、启动和脚本模块。
3. 搜索源码中是否出现 `pymysql`、PolarDB 主机、数据库配置或疑似凭据。
4. 检查标签与 `VERSION` 完全一致。
5. 等待双平台构建与 publish job 全部成功。
6. 下载 GitHub Release 和 OSS 安装包，核对大小与 SHA-256。
7. 公网读取 latest 清单，分别按 Windows/macOS 模式通过客户端校验函数。

## 已知事项

- 旧版本曾把数据库凭据提交到公开 Git 历史；旧值已失效，任何情况下都不要恢复。若要彻底清除公开历史，需要单独安排历史重写和所有协作者重新同步，本次发布不重写历史。
- macOS DMG 当前未配置 Apple Developer 签名和公证，首次打开可能需要在系统安全设置中确认。
- 原工作目录在本次任务开始前已有 4 个认证文件修改和 4 个未跟踪文件；发布工作在独立 worktree 完成，原改动必须保留。
