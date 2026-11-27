# Dev｜开发、环境、CI、服务器与发布

本文件是当前实现说明；[协作规范](RESEARCH_COLLABORATION_STANDARD.md)是团队建议及交接原则。V0.3 融合候选，未实施管理员控制。原 V0.1/V0.2 细分文件保留于 Git 历史与相应 PR，无需重复维护。

## 环境与资源

Python 3.11–3.13；个人默认 3.12；uv.lock 锁定项目 Python 依赖，外部仿真器、驱动、模型、资产、许可证及系统库分别记录。模板不安装 Isaac Sim/Isaac Lab/MuJoCo。公共底座版本化、任务源码独立、个人 .venv/缓存/实验产出隔离；多模型依赖冲突则分别固定各自环境，复用稳定接口。不复制大型公共平台。公共环境不执行 uv sync、uv run 自动同步或 editable install。--no-deps 并不防止写入环境。维护者建立新环境并验证后切换，保留旧运行版本；必要时再考虑容器、受控 wheel/cache，避免共享可写缓存及未经验证的硬链接。

个人环境用 bootstrap/ci 显式准备；doctor/smoke/audit/lint/test/reproduce 不调用 uv 自动安装。正式运行采用经批准的版本化解释器：

```bash
cd /home/shared/<repository-name>-published/current
RESEARCH_RUNTIME_PYTHON=/absolute/versioned/env/bin/python ./run.sh doctor
```

以上是目标路径示例，不是已部署命令。共享路径可通过 RESEARCH_SHARED_PREFIXES 配置（冒号分隔，默认 /home/shared）；发布清单、只读目录和路径检查防误写，不代替 OS 权限。启动时固定源码和解释器父目录，保留最后一级 Python 链接。真实平台导入、二进制插件、资源、许可和跨账号须另外实测。

| 资源 | 模板 | 实际项目需要记录 |
| --- | --- | --- |
| CPU/RAM/磁盘/时间 | CPU 软件检查 | 最低、推荐、实测及预算 |
| GPU/显存 | 不使用 | 型号、数量、峰值、实时余量 |
| 资产/环境 | 无外部资产 | 版本、哈希、授权和获取方式 |
| 输出 | 个人目录 | 数据、缓存、日志、视频、权重分离 |

## CI

模板为 STANDARD_CI 候选，`./run.sh ci` 执行 uv lock --check、uv sync --locked、doctor、Ruff lint/format、pytest、smoke、辅助 audit。低成本软件验证不是科研验收；audit 不能判断真人交接就绪。CI 不运行 GPU、不访问共享服务器、实机、密钥或部署网站。原生实验按风险与接口合同独立验证，记录准确 commit、运行条件和真实证据。未运行/跳过/取消/旧 SHA 不能称 PASS。

[GitHub Actions](../../.github/workflows/ci.yml) 目前仅手动触发；尚未执行托管验证。依赖固定 commit、最小只读权限、超时和取消过期运行。组织 CI 属于团队公共预算（并非无限），高频迭代优先个人资源，本地通过后再使用组织 CI 验收。默认不自动部署公网服务、Pages，不上传私有模型/数据/凭据，不使用科研服务器作为通用 Runner。第三方 CI 和付费资源由授权维护者确认隐私、配额和预算后才启用。自动 PR 触发、主分支保护等由团队确定。其他项目允许等价 CI，实际检查、成本、权限与状态必须可发现。

## 服务器协作、发布与回滚

个人 $HOME/<repository-name> 从组织 main clone，功能分支→检查→PR→按风险审阅→合并。普通成员不改他人工作区、公共环境、共享发布或系统配置；当前以自觉约定为主，不新增权限控制，也不收回既有权限。旧共享目录不覆盖。管理员在达成共识后将 /home/shared/<repo>-published 及公共环境设置普通成员读/执行、维护者受控写，最小权限并保留回滚。

发布与 Git merge 分开确认：从准确 main commit 创建独立 releases/<version>，记录环境、资产、源码、验证证据及发布者；确认候选后原子切换 current。运行固定实际版本，不在现役 current 内 git pull。回滚切换至已验证旧版本；清理须核对运行引用及科研保留。发布维护者、ACL、自动同步仍待协商，不宣称已实施。

可选 RELEASE_MANIFEST.json 使用 schema_version: 1、完整 40/64 位 Git hash source_commit、可选 release_version；只读解析并记录清单 SHA-256。清单仅声明来源，不能验证发布树内容；真正发布需独立核对快照、环境及签名/哈希等证据。跨仓集成固定已验证 commit 或版本，使用 submodule/锁定依赖等可复现方式；交付包说明包含/排除、外部资产及获取许可，不能把静态存在当作复现通过。

## 参考与变更理由

统一入口使新人能独立复现；低成本检查与原生科研验收分层。隔离共享依赖、显式准备、版本化发布、最小权限和按需文档保持低维护成本。参考 [uv](https://docs.astral.sh/uv/concepts/projects/sync/) 与 [Isaac Lab](https://docs.nvidia.com/isaaclab/3.0/developer-tools/build-your-own-project-or-task)。设计迭代及历史见 Git PR #1–#4 与本融合候选。没有容器化或固定 CI 厂商要求。
