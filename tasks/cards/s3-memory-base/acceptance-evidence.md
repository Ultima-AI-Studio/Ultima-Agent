# 验收证据 · s3-memory-base（M17 记忆底座）

- **task_id**：s3-memory-base
- **状态**：COMPLETED
- **验收时间**：2026-10-27
- **验收人**：Ultima 主脑（独立复核视角：实现与验收分离，dev 不自证清白）

## ACCEPT 清单

| 项 | 验收项 | 结果 | 证据 |
|---|---|---|---|
| ACCEPT-1 | 四层记忆结构可写入可检索可回溯 | PASS | `test_memory_s3.py::TestLayers`（四层写入/检索/软删回溯/重启持久化）；落地 `data/memory/layers/*.jsonl` |
| ACCEPT-2 | 本地向量检索可用；Mem0 备选 PoC 结论落档 | PASS | `OnnxEmbeddingProbe` 真实探测：fastembed-onnx + BAAI/bge-small-zh-v1.5（512 维）ok=true，结论落档 `data/memory/onnx-poc-result.json`；`VectorRetriever` 向量主选、失败回退关键词 |
| ACCEPT-3 | 反思条目与遗忘边界规则生效 | PASS | `ReflectionWriter` 反思条目入程序式层；`forgetting_rules`/`forget_expired` 按 retention_days/max_entries 逐出并留驱逐审计 `data/memory/logs/memory-evictions.jsonl` |
| ACCEPT-4 | 写入闸门拦截不可信内容；事实/建议分离标注 | PASS | `MemoryWriteGate`：web/model.draft 不可信来源拒绝直入长期层；敏感模式（key/凭证明文）拒绝入库；fact/suggestion 自动分离；测试 `TestGate` 5 项 |
| ACCEPT-5 | 记忆经总线供读，跨模块一致 | PASS | 真实总线 `BusKernel.load("ultima.memory.lite")` → `memory.write`（可信入库 declarative/fact）/（不可信 denied）/`memory.read`（命中）全通；契约签名 memory.read(query)/memory.write(fact) 未变 |
| ACCEPT-6 | 回执完整 | PASS | `receipt.json` 落盘并经 `ReceiptValidator(base=项目根)` 复核 0 issues；tasks.json 置 COMPLETED |

## 测试结果

| 测试集 | 结果 |
|---|---|
| `src/brain/memory/tests/test_memory_s3.py`（本工单验收，12 项） | 12/12 OK |
| 回归 `guardrails_s3`（31 项） | OK |
| 回归 `guardrails_m2`（19 项） | OK |
| 回归 `credential_s3`（17 项） | OK |
| 回归 `memory_m3`（8 项） | OK |
| 回归 `preference_p2`（14 项） | OK |
| 回归 `credentials`（24 项，python31313） | OK |

## 关键参数冻结表（不越基线）

| 参数 | 值 | 依据 |
|---|---|---|
| 四层 + 双档案 | working / declarative / procedural + device_profile / env_profile | ADR-008 / data-model.md |
| onnx 嵌入模型 | BAAI/bge-small-zh-v1.5（512 维，fastembed） | 任务卡 ACCEPT-2（onnx 主选） |
| Mem0 备选 | 既有 Mem0Backend（ollama nomic-embed-text + FAISS） | PoC 失败升级评估路径，本轮探测 fastembed 可用故主选 onnx |
| 可信来源 | user / tool / bus.internal / system / engine | 写入闸门分级 |
| 不可信来源 | external / model.draft / web / mcp.unverified | 只允许 working 暂存或拒绝 |
| 遗忘边界默认 | working 200 条/1 天；declarative 500/365；procedural 300/730；档案 100/365 | 可配置（max_entries/retention_days） |
| 删除语义 | 软删（deleted=True 保留行） | 可回溯可审计 |
| 总线契约 | memory.read(query) / memory.write(fact) 签名不变 | manifest.py INTERFACE_SIGNATURES 冻结 |

## 产出文件

- `src/brain/memory/layers.py`（四层存储/检索/回溯/删除/遗忘边界）
- `src/brain/memory/gate.py`（写入闸门 + 事实/建议分离 + 敏感拦截）
- `src/brain/memory/reflection.py`（反思条目 + 遗忘规则快照）
- `src/brain/memory/vectors.py`（VectorRetriever + OnnxEmbeddingProbe PoC 落档）
- `src/brain/memory/__init__.py`（扩展导出）
- `src/brain/memory/tests/test_memory_s3.py`（12 项验收测试）
- `execution/packages/memory/ultima.memory.lite/0.1.0/ultima_memory_lite_v0_1_0/main.py`（总线插件升级：四层+闸门+反思+向量，契约签名不变）
- `data/memory/onnx-poc-result.json`（PoC 结论落档）
- `tasks/cards/s3-memory-base/acceptance-evidence.md`、`receipt.json`

## 边界未触碰

- ADR-008 冻结基线未推翻（四层结构语义对齐，不替换既有 PreferenceStore/Mem0Backend，仅在其上新增分层底座）；
- manifest.py 冻结契约未改（memory.read/memory.write 签名与 L9 域暴露不变，无新增 exposes）；
- 未向 fileDomain（H:/UltimaAI/UltimaAgent）之外写任何文件；
- 模型/API 冻结基线未动；守护进程（watchdog/agent_server）未触碰；
- 测试与演示写入均已清理（真实记忆库零污染）。
