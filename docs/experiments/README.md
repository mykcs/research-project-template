# Experiments｜证据与复现

当前无真实科研实验。Run ID、commit、环境/资产版本、输入配置、种子（适用时）、命令、真实指标、资源峰值、耗时、终止条件、结果与失败原因应可追溯。输出保存在个人/指定实验区，原始证据不覆盖。区分 Mock、CPU、MuJoCo、PhysX、实机；导航规划不等于自主行走、抓取不等于持箱行走，连续任务不得拼接不同 episode 冒充成功。

`./run.sh smoke` 的 JSON 记录配置 SHA-256、Run ID、时间、验证范围和 Git 身份；无可确认来源记 UNKNOWN，发布清单只是声明，`source_integrity=NOT_VERIFIED`。`scientific_result=NOT_TESTED` 不会因软件检查改变。

## 可选外部资产契约

可信 TOML 输入可用 schema_version=1，多个 [[assets]] 分别声明 name、path（相对清单或绝对路径）、sha256（64 位十六进制）。显式提供 `./run.sh doctor --asset-manifest /path/to/assets.toml` 后流式读取校验，缺失/不符非零退出；资产校验不是使用许可或科学成功。不要默认下载或上传资产。

`--receipt-out /absolute/personal-output/new.json` 仅创建新文件，父目录须预先存在，拒绝覆盖、共享运行 checkout 和配置共享前缀。个人 checkout 内仅允许 outputs/ 或 runs/。这是防误操作，不能替代服务器 ACL。audit 只是辅助检查，交接必须由真人独立验收。

对照实验记录模型/checkpoint、数据版本、任务初态、种子、最大步数、指标、评分协议，快速抽样与完整 benchmark 分开。转换数据由原生消费者重读检查关键字段及边界。训练→评估→部署核对同一 checkpoint；短跑证明流程不证明模型效果。在线决策与固定回放、历史证据与本次重跑明确分开。研究项目按需使用 [Research](../research/README.md)。
