# AutoResearchClaw 主框架：讨论、最小验证与回流

## 已实现与未完成

本版用 **Claw 的原生阶段执行器 execute_stage、Stage 枚举和 DECISION_ROLLBACK** 作为执行与回退依据，增加适配调度器。**没有直接运行未修改的 execute_pipeline**：为避免原生回退次数用完后强制推进，以及论文生成阶段被自动触发，外围调度、检查门禁和预算由 mai_auto 管理。此区别属于明确记录的集成改动。

Arbor 继续负责 idea 池与演化记录；独立引用技术链不被覆盖。七类生成方法仍各自使用原生入口，不由本仓库重新编写科研提示词。

当前完成：连续调度、条件回退、逐候选原生 debate 后排序、novelty 接口、Claw 阶段调用接口、预算与恢复。**未完成真实模型和 VR 实验的端到端联调**。必须接入生成、验证计划检查、实际结果检查、Arbor 累计归档 worker；模板中的空值会在执行前被拒绝。现有 Windows A-Frame 文件不在此仓库。

## 顺序与回路

候选生成 → 初筛 novelty → 逐候选发言/反驳/综合 → 排名挑选 → 对选中修订版再查 novelty → 最小实验设计 → 计划检查 → 实现 → 资源规划 → 执行 → 结果检查 → 分析 → Claw 研究决策 → 归档。

| 信号 | 去向 |
|---|---|
| 任一 novelty 报告（包括机器建议 proceed） | 暂停为 awaiting_human，等待用户决策 |
| 用户选择 differentiate/reject/need_evidence | 分别返回生成／停止／等待补证据；机器建议不直接控制去向 |
| 计划检查 revise | 回实验设计，不重新生成全部候选 |
| 实际执行失败 | refine 后重新执行，不否定研究假设 |
| 实验设计无法回答问题 | 回实验设计 |
| 结果 supported/refuted/inconclusive | 交给结果分析与原生研究决策 |
| Claw 决策 pivot | 归档后回 HYPOTHESIS_GEN（8） |
| Claw 决策 refine | 归档后回 ITERATIVE_REFINE（13），再执行与检查 |
| Claw 决策 proceed | 只有实际结果检查为 supported 才进入 ready_for_formal_review；不自动写论文 |
| 预算耗尽 | 保存并停止，不强制 proceed |

每次回退清除当前上下文中失效的下游结果；旧尝试原文保留在独立目录，并作为 feedback 提供给后续 worker。集成未实现“哪个生成方法最有效”的学习算法，也未实现自动并行分支队列。

## 裁决和挑选的实现边界

`claw_discuss_select` 对每个外部生成候选调用原生 run_debate。仍使用原生角色与提示词；候选和反馈作为 synthesis 变量中的输入材料。综合结果可能改变假设，所以分配新的修订 ID、parent_id 和文本 SHA256。随后使用原生 tournament_rank 提示词和 _parse_winner 排序这些修订版。

没有直接调用 run_tournament，因为它会重新生成候选，不能直接接收外部候选池。这是“排序已有候选”的薄适配，并非上游已有的完整串联路径。无法解析裁决时直接阻塞，不沿用原生默认选择第 0 个的降级行为。

原生 debate 的裁决失败可能退化为拼接观点。本适配保留原始记录，随后另作选择评价，仍不声称讨论证明假设正确。当前适配共用一个模型，不宣称独立评审；最大候选数默认 4，反驳默认 1 轮。原生角色仍有其领域倾向，不自动改写成 VR 专用角色。

`claw_novelty` 原样调用 check_novelty，绑定被检查文本的 SHA256。Claw 原生方法主要使用文献检索与关键词相似度，不是语义原创性证明。选中修订版必须获得与其文本一致的报告，并单独经人工确认。CoI 的深层新颖性修订尚未接入此驱动器。

## 配置和运行

复制 examples/research-loop.template.json 到 workspace/research-loop.json；填入真实文献、原生 Claw YAML 和空 worker。完整 Claw 依赖应安装在独立环境，在每个 job.python 指定对应 Python。源码通过 bootstrap 固定版本。

```bash
python -m mai_auto.cli bootstrap claw arbor
python -m mai_auto.cli loop workspace/research-loop.json
python -m mai_auto.cli loop runs/claw_ID/config.json --resume runs/claw_ID
# 检查日志和副作用后，仅重试执行错误或中断的阶段
python -m mai_auto.cli loop runs/claw_ID/config.json --resume runs/claw_ID --retry
```

