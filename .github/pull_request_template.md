## 变更目标与影响范围
- 解决的问题 / 关联任务：
- 是否修改共享接口、配置 schema 或公共启动器（是 / 否）：

## 验证证据（严格区分验证层级）
- [ ] 本地软件检查：`./run.sh ci`（或说明实际执行的命令与结果）
- [ ] 真实仿真 / 实机验证（适用时填写后端、checkpoint、资产版本、运行收据；未执行请明确标 `NOT_TESTED`）：
  - `validation_scope`: `SOFTWARE_ONLY` / `NATIVE_SIM` / `REAL_ROBOT`
  - `scientific_result`: `NOT_TESTED` / `PASS` / `FAIL`

## 协作与安全边界自查
- [ ] 未修改共享发布目录、公共环境、他人工作区或服务器权限
- [ ] 未提交 `.venv`、权重（`.pt/.pth/.onnx`）、数据包（`.bag/.mcap/.usd`）或临时输出
- [ ] 提交者已亲自审阅 diff、测试结果及对其他成员的影响

## AI Provenance（适用时填写，未知项填 `Unknown`，不猜测）
- Orchestrator / Harness:
- Model Provider / Family / Version:
- Reasoning Effort:
- Contribution Role:
- Verification Basis:
