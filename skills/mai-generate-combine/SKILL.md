---
name: mai-generate-combine
description: 使用 SciPIP 原生文献启发加头脑风暴组合流程，合成并展开候选。
---

## 原生入口
`src/generator.py: IdeaGenerator.generate_ins_bs(detail_background)`。按其原生构造器准备 paper_list、brainstorm、API helper 和 Neo4j 等所需依赖；直接调用函数，不重新编排其内部线程/筛选/展开。
保留 inspirations、initial_ideas、ideas_filtered、final_ideas 各阶段原文。原生函数并不提供完整多父 ID，对可确认的来源做外层关联；无法确认具体来源时标 unresolved，禁止按线程完成顺序猜论文映射。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
- [cheerss/SciPIP @ a0a927a7fa83](https://github.com/cheerss/SciPIP/tree/a0a927a7fa830b4fcf9cb33905feecc005d3b631)；入口 `src/generator.py`。
