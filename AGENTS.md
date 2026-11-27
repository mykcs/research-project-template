# 项目协作规则

先读 README、Task MAIN/CURRENT、Dev LATEST、CI 及相关 Design。正式源码放 src，配置放 configs，脚本放 scripts，测试放 tests。复用已有接口，不堆临时文件，不提交密钥、缓存和未经许可资产。只修改授权个人工作区，不修改共享 published 目录、公共环境、其他成员工作区或服务器权限。

项目变更须执行 ./run.sh ci；记录实际 commit 与检查结果。原生仿真独立验收，不降低科研门槛，不以 Mock、CPU CI、视频拼接冒充物理成功。CI 只运行声明的低成本软件检查，不用共享科研 GPU 充当通用 runner。未验证的结果标记未验证。

公共运行环境不执行 uv sync 或 editable install。任何权限、公共环境、发布机制变更由有权维护者按团队共识执行。AI 重要贡献记录实际工具、模型和验证依据，未知不猜测。
