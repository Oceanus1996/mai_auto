# mai_auto — 原生科研方法的 Skills 工作台

以 AutoResearchClaw 原生阶段执行器为主，Arbor 保存研究树，独立维护技术演化链；复用原仓库方法，增加接口与明确的调度门禁。

**当前是可导入的 skills 第一版，不是已经完成真实模型验证的全自动科研系统。**
14 个 SKILL.md 可供本地 backbone 的 agent 宿主或 API agent 宿主加载。仅有模型权重或 API key 不会自动提供文件、进程、检索和调度能力。

## 使用

```bash
git clone https://github.com/Oceanus1996/mai_auto.git
cd mai_auto
# 当前功能在 feat/native-research-bridge 分支；合并前需要切换
git switch feat/native-research-bridge
python -m venv .venv
# Linux/macOS；Windows 进程控制请在 WSL 使用
source .venv/bin/activate
pip install pydantic-settings
python -m mai_auto.cli bootstrap arbor
python -m mai_auto.cli run examples/arbor-tree.json
```

向你的 agent 宿主提供 `skills/mai-research/SKILL.md` 和仓库绝对路径（MAI_ROOT）。如果宿主支持技能目录，注册 `skills/` 下全部子目录。各 skill 引用根目录 contracts.md 和 upstreams.lock.json，不能只复制单个 SKILL.md 后丢掉这些资源。

任务示例：
> 使用 mai-research。工作区是本仓库。先对我的研究问题获取文献并形成综述，给出各方法的依赖状态；仅运行已经可用的原生入口。先做最小机制验证，初步支持后再正式审查与检查基线。

## 不改研究方法

固定 12 个上游 SHA，bootstrap 原样检出；不复制改写它们的提示词，不把自己写的脑暴当原生方法。不覆盖 ML/NLP 偏好，不静默修补原脚本。缺入口、数据、环境或工具就 blocked。

- 原生桥：Arbor Node/IdeaTree；AutoResearchClaw run_debate；CoI 原生链和 review→refine。
- 其余方法：已写明原生入口和运行约束的 skills，尚未封装为一键桥。宿主需按原仓库配置环境执行；不得宣称全部七种已联调。
- 独立 chain SQLite：仅存证据关系和快照；推断仍来自原生链方法/有依据的核查，不新增“演化算法”。
- Arbor bridge 输出每次任务独立树；共享树导入由协调器单写管理，尚未提供自动共享树合并服务。

## 本地模型 / API

先在上游各自的独立 Python 环境安装其依赖；在 job 的 `python` 填那个环境的 Python 绝对路径。`source` 可指定已核对 SHA 的干净 checkout。源码依赖隔离，不在总环境混装。

`examples/early-debate.json` 演示 local 模式；`examples/late-review.json` 演示 api 模式。替换占位内容。
- local：loopback HTTP OpenAI-compatible endpoint；不要求云 key。
- api：显式 HTTPS endpoint + model + key_env；密钥在环境变量中，禁止写进 JSON/Git。
- 兼容的是原生方法需要的 chat/response_async 传输；供应商特定协议尚未实现。其他原生网络客户端不会被本适配器自动替换。
- 同模型多角色仍是相关的判断来源；不称独立模型评审。

```bash
python -m mai_auto.cli doctor
python -m mai_auto.cli run examples/early-debate.json
# jobs.json 是任务数组；无依赖任务才并行
python -m mai_auto.cli batch jobs.json --workers 2
python -m unittest discover -s tests -v
```

运行产物在 `runs/<run_id>/`：request/result/record/stdout/stderr。completed 只表示入口正常返回，scientific_verdict 仍为 not_assessed。忽略产物与密钥文件，不上传科研输入。

## 顺序
文献获取/精读/综述 → 并行生成 → 前期反驳 → 最小机制验证 → 修订或初步支持 → 后期实验 review→refine → 控制组检查/有限实现搜索 → 实际核验。

具体边界见 [contracts.md](contracts.md)，各阶段见 [skills/mai-research/SKILL.md](skills/mai-research/SKILL.md)。测试范围见 [docs/validation.md](docs/validation.md)。

## 来源与许可
只保存上游地址、提交与适配调用；第三方代码通过独立 checkout 获取，许可证仍以各锁定仓库为准。分发完整依赖包前须逐仓核对许可证。本仓库不声称拥有第三方方法。

## 连续循环（新增）

`python -m mai_auto.cli loop CONFIG.json` 使用 Claw 原生阶段与回退映射，接入讨论挑选、novelty、最小实验计划检查及结果检查。计划问题回设计、执行问题回修复、pivot 回生成；novelty 必须人工判断，预算耗尽不强制推进。详见 [实现边界与配置](docs/research-loop.md)。

**这是一层适配驱动器，不是未修改的上游 runner，也尚未完成真实研究闭环。** [配置模板](examples/research-loop.template.json) 的空 worker 必须连接原生生成、计划检查、实际结果检查与归档；VR 执行器及模型也需配置。模板会拒绝空入口。
