# DHI筛查助手项目状态

更新时间：2026-08-14

## 当前目标与版本

- 仓库：`Barton0411/dhi_screening`
- 当前发布版本：`v4.02.30`
- 发布内容：紧急修复强制更新时关闭启动窗口导致程序提前退出；同时包含 v4.02.29 的默认伊起牛登录、系统凭据库记住密码、主界面检查更新、显示设置和高 DPI 修复。
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
- 登录页默认使用“伊起牛登录”，并保留“原账号密码登录”。用户勾选记住密码后，密码只保存到 macOS Keychain 或 Windows 凭据管理器；伊起牛上游令牌不持久化，认证成功后通过 `/api/auth/yqn/exchange` 换取软件 JWT。
- 迁移前的 40 个原账号首次登录均返回受限 JWT，必须先修改自己的密码；完成前普通受保护接口和主界面均不可用。改密成功后服务端返回正常 JWT，并清除本机保存的旧密码。
- 修改密码由 JWT 限定只能修改当前账号；伊起牛登录不走本地改密。
- 忘记密码不再允许客户端凭“工号+姓名”直接重置，改为联系管理员核验身份。
- `simple_auth_service.py` 和兼容入口 `simple_auth_service_v2.py` 均不再包含数据库连接能力。
- HTTPS 客户端显式使用随安装包携带的 `certifi` CA 证书，并禁用环境代理继承，避免 PyInstaller 运行环境出现证书链差异。

## 自动更新与发布

- 客户端启动时读取 OSS：
  `https://genetic-improve.oss-cn-beijing.aliyuncs.com/tools/dhi-screening/latest/version.json`
- 清单按平台提供 Windows EXE 与 macOS DMG 的 HTTPS 地址、文件大小和 SHA-256。
- 客户端只接受固定 OSS 域名和固定对象前缀；下载完成后必须同时通过大小和 SHA-256 校验才启动安装。
- 标签 `v*` 触发 `.github/workflows/release.yml`：
  1. Windows 和 macOS 分别运行认证/更新单元测试并并行构建；
  2. 汇总安装包并生成 `version.json`、`SHA256SUMS.txt`、发布说明；
  3. 先发布 OSS 不可变版本目录；
  4. 两个平台文件都成功后最后更新 OSS `latest/version.json`；
  5. 创建 GitHub Release。
- OSS 路径：
  - 不可变版本：`tools/dhi-screening/releases/v<版本>/`
  - 最新指针：`tools/dhi-screening/latest/version.json`

## v4.02.26 发布记录

- 合并 PR：`#2`；合并提交：`d3e22d398a08a272b78a8168001d944bd1bdfbdb`
- 正式 Actions：`30814329341`；Windows、macOS、publish 全部成功
- GitHub Release：`https://github.com/Barton0411/dhi_screening/releases/tag/v4.02.26`
- Windows：`DHI-Screening-v4.02.26-Windows-Setup.exe`，49,743,669 字节，SHA-256 `80182ab1b8b287cb81d5ef2832275535cdb1c8edad990cd89ec6c568e8cfde44`
- macOS：`DHI-Screening-v4.02.26-macOS.dmg`，60,723,084 字节，SHA-256 `1ec37c486266ddcb2e4b992d6b1daaf0526bed9c35897bdb622bb1bb4a5c1a4a`
- 首次改密窗口已取消 400×300 固定尺寸，改为按内容计算最低高度并允许伸缩；macOS 离屏实际渲染为 440×450，所有控件完整可见。
- 已从公网 OSS 实际下载两套安装包，文件大小和 SHA-256 均与 `latest/version.json`、GitHub Release 一致。

## v4.02.29 发布内容

- 默认伊起牛登录，伊起牛与原账号登录均允许安全记住密码。
- 主界面展示版本号并提供手动检查更新入口，强制更新失败时只能重试或退出。
- 显示设置改为紧凑双栏布局，增加稳定预设、主题和实时预览。
- 修复高 DPI 重复缩放；启动更新页通过 100%、125%、150% 缩放渲染验证。

## v4.02.30 紧急修复

- 强制更新、检查失败重试及登录窗口切换期间保持 Qt 应用进程运行。
- 主窗口显示后恢复“关闭最后窗口即退出”的正常桌面行为。
- v4.02.28/v4.02.29 macOS 用户需要手动安装一次 v4.02.30；后续版本可恢复自动强制更新。

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
