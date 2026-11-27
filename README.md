# Research Project Template

**V0.1 · 讨论稿**。这是可运行的科研代码起点，不包含机器人算法或真实实验结果。

## 快速开始

在个人工作区 clone 仓库，进入仓库根目录；需要 Python 3.12 和 uv：

```bash
cd "$HOME/research-project-template"
./run.sh doctor
./run.sh smoke
./run.sh ci
```

`reproduce` 在真实实验尚未注册时明确失败。模板 smoke 不代表科研成功。

## 文档导航

[Task](docs/task/README.md) · [Dev](docs/dev/README.md) · [Design](docs/design/README.md) · [Wish](docs/wish/README.md) · [Experiments](docs/experiments/README.md)

新项目需填写目标、上游关系、当前真实进展、实验资源、运行命令、成果证据、维护者和交接方式。接手者独立运行检查、定位已有成果、在个人分支修改测试，再提交 PR。默认不启动 GPU 或实机。
