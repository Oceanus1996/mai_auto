---
name: mai-research
description: 编排 Arbor 自动研究工作流，适用于从研究问题到文献综述、并行构思、双阶段讨论和最小验证的个人研究任务。
---

## 顺序
1. 记录研究目标、资源和阶段预算；检查宿主可运行进程、模型配置与上游环境。
2. 调用 mai-literature 精读并综合证据，同时调用 mai-tech-chain 独立维护技术演化链；固定综述与链快照。
3. 将同一背景包交给 mai-generate-batch、mai-generate-directions、mai-generate-chain、mai-generate-transfer、mai-generate-combine、mai-generate-retrieval。无依赖部分可并行，SciPIP 只接收原生 paper_list/brainstorm，不擅自添加跨候选合成算法；仅对能够确认的来源登记辅助关系。mai-generate-errors 等待有效错例。
4. 调用 mai-debate-early；保留分歧，不将共识当正确性。原生结果到共享主张记录的对应只是附加标注，不改原始辩论内容。
5. 由协调器用 Arbor 原生 Node/IdeaTree 入树。重复方案标注、不删除；合成选主父节点，辅助来源单独记录。新增假设子节点，不覆盖旧假设。
6. 调用 mai-minimum-check。先验证一个关键机制，再决定是否修订、分叉或投入完整实验。此时不强制复现完整基线；比较性主张仍需最小对照。
7. 有初步支持后调用 mai-review-late，随后调用 mai-formal-check 做正式实验计划、控制组检查、有限实现搜索与结果核验。
8. 将有效反例送 mai-generate-errors；执行错误送实现修复，不把报错当假设证伪。停止时汇报已完成/blocked/未执行和原始证据。

## 调用和存储
同级 `mai-*/SKILL.md` 是具体技能入口，按需读入；每个目录都可被宿主注册为独立 skill。安装时保留整个 skills 集合与仓库运行资源，或者显式提供 MAI_ROOT。
通过 `python -m mai_auto.cli run JOB.json` 调用已实现原生适配器；通过 `batch JOBS.json --workers 2` 隔离运行多个任务。未封装的入口按该 skill 的原生指引在独立环境运行，不伪装为已经一键接入。
Arbor tree 是研究结构；文学链用独立 sqlite；记录文件不自动宣告科研成功。详见 contracts.md。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
参照同级具体技能和根目录 upstreams.lock.json。
