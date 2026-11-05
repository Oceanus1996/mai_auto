---
name: mai-generate-directions
description: 使用 HKUDS AI-Researcher 原生 idea agent 形成多方向结构化研究提案。
---

## 原生入口
`research_agent/inno/agents/inno_agent/idea_agent.py: get_idea_agent` 是 agent 工厂，不是生成完成的函数。使用该仓库原生运行器与 environment/工具装配执行它；仅成功构造 Agent 不能标记生成完成。
提供原生 context_variables 与调研文件。保留工具轨迹和提案输出；原生 agent 名称不能当全局唯一 ID，外层另设 agent_id/task_id。不要用普通 chat 调用替代原生工具循环。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
- [HKUDS/AI-Researcher @ f9a6f8480860](https://github.com/HKUDS/AI-Researcher/tree/f9a6f8480860c193afff600eeffe3defcee8a978)；入口 `research_agent/inno/agents/inno_agent/idea_agent.py`。
