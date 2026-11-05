---
name: mai-literature
description: 获取、精读和综合研究文献，形成带证据的技术路线综述后再生成研究 idea。
---

## 原生路径
使用 Stanford `ai_researcher/src/lit_review.py: collect_papers` 获取并保存 paper_bank。用 HKUDS `research_agent/inno/agents/inno_agent/survey_agent.py` 中现有 survey agent 与文件工具读取论文和对应代码。用 OpenScholar `src/open_scholar.py: OpenScholar.run` 综合已提供的 input/ctxs；不要把 run 当作完整爬虫。
## 输入输出
输入研究主题与获取范围；保留每篇资料、段落位置、方法和实验依据。提供 OpenScholar 原生 ctxs，并保存其 output/feedback 等原始结构。额外整理“机制/假设/数据/基线/结果/限制”映射，明确这是组织层的证据整理，而非作者原生评测结论。
默认参数保持原样，若启用 ranking_ce/use_feedback/posthoc_at，显式记录，因为它们并非默认全开。搜索失败标 unknown；不把未找到论文说成研究空白。输出冻结的综述包供各生成器共同读取。

## 执行约定
读取仓库根目录的 `contracts.md` 和 `upstreams.lock.json`。先核对上游 SHA、工作树与依赖；不要凭本文件重写原算法或生成替代提示词。保持上游 prompt、参数默认值、排序、停止条件和解析逻辑，任何覆盖都记录在 invocation 中。没有可运行入口或依赖就输出 blocked 和具体缺项，不假装执行。

将 source_commit、agent_id、task_id、输入产物哈希、参数、模型配置（不含密钥）、原始输出路径写入本次记录。将原始输出原样保留，派生字段另存。多 agent 使用独立进程、独立输出目录和上游独立环境；禁止直接改其他 agent 的产物或 Arbor 共享树文件。

模型由宿主提供。原函数需要 SDK/client 时使用兼容传输适配，不将一次宿主回答冒充上游程序运行。没有工具执行能力的裸模型只能阅读说明，不能声称完成该 skill。默认不切换模型或回退到云端。API 模式由用户配置 endpoint/model/key_env；密钥只读环境变量。

## 固定上游
- [NoviScl/AI-Researcher @ e5dd05a90bca](https://github.com/NoviScl/AI-Researcher/tree/e5dd05a90bcadb436c07283c2f429367c6e525d3)；入口 `ai_researcher/src/grounded_idea_gen.py`。
- [HKUDS/AI-Researcher @ f9a6f8480860](https://github.com/HKUDS/AI-Researcher/tree/f9a6f8480860c193afff600eeffe3defcee8a978)；入口 `research_agent/inno/agents/inno_agent/idea_agent.py`。
- [AkariAsai/OpenScholar @ 0e9b8fb91227](https://github.com/AkariAsai/OpenScholar/tree/0e9b8fb912273d3dae39e593da86e4f6d3bf8de1)；入口 `src/open_scholar.py`。
