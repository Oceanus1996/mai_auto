---
name: mai-minimum-check
description: 用已有执行器对一个 idea 关键假设做最小实际验证，在完整基线复现前快速决定继续或修订。
---

## 原生入口与边界
沿 Arbor 原生 coordinator/executor 的任务执行接口提交小型验证任务，读取 `src/coordinator/tools/executor_run.py` 及现有 executor CLI 的参数后执行。不得用模型口头模拟实验结果。此 skill 只缩小任务范围/预算，不改 executor 算法；实际进入完整工作流所需环境仍应列出。
先固定单个主张、预期观察、判据、输入样例、预算和原始产物位置。比较性主张需要最小对照，其他主张不强制完整论文基线。确认代码实现所测机制；记录失败是实现错误还是反例。
输出 supported/refuted/inconclusive/invalid_execution，注明适用样例范围。supported 仅表示本轮初步支持。没有可执行工具或可信判据时 blocked；不创建假日志或假分数。未提供通用领域自动判定器，需按任务装配已有测试/求解工具。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
- [RUC-NLPIR/Arbor @ 7cdaf1fa6d77](https://github.com/RUC-NLPIR/Arbor/tree/7cdaf1fa6d779b3d5e340052357bf3fe55dfed93)；入口 `src/coordinator/idea_tree.py`。
