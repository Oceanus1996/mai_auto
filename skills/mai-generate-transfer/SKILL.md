---
name: mai-generate-transfer
description: 调用 SciMON/CLBD 原生检索启发与相似度迭代流程，探索从已有研究迁移机制的候选。
---

## 原生入口
`models/GPTRetr/fewshot3.py`、`models/Iterative/calculate_sim.py`、`models/Iterative/gpt4_iter1.py` 是有数据和路径约束的实验脚本，不是通用 idea API。先按 README 准备原生数据格式、检索模型与运行环境，使用隔离工作目录运行原脚本。
检查到的原生流程有硬编码路径/模型等约束；无法以纯配置接入时标 blocked，提出最小补丁供明确选择，不能重新实现算法。固定语料相似度不是全球新颖性证明。仅在原生结果实际产生后登记候选。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
- [EagleW/CLBD @ 2dc17a1e2e22](https://github.com/EagleW/CLBD/tree/2dc17a1e2e22c22a6b595c212d3bbeca2b0dd89e)；入口 `models/Iterative/gpt4_iter1.py`。
