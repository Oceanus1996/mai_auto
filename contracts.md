# Shared orchestration contract

These are integration rules, not claims that upstreams implement every field.

## Invocation and fidelity
- Resolve MAI_ROOT to this checkout. Read upstreams.lock.json. Use a clean, pinned checkout and an independent Python environment for each upstream. Do not install all upstream dependencies into a shared environment.
- Preserve native prompts, retrieval, defaults, scoring, stop conditions, and parsing. Record caller overrides (including model, role count, budgets and rounds). Transport changes are adapters, not method changes.
- Do not silently repair upstream bugs or specialize ML-centric prompts for security. Report a minimal proposed patch separately; patched runs are not pristine upstream runs.
- A missing native interface/data/backend is blocked. An agent factory is not a completed agent run. Host-emulated prompts are not native execution.
- Record source SHA, task/agent IDs, native entry, arguments, model identifier, input hashes, raw outputs, times and failures. Keep model credentials in environment variables, never JSON, prompts, Git, or output metadata. Native logs may contain task data; keep runs private and ignored by Git.
- Source pinning is not a dependency lock. Upstream dependency installation and provider compatibility need separate validation. `doctor` currently checks source identity only.

## Two independent stores
- Arbor original IdeaTree JSON is the idea structure. Only the coordinator writes the shared tree. Parallel upstream jobs return artifacts to it. The native arbor_tree adapter creates a per-run tree, not a shared-tree merger; its result must be explicitly imported by the coordinator.
- Use single-parent Arbor nodes. Store supporting/composed-from IDs in a sidecar, not an invented second parent in Arbor's schema. Preserve old hypothesis versions by creating new nodes. Execution retries have separate run IDs.
- literature.sqlite owns papers, citations, evidence-backed evolution links, and immutable snapshots. It does not contain writable Arbor node state. Chain updates issue review requests; never rewrite old grounding.
- Citation edge is bibliographic fact; evolution edge is supported interpretation. Keep locator/quote or unresolved status, and do not turn inferred inheritance into verified citation.
- Shared schema envelope: `schema_version`, `task_id`, `agent_id`, `node_id` (optional), `source_commit`, `input_artifacts`, `raw_artifacts`, `derived_annotations`, `status`. Native content remains unmodified under raw_artifacts.

## Phase order
literature -> independent generation -> early debate -> minimum mechanism check -> revise/branch or advance -> formal design late review -> baseline checks/implementation search -> final verification.
Minimum checks have their own explicit oracle and lightweight controls if the claim is comparative; they do not require complete benchmark reproduction. Late review is before formal experiments, after initial support. Execution success is not support; reviewer agreement is not correctness.

## Gate evidence
- Critique: exact claim, supporting evidence or proposed check, author response, unresolved items. Append annotations to native output; do not pretend original prompts enforce this schema.
- Minimal check: claim, prediction, falsifier, small input, command/tool, budget, raw logs, verdict (`supported`, `refuted`, `inconclusive`, `invalid_execution`), scope and assessor.
- Formal plan: controls, treatments, fixed data split, metric direction, evaluation code reference, budget. Curie `done` only means its native completion condition; baseline validation is a separate evidence record.
- Verification: actual test outputs, recomputed metrics, statistical checks when appropriate, formal verifier output when applicable. LLM explanations do not replace those artifacts.

## Host compatibility
A skill is instructions/resources for an executing host, not a model server. A local backbone or API model needs a host with file/process tools and optional parallel task support. The host loads requested SKILL.md files; dependencies are executed in native environments. If no parallelism is available, sequential execution is permitted but must be recorded, not called parallel.
The included transport handles loopback HTTP in local mode, explicit HTTPS+key_env in api mode. It serves only the supplied bridge methods; it does not intercept other upstream network calls. Native literature retrieval may still require the Internet. Do not claim whole-system offline inference until every invoked native client is checked.

## Transport delta
The bridge preserves research functions and prompt sources, but does not reuse native cloud SDK wrappers. It defaults to temperature 0.7; CoI response_async also defaults to n=1 and max_tokens=4000, matching inspected upstream defaults. HTTP timeout defaults to 180 seconds. Transport errors raise rather than silently returning None, and no provider-specific fallback/response-format adaptation is implemented. Record this adapter difference; do not describe whole-client behavior as identical.
