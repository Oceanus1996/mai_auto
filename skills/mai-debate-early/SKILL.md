---
name: mai-debate-early
description: 使用 AutoResearchClaw 原生多角色 debate、judge、synthesizer，在最小验证前讨论候选机制与关键假设。
---

## 原生入口
`researchclaw/pipeline/debate.py: run_debate`；角色来自 `PromptManager.debate_roles_hypothesis()`，综合模板使用 hypothesis_synthesize。已封装 claw_debate：input.variables 为 topic/synthesis，rounds 默认 1（这是组合层配置，须记录）。原有 rebuttal prompt 和上一轮快照保持不变。
保留角色每轮 markdown 和 debate_record.json。当前便捷适配使用同一模型不同角色，必须标记 model_independence=false；配置多个原生 clients 时仍用上游 run_debate。
将批评对应到主张/证据/待执行检查作为单独附加标注，不修改原文。没有证据的共识不能成为通过标准；judge 失败后的上游回退必须如实记录。分歧可保留为 Arbor 兄弟分支。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
- [aiming-lab/AutoResearchClaw @ be4ba4755bf1](https://github.com/aiming-lab/AutoResearchClaw/tree/be4ba4755bf1b52220f25e13b2293b5956590070)；入口 `researchclaw/pipeline/debate.py`。
