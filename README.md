# Research Project Template

**V0.2 · 团队协商稿**。这是可运行的科研项目起点，不包含机器人算法或真实实验结果。

## 个人开发

在个人工作区 clone 仓库；Python 3.12 和 uv 已安装：

```bash
cd "$HOME/research-project-template"
./run.sh doctor
./run.sh ci
```

`./run.sh smoke` 是软件冒烟检查；`./run.sh reproduce` 在真实实验未配置时明确失败。

## 正式版本运行

团队协商并完成发布后，从正式版本入口运行。启动器支持通过 `RESEARCH_RUNTIME_PYTHON` 指定经验证的版本化公共环境解释器；此模式不会调用 uv 安装或同步依赖。具体部署路径、环境版本、运行命令由各项目在交接前实测并写入 README。见 [环境](docs/dev/ENVIRONMENT.md) 和 [服务器](docs/dev/SERVER.md)。

## 交接入口

[Task](docs/task/README.md) · [Dev](docs/dev/README.md) · [Design](docs/design/README.md) · [Wish](docs/wish/README.md) · [Experiments](docs/experiments/README.md)

实例化后填写项目目标、上游关系、当前真实进展、资源、已验证运行命令、成果证据、维护者和问题反馈方式。接手者独立运行检查、理解现状、在个人分支修改测试并提交 PR。

本版本没有配置正式仿真环境、原生 GPU 实验或服务器发布；权限和自动同步暂为团队讨论事项。
