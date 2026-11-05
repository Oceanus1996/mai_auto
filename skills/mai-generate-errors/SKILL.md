---
name: mai-generate-errors
description: 使用 HypoGeniC 原生错例驱动假设更新，适用于有可信标签或判定器的任务。
---

## 原生入口
`hypogenic/algorithm/update/default.py: DefaultUpdate.update`，通过原生 pipeline 构造 generation/inference/replacement 组件、训练数据与 hypotheses_bank。
只接受带可信标签/判据的预测错误。没有标签、只有 reviewer 意见或代码运行失败时标 blocked。保留样本索引、假设统计、更新前后 JSON 快照；原算法的触发阈值不要求所有假设同时出错，不自行改成全票错误。
研究问题无法表达成原生预测任务时说明不适用，不把一般反思当作 HypoGeniC。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
- [ChicagoHAI/hypothesis-generation @ bd37a3129a2f](https://github.com/ChicagoHAI/hypothesis-generation/tree/bd37a3129a2f98ee586f545a57b10b59496eedad)；入口 `hypogenic/algorithm/update/default.py`。
