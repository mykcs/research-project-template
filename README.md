# Research Project Template

**V0.5 三种仓库形态 · 协商稿**。一个模板支持独立代码仓、独立网站仓和综合项目仓；当前实例为 Python 软件检查示例，没有真实科研结果或网站发布。

Repository profile: code

## 第一次运行（本模板的 Code 示例）

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

## 三种仓库形态 · 同一个模板

| 形态 | 适用范围 | 典型源码布局 |
| --- | --- | --- |
| Code | 独立算法、工具、库或科研实现 | `src/`；不要求网站 |
| Website | 独立网站或 Web 产品 | 默认根 `src/` + 网站构建配置；也允许独立 `website/` 子树 |
| Project | 同一个项目在同仓维护非网站业务代码及附属网站 | `src/` + `website/`（各自依赖、构建和发布） |

**MUST IF（条件必需）**：有现行自有非网站业务代码，就必须放在根 `src/`；有附属网站且仓内另有业务代码，就必须放在 `website/`，网站自身的 `src/` 在其中。纯网站仓的网页源文件应集中于根 `src/` 或 `website/`，不得重复维护两套；网站依赖、框架配置、资源与实际构建根对应。网站存在时记录构建、预览、发布和访问范围；无网站不建空目录。若网站独立分仓，只登记链接和必要接口。

**SHOULD（推荐）**：同一逻辑项目优先使用 Project 形态；确有独立产品生命周期、访问权限、发布边界或维护责任时，可采用独立 Code / Website 仓库，或保持成熟分仓。三种同等合法，选择形态而不是另建模板。README 说明实际范围和构建入口；推荐使用上方 `Repository profile: code`（可改为 `website` 或 `project`）供辅助 audit 读取。纯网站项目按真实网站工具替换本 Python 示例及检查入口，不要求 Python/uv、科研实验或空的科研目录。
- 配置、测试、启动/辅助脚本、文档、获准的外部依赖及不可变历史实验证据可保留其职责目录；不能用这些目录规避现行源码归入 `src/`。旧命令若仍被依赖，只保留轻量委派入口；迁移须验证导入、路径、发布清单和软件回归。

除上述适用的条件必需结构外，既有项目可采用等价结构与工具，不要求照搬其他目录。新项目替换模板信息，填写真实资源、命令、结果、负责人及反馈渠道；验证接手者能从干净 checkout 独立运行。共享环境仅使用管理员认可的固定版本解释器；不安装公共依赖。具体例子见 Dev。
