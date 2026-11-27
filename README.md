# Research Project Template

**V0.3 融合候选 · 协商稿**。支持工程交接与科研探索的可运行模板。当前没有真实机器人算法、仿真结果或公共发布。

## 第一次运行

进入本人 clone 的目录（任意目录名），准备 Python 3.11–3.13、uv；默认开发版本 3.12。

```bash
./run.sh ci
```

在个人工作区显式准备锁定环境并执行软件检查；不运行 GPU 或真实机器人。以后 `./run.sh doctor`、`./run.sh smoke`、`./run.sh audit` 不安装依赖。首次环境未准备时提示 bootstrap/ci。更多命令：`./run.sh --help`。

doctor/smoke 可选 `--asset-manifest` 校验可信输入的 SHA-256，`--receipt-out` 写入一个不存在的新收据文件，父目录须为已有个人输出目录。audit 是辅助检查，不证明交接通过；reproduce 在尚无真实科研实验时返回非零。

## 导航

- [Task 与交接](docs/task/README.md)：上游、主线、现状与验收；[交接清单](docs/task/HANDOFF.md)。
- [Dev](docs/dev/README.md)：依赖、CI、资源、共享环境与发布。
- [Design](docs/design/README.md)：接口、架构、决策；[Wish](docs/wish/README.md)：原始意图及未立项目标。
- [Experiments](docs/experiments/README.md)：真实证据与复现；[Research（科研项目按需）](docs/research/README.md)：研究问题、假设、基线、实验协议及发现。
- [团队协作规范](docs/dev/RESEARCH_COLLABORATION_STANDARD.md)：必需、条件必需、推荐与可选。

既有项目可采用等价结构与工具，不要求照搬目录。新项目替换模板信息，填写真实资源、命令、结果、负责人及反馈渠道；验证接手者能从干净 checkout 独立运行。共享环境仅使用管理员认可的固定版本解释器；不安装公共依赖。具体例子见 Dev。
