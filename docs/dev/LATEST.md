# 当前开发方式

V0.2 讨论稿：Python 3.12、uv 锁文件、Ruff、pytest、统一 run.sh；个人开发使用独立 .venv，公共运行使用明确指定的解释器，不安装依赖。

CI 模式：STANDARD_CI 候选，当前本地 ./run.sh ci；仓库提供手动 GitHub Actions 工作流，是否自动触发与作为合并门由各项目结合配额及权限确认。实际托管运行尚未验证。原生 GPU 科研验收独立于普通 CI。

共享目录权限、正式发布与自动同步尚未实施。见 [CI](CI.md)、[环境](ENVIRONMENT.md)、[服务器](SERVER.md)、[发布](RELEASE.md)。
