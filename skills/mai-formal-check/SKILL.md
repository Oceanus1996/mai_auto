---
name: mai-formal-check
description: 在最小验证获得初步支持后，复用 Curie、HKUDS 和 NeuriCo 完成正式实验准备、实现检查及核验。
---

## 原生分工
Curie `curie/scheduler.py: SchedNode.update_queues` 管理控制组完成后派发实验分区；它的 done 不等于科学有效，另保存 baseline_check 证据，不改原始 done 含义。
HKUDS `research_agent/inno/agents/inno_agent/judge_agent.py` 的 get_judge_agent/get_code_review_agent 检查 idea 与实现是否对应，保留原生 fully_correct/suggestion，但不把该布尔值当作证明。
NeuriCo `src/agents/eval_verifier.py: run_eval_verifier` 核查评价契约。原后端有云 API 要求，未完成本地传输适配时明确 blocked，禁止静默调用云服务。
Arbor 现有执行树承载少量实现搜索；在可靠评测器出现以前不额外加入程序进化算法。
## 最后核验
绑定输入、代码提交、环境、seed、原始产物，运行已有测试和指标重算；按任务选择统计检查或形式化验证器。记录所用工具、范围及失败。模型的解释单独保存，不是核验结果。此组合层不提供新的通用判定算法。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
- [Just-Curieous/Curie @ db1b1f56159b](https://github.com/Just-Curieous/Curie/tree/db1b1f56159b591515f77e03c55bf473d5c1c201)；入口 `curie/scheduler.py`。
- [HKUDS/AI-Researcher @ f9a6f8480860](https://github.com/HKUDS/AI-Researcher/tree/f9a6f8480860c193afff600eeffe3defcee8a978)；入口 `research_agent/inno/agents/inno_agent/idea_agent.py`。
- [ChicagoHAI/NeuriCo @ 8170d6d0d922](https://github.com/ChicagoHAI/NeuriCo/tree/8170d6d0d9221f5495bc34e67de1b1b86873699a)；入口 `src/agents/eval_verifier.py`。
- [RUC-NLPIR/Arbor @ 7cdaf1fa6d77](https://github.com/RUC-NLPIR/Arbor/tree/7cdaf1fa6d779b3d5e340052357bf3fe55dfed93)；入口 `src/coordinator/idea_tree.py`。
