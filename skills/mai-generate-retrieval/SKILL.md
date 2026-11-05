---
name: mai-generate-retrieval
description: 使用 Nova 原生检索计划与候选迭代入口，引入不同检索方向的研究材料。
---

## 原生入口
`src/plan_and_iteration.py: IdeaRelatedPaperPlanThenRetrievalAgent.run`；`vo/idea_data.py: IdeaResult` 保存来源和思考字段。依原生配置提供 args 和学术搜索服务，保存 search_plan_result_list、top1_document、排序结果及 prompt。
该 run 主要返回检索资料，不等于生成完整 idea；需要 idea 时继续使用仓库 `agent/new_idea_iteration_agent.py` 的原生迭代入口，先核实签名。不得自行添加一个“读资料想 idea”的提示词冒充 Nova。原代码未实现的自适应搜索迭代不得宣称已开启。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
- [hflyzju/Nova @ 94bdc7590aac](https://github.com/hflyzju/Nova/tree/94bdc7590aac160838bfb7895f9e1dc882b233ab)；入口 `src/plan_and_iteration.py`。
