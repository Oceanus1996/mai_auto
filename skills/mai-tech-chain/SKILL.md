---
name: mai-tech-chain
description: 独立维护基于引用关系的技术演化链，追踪技术继承、变化、限制及原文依据，不修改 Arbor 研究树。
---

## 原生路径
调用 `agents.py: DeepResearchAgent.generate_idea_with_chain`；底层 `deep_research_paper_with_chain` 输出 deep_research_chains.json 等记录。已封装入口 coi_chain，输入是原生 arguments 与 settings。
保留整份原始链，即使它同时产生 ideas；不要将它的 idea 自动加入 Arbor。链生成和 idea 生成角色即使使用同一个类，也必须使用不同 task_id/save_file。
## 独立链记录
把原生结果对应到论文与关系，使用独立 literature.sqlite。引用关系与技术演化判断分开：引用边须有参考文献依据；演化边须保存原文位置或明确 inference/unknown。原生结果缺 DOI/论文 ID 时不得编造，保留题名及未解析状态。
快照用内容哈希标识。链更新只能发出待复查事件，不重写已有 idea 的 grounding。支持分叉/汇合，阅读界面展示选定路径。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
- [DAMO-NLP-SG/CoI-Agent @ ac94317ff2d1](https://github.com/DAMO-NLP-SG/CoI-Agent/tree/ac94317ff2d1997f362747edc2c9e5f0fdc9c450)；入口 `agents.py`。