WSL/Linux/macOS；不是后台守护服务。相同运行有文件写锁；恢复要求完全相同配置。max_rounds 统计初始尝试和回退次数，max_calls 包含失败尝试，max_seconds 为累计执行预算，stage_timeout 为一次调用上限。这些不是精确 token/API 费用上限。

原生 Claw 阶段使用其 YAML 中自己的模型配置，而讨论 adapter 使用 job.model；两者必须显式配置一致或记录差异。loopback 本地模式和 API 均需正确的原生依赖。模拟实验模式会被拒绝，消息发送和外部 session spawning 必须关闭。模板 pass_env 显式传递 MAI_CLAW_API_KEY；不要把密钥写进 JSON、YAML 或 Git。原生客户端的供应商重试/回退行为仍由上游配置决定，本适配未全面审计其联网路径。

模板把 Claw 原生设计门禁设为 auto_approve_gates=true，后接我们显式配置的 plan_check；这是检查位置调整，不是以默认同意替代检查。可以关闭自动批准并保留上游人工门禁。

## 人工 novelty 决策

两个 novelty 位置均强制人工参与，不提供模型自动批准开关。每次暂停会生成 `review-request.json`：候选原文、机器检索报告、可选操作。用户可让宿主进一步整理最近工作与差异，但不得把自动摘要当作用户已批准。

```bash
python -m mai_auto.cli novelty-review runs/claw_ID continue --reviewer "your-name" --reason "具体差异及继续验证的理由"
python -m mai_auto.cli loop runs/claw_ID/config.json --resume runs/claw_ID
```

四个决定：continue（允许继续探索，不证明新颖）、differentiate（改方向后重审）、reject（停止本次研究）、need_evidence（补充文献后再处理）。理由与审核人不能为空。记录绑定报告内容、候选文本和配置；修改报告会使旧决定失效。恢复不重复执行已完成的检索，不因超时或 --retry 推断用户同意。

`human-review.json` 是本地操作审计，不是带身份认证的安全系统；同一文件系统权限的程序仍能编辑文件。agent 应仅在用户明确作出该次决定后代录，不能为了让循环继续而自行调用批准命令。测试中的批准记录仅属于夹具。

## worker 协议

空入口使用 command argv 数组，调度器在末尾追加 request.json 与 result.json 的绝对路径。工作目录是仓库根目录。不经过 shell。worker 成功写 JSON 对象，退出码为 0；stdout/stderr 保留。command worker 必须实际调用指定上游/实验工具，不能用固定文本替代。

请求包含 input、current、feedback、history、round、stage、root、workspace（共享原生 Claw 产物目录）、output（独立尝试目录）。job 中 {"$ref":"/current/..."} 按 JSON pointer 绑定实际输入。

| worker | 输出与职责 |
|---|---|
| generate | candidates: [{id,text,...原生来源}], text: 原始候选集合的文本表示；保留原始产物与上游版本，读取 feedback 做有根据的更新 |
| plan_check | verdict=pass/revise/blocked，附具体原因；检查主张、样本、操作、观测、判据和预算是否对应 |
| execute | 模板默认 Claw Stage 12；VR 实验通常须替换为真正的浏览器/引擎 worker，同时生成后续原生分析所需的产物契约 |
| result_check | verdict=supported/refuted/inconclusive/execution_failed/invalid_design；evidence 为实际文件路径数组（位于仓库工作区）；附原因、测试退出码及判据解释 |
| archive | 汇总所有候选和父子关系调用原生 Arbor；保存原始讨论、验证结果及来源，不把单次快照假装自动共享池合并 |

原生 Stage 9–15 输入输出仍按 Claw 自己的 contracts 校验。讨论选中的文本自动映射到 native/stage-08/hypotheses.md。不能只输出一个 verdict 就假装 A-Frame 与 Claw 的指标/分析格式已经兼容。

调度器检查证据文件存在并记录 SHA256，但不证明证据内容是真的，也不自动构造软件测试 oracle。计划检查与结果判定仍需要接入可执行且有来源的实现。ready_for_formal_review 仅表示最小验证获初步支持，不代表论文结论成立。

## 恢复与测试

每次尝试独立留档，state.json 原子保存。故障恢复跳过已经完成的阶段；中断时需要确认子进程与副作用再 --retry，不保证 exactly-once。科学证据不足导致的 blocked 不用 --retry 绕过，应补材料后另开明确的新任务。

测试使用真实 Claw Stage/回退映射和原生 debate/排名提示词，但模型回复与实验结果是确定性夹具。覆盖连续两轮、条件回退、恢复不重跑、预算不强制推进、novelty 绑定、人工暂停/批准、旧批准拒绝、证据门禁及非法裁决。真实模型和 A-Frame 闭环尚未验证。
