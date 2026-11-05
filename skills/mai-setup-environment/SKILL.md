---
name: mai-setup-environment
description: 为 mai_auto 的原生科研接口按需准备或修复上游环境。用于执行前缺源码、依赖、解释器、浏览器或模型连接配置时；检查已有环境，依据固定仓库版本安装，完成就绪验证后交回研究协调器。
---

## 职责
作为环境设置 agent，接收接口需求和失败日志，执行部署及环境检查；不生成科研结果、不修改上游科研算法、不代替用户批准 novelty。使用仓库根目录 MAI_ROOT；先读 upstreams.lock.json、contracts.md 和 docs/environment-agent.md。

## 输入
读取运行器返回的 environment-request.json，包含 upstream、adapter、source_commit、repository、required_imports、source、descriptor_path 和失败原因。若由宿主在运行前调用，直接从 job 与 lock 文件取得相同信息。没有实现的 adapter 或空 worker 属于接口开发问题，明确交回协调器，不用安装软件掩盖。

## 按需准备
1. 核对源代码提交与干净状态。缺源码则使用现有 bootstrap；已有稀疏检出可补齐同一提交的必要文件，不升级 HEAD、不改源码。
2. 从该提交的 README、pyproject.toml、requirements、Dockerfile 和运行示例确定安装命令、Python/Node 版本及系统依赖。记录引用文件和执行命令；不凭印象选择依赖版本。
3. 优先复用 `.environments/<upstream>/ready.json` 中相同提交的环境。缺少依赖再修复，避免每轮重装。需要重建时建立独立目录，保留旧环境及日志。
4. 在 `.environments/<upstream>/` 下创建隔离环境，按上游原生方法安装。不要把不同仓库的所有依赖混入主环境。并发任务共用部署时使用文件锁，避免同时 pip install。
5. 检查该接口所需模块可导入。另按任务要求验证命令行入口、浏览器/引擎启动、数据路径和模型端点；分别报告，不以 import 成功代替全部就绪。
6. 本地模型只检查明确配置的本地端点；API 模式读取指定环境变量，不输出密钥、不自动换供应商。缺凭据或不存在的本地引擎属于确实缺少的外部资源，报告精确缺项。
7. 保留原始安装与检查日志。安装成功后写 ready.json，见下方格式，再由协调器恢复原阶段；不要重跑已完成的科研步骤。

```json
{
  "source_commit": "固定上游提交",
  "source": "/绝对路径/上游源码",
  "python": "/绝对路径/独立环境/bin/python",
  "install_evidence": "/绝对路径/install.log"
}
```

仅在实际执行并验证后填写真实路径。该记录是可复用环境位置，不是全系统成功证明；运行器每次仍按接口做导入检查。Python 依赖已经可用但模型未配置时，可以登记环境，同时明确 model_ready=false，禁止声称科研任务可运行。

## 失败与返回
区分 source_missing、dependency_missing、runtime_missing、model_unavailable、interface_missing。可修复的环境问题在现有授权与预算内自行处理；保留有限重试记录，不无限安装重试。无法解决时输出实际错误、已完成内容、剩余缺项和下一步。

返回 source、Python 路径、安装依据、导入验证结果、模型/实验环境各自状态及日志。协调器收到后执行同一个 job；若在 loop 中则恢复该阶段。不要伪造 human-review.json。
