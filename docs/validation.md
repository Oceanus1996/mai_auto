# Validation — 2026-11-05

## Passed
- 14 skill folders passed the skill frontmatter/name validator.
- Six unittest cases passed, including actual pinned Arbor Node/IdeaTree creation, parent linkage, depth, save/load and invalid-parent rejection.
- Actual subprocess CLI invocation of Arbor completed and produced JSON/Markdown plus invocation provenance. Example hypothesis was test data, not generated research.
- Actual pinned AutoResearchClaw run_debate ran against a local **scripted HTTP test server**: original prompts/roles, round-0/round-1 files and judge invocation were exercised. This validates wiring, not model inference or idea quality.
- Chain evidence checks, foreign-key integrity and immutable snapshots passed.
- Transport rejected accidental cloud endpoints in local mode and unconfigured API mode.
- Independent skill read-through handled missing papers, missing labels and missing oracles without pretending seven native agents had run. Clarified that SciPIP's native combination is not arbitrary cross-candidate synthesis.

Environment: Python 3.12; tree import required pydantic-settings (2.16.2 installed in an isolated venv with existing runtime packages). The first import test exposed that missing dependency; it passed after installation. No upstream source files were patched.

## Not yet verified
- No real local model service was found on the checked loopback endpoints; no cloud model call was made.
- CoI bridge is source-mapped but has not completed a native runtime/model test.
- Seven generation methods are skills, not seven fully installed runnable adapters. SciMON data scripts, HKUDS tool runner, SciPIP storage and Nova search infrastructure still need native setup.
- No scientific experiment, domain oracle, benchmark, or research-quality improvement was validated.
- No host-specific skill installation or UI dashboard has been performed. Host must load the repo skills and supply tools.
- Process-group timeout handling is POSIX-oriented: Linux/macOS/WSL. Native Windows behavior is not tested.
- Repository dependencies and model compatibility are not fully locked or benchmarked; source SHA pinning alone is insufficient.

Reproduce:
```bash
MAI_TEST_ARBOR=/absolute/path/to/pinned/arbor \
MAI_TEST_CLAW=/absolute/path/to/pinned/claw \
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```
Without those variables, native integration cases are explicitly skipped. Ordinary tests use no model or network services except a loopback scripted server in the optional debate test.

## Claw 连续循环

新增 tests/test_loop.py：验证原生 Stage 与回退映射下的两轮连续推进、计划回退、恢复、预算、证据门禁、修订版 novelty 绑定和原生 debate 后排序。人工 novelty 暂停、恢复不绕过、报告变化后旧批准拒绝也已覆盖。模型与实验结果使用确定性夹具，不是科学发现。真实模型、Claw 全套原生阶段和 A-Frame 集成尚未运行验证。

## 环境 agent 接入

新增 tests/test_environment.py：缺源码时产生部署请求、旧提交环境不复用，以及真实独立 Claw 环境经运行器调用原生 debate（本地 HTTP 返回脚本化测试文本）。启用 MAI_TEST_SETUP_CLAW=1 时执行最后一项。当前完整测试共 21 项通过。

本次环境设置 agent 实际按上游 README 执行 venv + pip install -e 固定源码；pip check、researchclaw --help、debate/tournament/novelty/executor/config/adapters 导入均通过。记录在被忽略的 .environments/claw/ 中。模型回复测试仍为夹具，未执行真实科研推理或 A-Frame 实验。
