# Research Project Template｜独立设计审查与 V0.3 改进方案

基于 `template/v0.2`（[PR #2](https://github.com/mykcs/research-project-template/pull/2)）的独立架构审查与工程实现。本分支不覆盖已有贡献，保留 V0.1/V0.2 全部核心安全边界与向后兼容性，聚焦解决过度文档化、机器人共享环境兼容性、发布清单溯源、外部资产校验与可执行交接检查等关键短板。

## 1. 发现了哪些问题（针对 V0.2 候选）

1. **文档严重过度设计，与原始 Intent 矛盾**：`template/v0.2` 仅有约 100 行 Python 源码，却包含 **27 个 Markdown 文件**（`docs/` 下 5 个子目录共 24 个文件）。ETH Zurich 实证研究 [Evaluating AGENTS.md (arXiv:2602.11988)](https://arxiv.org/html/2602.11988v1) 表明，冗余仓库上下文文件会使 Coding Agent 推理成本上升 >20% 且可能降低成功率；极简人工规范才最有效。
2. **Python 3.12 硬编码锁死**：`doctor` 硬编码 `sys.version_info[:2] == (3, 12)` 且 `pyproject.toml` 锁死 `>=3.12,<3.13`，导致 Isaac Sim / ROS 2 等 Python 3.11 共享仿真解释器直接 `FAIL`。
3. **共享隔离仅硬编码 `/home/shared/*`**：换到 `/opt/shared`、`/srv/releases` 或只读挂载目录时防护失效。
4. **收据无落盘隔离参数且未读取发布清单**：文档要求发布快照使用清单、收据写入个人目录，但代码未提供 `RELEASE_MANIFEST.json` 只读解析或带写保护的 `--receipt-out`。
5. **缺少可执行交接审计、外部资产校验与 PR 协作模板**：交接检查停留在纯手工 Markdown 表格，缺少 URDF/USD/权重 SHA-256 校验契约与 `.github/pull_request_template.md`。

## 2. 借鉴了哪些成熟实践
- [Evaluating AGENTS.md (arXiv:2602.11988)](https://arxiv.org/html/2602.11988v1)（极简 Agent 上下文）
- [Cookiecutter Data Science v2](https://cookiecutter-data-science.drivendata.org/) & [Modern Lightning-Hydra Template](https://github.com/cauliyang/cookiecutter-modern-lightning-hydra-template)（低摩擦结构与配置驱动实验）
- [ROS 2 Best Practices (Henki Robotics)](https://henkirobotics.com/ros-2-best-practices/) & [GitHub Blog: Reviewing Agent PRs](https://github.blog/ai-and-ml/generative-ai/agent-pull-requests-are-everywhere-heres-how-to-review-them/)（接口契约与 PR 审阅门禁）
- 注：访问 `AINet-CruelAngel` 组织返回 `PERMISSION_DENIED`，仅沿用 PR #2 正文中的通用工程边界摘要。

## 3. 建议的文档收敛方案（27 份 -> 4 份）
建议团队评审通过后将现有 27 份 Markdown 收敛为：`README.md`（60 秒启动入口）、`HANDOFF.md`（合并 `docs/task/` 7 份）、`docs/ENGINEERING.md`（合并 `docs/dev/` 10 份 + 接口与实验规范）、`AGENTS.md`（极简硬边界）。

## 4. 真实测试与未验证项
- **已执行**：离线 Linux 沙箱（Python 3.11.2，Bash 5.2.15）下 `bash -n run.sh`、`py_compile`、`RESEARCH_RUNTIME_PYTHON=$(which python3) ./run.sh doctor|smoke|audit|reproduce` 及全部 **20/20** 项单元测试（V0.2 原有 14 项 + 新增 6 项）均通过。
- **未验证**：离线环境未运行 `uv lock --check`、`uv sync --locked`、`ruff`、GitHub Actions 托管 CI 或任何 GPU/原生仿真/实机验证（`scientific_result: NOT_TESTED`）。

## 5. AI Provenance
- Orchestrator: `Unknown` | Harness: `Gemini` | Harness Version: `Unknown` | Mode: `Task Mode`
- Model Provider: `Google` | Model Family: `Gemini` | Selected Model / Variant / Snapshot: `Unknown` | Reasoning Effort: `Unknown`
- Contribution Role: `Independent Architecture Review & Implementation`
