# 环境与隔离

## 当前阶段

不修改现有公共环境。现有依赖由团队按实际情况登记；本模板仅含可独立运行的软件检查，未安装 Isaac Sim、Isaac Lab、MuJoCo。需记录 Python、仿真器、驱动、资产及外部平台版本，许可证、兼容性和真实验证。

## 拟议三层环境

公共仿真底座使用版本化目录，由指定维护者统一提供与更新；大型仿真平台及资产优先只读复用。具体路径、容量和版本由管理员确认。各科研任务保留独立源码、pyproject.toml、uv.lock 和配置；Isaac Lab 可参考官方 External Project Generator，避免复制底层平台。开发者在个人工作区使用独立 .venv、实验输出及缓存。

公共环境不执行 `uv sync`、`uv run` 自动同步或 `uv pip install --no-deps -e .`。--no-deps 并不禁止写入目标环境。可编辑安装必须写入个人环境。uv.lock 锁定项目 Python 依赖，不自动锁定驱动、外部平台、模型、资产或系统库。

正式运行采用明确的版本化公共解释器，通过 RESEARCH_RUNTIME_PYTHON 指定；run.sh 在此模式中只执行 doctor、smoke、reproduce，不调用 uv，不生成字节码缓存。它将本项目 src 作为导入入口；真实项目若需要任务注册、二进制插件或额外依赖，需先验证该机制，必要时由维护者建立隔离项目运行环境，不能临时写入公共环境解决。运行时不能继承可变 current 环境入口；具体解释器必须固定到实际版本。

个人开发优先复用经验证的软件包缓存或 wheel 下载仓库；文件系统支持时评估写时复制。不默认共用可写缓存或将个人 .venv 链接到公共环境。启动器的路径检查仅是防误操作，不是操作系统权限边界。

## 更新与演进

公共环境变更采用新版本，经过环境导入、CPU/GPU 及真实代表性实验验证后由维护者发布；旧实验仍固定其原版本。个人日志、缓存、视频和训练结果独立保存。团队扩大或依赖冲突时再评估 Docker / Apptainer，不强制提前迁移。

参考：[Isaac Lab 外部项目生成](https://docs.nvidia.com/isaaclab/3.0/developer-tools/build-your-own-project-or-task)、[uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)。
