# 项目续接规则

开始处理本项目时，先完整阅读 `PROJECT_STATUS.md`，再检查 `git status`、当前分支和最近的 GitHub Actions。

- 认证客户端只能通过 `https://api.genepop.com` 调用认证服务；不得恢复数据库直连，不得把数据库密码、AccessKey、Token 或 JWT Secret 写进代码、文档、日志和 Git 历史。
- 应用版本以根目录 `VERSION` 为唯一发布版本；发布标签必须严格等于 `v$(cat VERSION)`。
- 发布前运行单元测试、凭据模式扫描和双平台 GitHub Actions。只有 Windows、macOS 安装包均成功后，才允许更新 OSS `latest/version.json`。
- OSS 发布账号只能拥有 `genetic-improve/tools/dhi-screening/*` 前缀的对象读写权限。
- 保留用户在原工作区的未提交文件，不使用 `git add -A`，不覆盖与当前任务无关的软著或需求材料。
