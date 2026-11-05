---
name: mai-generate-batch
description: 使用 Stanford AI-Researcher 原生批量候选生成与去重逻辑，为研究问题扩大候选覆盖。
---

## 原生入口
`ai_researcher/src/grounded_idea_gen.py: idea_generation`；CLI 参数以该脚本 --help 为准。输入原生 paper_bank、existing_ideas、examples、生成参数与原生 SDK client。该函数返回 prompt/response/cost，保留后解析 JSON。
去重使用 `dedup_ideas.py` 原有流程，提前准备其所需相似度矩阵。另保留未去重产物及被排除映射，不改变原排序规则。上游 AI/NLP 最佳论文偏好保持并记录；用户未授权不得改写为安全领域提示。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
- [NoviScl/AI-Researcher @ e5dd05a90bca](https://github.com/NoviScl/AI-Researcher/tree/e5dd05a90bcadb436c07283c2f429367c6e525d3)；入口 `ai_researcher/src/grounded_idea_gen.py`。
