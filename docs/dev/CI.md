# CI

CI_NONE：当前无托管 CI。提交前执行 ./run.sh ci（锁文件、Ruff、格式、pytest、smoke），记录实际 commit 与结果。未执行不得称 PASS。原生 GPU 物理实验独立验收。
