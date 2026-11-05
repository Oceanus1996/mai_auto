---
name: mai-generate-chain
description: 从 CoI-Agent 原生论文研究链提出研究缺口和新 idea，读取独立技术链快照作为证据。
---

## 原生入口
`agents.py: DeepResearchAgent.generate_idea_with_chain`，已封装为 coi_chain。输入 topic 和可选 anchor_paper_path；设置保持原生默认，预算调整单独记录。
将生成的 idea、experiments、entities、chain 等所有原始输出保留。将文献链快照 ID 写入附加来源记录；不得直接编辑 mai-tech-chain 的数据库。该入口会自身检索，保留新增资料，不声称所有策略收到完全相同资料。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
- [DAMO-NLP-SG/CoI-Agent @ ac94317ff2d1](https://github.com/DAMO-NLP-SG/CoI-Agent/tree/ac94317ff2d1997f362747edc2c9e5f0fdc9c450)；入口 `agents.py`。
