# AGENTS.md

先读 README、当前 Task、适用 Dev/Design/Experiments；科研问题再按需读 Research。优先复用已有接口和工具；不要为规范创建空壳或强制迁移成熟结构。

- 个人开发积极利用 Agent；多人协作提交前理解 diff、检查测试及影响，合并前按风险审阅。
- `./run.sh ci` 显式准备个人环境并检查；doctor/smoke/audit 不安装。共享运行仅指定获准解释器，不写共享源码/环境、他人工作区或权限。
- 不抢占他人计算资源；不擅自启动未授权 GPU/实机、付费 CI、公开部署或共享资源变更。
- 实验与软件检查分层；不可用 Mock、回放、CI 或拼接视频冒充科研成功。未测试标 NOT_TESTED；audit 不等于真人交接。
- 不提交密钥、.venv、未经许可资产及个人实验产物；合法项目资产按实际授权管理。
- 真实测试、接口兼容和重要 AI 贡献须有可追溯证据，未知不猜。协作规范为 [Dev 标准](docs/dev/RESEARCH_COLLABORATION_STANDARD.md)。
