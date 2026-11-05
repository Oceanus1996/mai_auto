# 按接口调用环境设置 agent

每个原生 job 在运行前检查源码提交、解释器和所需导入。运行器优先使用 job.python，再使用 `.environments/<upstream>/ready.json`，最后尝试宿主 Python。缺失时保存 environment-request.json，返回 blocked_environment。已有环境通过检查即可复用，不每轮重装。

宿主协调器应自动把请求交给 `mai-setup-environment`：查看固定版本安装说明、配置隔离环境、验证后登记 ready.json，再恢复原阶段。环境 agent 是宿主的执行角色/子 agent，不是裸模型 API 自带的能力；Python CLI 本身不会凭空启动未配置的 LLM agent。无人值守 CLI 使用时需有宿主处理该请求，否则仍会等待。这是明确的执行边界。

## 自动处理与需要外部输入的边界

- 缺源码或 Python 包：设置 agent 按上游安装说明处理。
- 浏览器/系统工具：在可用环境中安装并验证，记录实际结果。
- 模型端点：检查指定本地服务或显式 API 配置，不静默换云模型。
- 没有 API 凭据、宿主无法访问 Windows/Unity：报告具体外部缺项。
- 根本没有实现的接口、空的实验检查 worker：交回实现 agent 补接口，不能说装依赖即可解决。

初始登记只代表解释器与相应导入可用；模型、数据和实际实验要分别验证。不能把设置环境的成功计入科研结论。

## 配置与产物

环境路径和机器相关记录保存在被 Git 忽略的 `.environments/`；上游保持固定 SHA。每个 job 的 runs/<id>/environment.json 记录当次实际解释器和导入结果，失败时有 environment-request.json、environment-check.log。

一个相同上游的环境可服务多个 adapter，但每个 adapter 单独检测需要的模块。运行器不执行任意自动安装命令；设置 agent 根据源码依据执行部署，避免把模型臆造的依赖清单当作真实安装方式。

恢复入口沿用 `python -m mai_auto.cli loop CONFIG --resume RUN --retry`，仅在环境准备完成、确认未重复执行副作用后使用。novelty 的人工门禁不会被此重试绕过。
