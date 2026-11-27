# Research Project Template

**V0.3 · 独立改进候选**。可运行的科研项目起点，不包含机器人算法或真实实验结果。

## 个人开发：第一次使用

从 Git clone 到自己的目录，进入仓库根目录（不要求目录名与模板相同）。安装 Python 3.12 和 uv 后，执行：

```bash
./run.sh ci
```

这条命令在个人目录创建/同步锁定环境，并运行软件验证。预期：锁文件、Ruff、pytest、doctor 和软件 smoke 通过；不会启动 GPU、仿真器或实机。

以后日常使用：

```bash
./run.sh doctor
./run.sh smoke
```

这两个命令不会安装或升级依赖。首次使用尚未准备环境时，doctor 会明确提示执行 `./run.sh bootstrap`（只准备依赖）或 `./run.sh ci`。其他命令通过 `./run.sh --help` 发现。

smoke 输出带配置指纹、验证范围和 Git 身份（可确认时）的 JSON 收据；`./run.sh reproduce` 在真实科研实验未配置时明确失败。软件检查不等于科研成功。

## 正式版本运行

团队协商并完成发布后，从正式版本入口运行。启动器支持通过 `RESEARCH_RUNTIME_PYTHON` 指定经验证的版本化公共环境解释器；此模式不会调用 uv 安装或同步依赖，启动时解析环境父目录的真实路径，同时保留 Python 自身的虚拟环境解释器链接。具体部署路径、环境版本、运行命令由各项目在交接前实测并写入 README。见 [环境](docs/dev/ENVIRONMENT.md) 和 [服务器](docs/dev/SERVER.md)。

## 交接入口

模板目录与工具是推荐实现，不是强制格式。必需的是交接信息、可运行能力、安全及验证证据；可沿用项目现有文档和等价工具。参考资料库、Wish、独立 ADR 等可按需要省略。详见 [规范分级](docs/dev/RESEARCH_COLLABORATION_STANDARD.md) 和 [交接验收](docs/task/HANDOFF.md)。

[Task](docs/task/README.md) · [Dev](docs/dev/README.md) · [Design](docs/design/README.md) · [Wish](docs/wish/README.md) · [Experiments](docs/experiments/README.md)

将模板用于实际项目时，替换示例目标和配置，填写项目真实入口、现状、资源、证据与维护者；README 的首次运行命令应由接手者在干净个人 checkout 独立验证。无需重写已有有效目录结构。

本版本没有配置正式仿真环境、原生 GPU 实验或服务器发布；权限和自动同步暂为团队讨论事项。
