# WO-ORB-W7 监工报告（主脑全程观察）

- 日期：2026-11-08
- 工单：`wo-orb-w7` — G-ORCH 编排层接线（过渡托底单，接线完成后交还外脑）
- 最终状态：`audit`（待 DeepSeek 独立审计）
- 最终提交：`1952160b`
- Tag：`wo-orb-w7-orchestration-wiring-20261108`（annotated，tag 对象 `51b880dc` → commit `1952160b`）

---

## 一、四项 Gate 结果

| Gate | 内容 | 结果 | 关键证据 |
|---|---|---|---|
| T1 | orchestrator 接链 + 回执契约 | **PASS** | `scripts/orchestrate-order.py` 三 stage 顺序跑通；`--dry-run` 退出码 0 且不建 run 目录；18 passed |
| T2 | sentinel 挂载 | **PASS** | 现场实证：run 目录自动生成 `.sentinel.lock` + `heartbeat.jsonl`（1331→2274B 持续增长），进程 `-m src.brain.sentinel wo-orb-w7` 常驻；`final.json`/`final-message.json` 双认；11 passed |
| T3 | pytest 作用域 | **PASS** | `testpaths = tests src scripts tasks execution`，根目录无位置参数跑：**1143 collected / 1115 passed / 28 failed / 0 skipped / 0 collection errors / 581.17s** |
| T4 | 回执契约对齐 | **PASS** | 三份真实回执判读正确（详见第三节）；专项 36 passed |

联合门：`tests/` 五文件专项 **36 passed in 1.01s**。

---

## 二、三块地基修到什么程度

| 地基问题 | 本轮修法 | 状态 |
|---|---|---|
| ① 主表脏数据 | **只做数据抢修 + 机制留待拍板** | **未修根**（详见第四节） |
| ② 全量测试没有定义 | `testpaths` 圈定自有目录，排除 `libs/legacy-topo/data/docs/tools` | **已修** |
| ③ 回执契约没对齐 | 新建 `receipt_contract.py`，fail-closed 分类 + 三处缺陷修复 | **已修** |

### ② 的口径依据（实测）

- 仓库不是单一 Python 项目：顶层混放 `libs`（外部库）、`legacy-topo`（历史工程）、`data`（证据快照）、`docs/research/sources`（研究源码）、`tools/*/source`（上游源码）
- 根目录递归：`collection errors=14028`、耗时 `1997.14s`（Codex 首轮实测踩中）
- 项目自有测试实际分布：`tests/` 5、`src/` 93（各模块 `tests/`）、`tasks/` 9、`scripts/` 3、`execution/` 1
- 白名单口径：**1143 tests collected in 8.51s**（vs 根递归 33 分钟仍失败）

### ③ 修复的三处缺陷

| # | 缺陷 | 复现 | 修复 |
|---|---|---|---|
| 1 | `status` 非字符串抛 `TypeError` | `status=[]` + 有效 evidence → `unhashable type: 'list'` | 非 `str` 直接 fail-closed |
| 2 | 裸子串匹配串单 | `wo-orb-w7` 命中 `wo-orb-w7x` | 完整工单号边界正则 |
| 3 | **全角冒号致「待审计」落 `blocked`** | 回执写 `- 自检：PASS`，正则 `自检\s*PASS` 不认冒号 → 判 `INVALID_RECEIPT` | `自检\s*[：:]?\s*(?:PASS\|通过)` |

第 3 条是本轮最关键的活体复现：Codex 明确报 `READY_FOR_DEEPSEEK_AUDIT`，`done.json` 却写 `receipt_valid: false, state: blocked`。修复后同一份回执判 `audit`。

### 三份真实回执交叉验证（修复后）

| 样本 | 期望 | 实际 |
|---|---|---|
| `wo-orb-w6-…133604629405Z`（待审计） | audit | `audit / valid=True / text` |
| `wo-orb-w6-…125637445858Z`（BLOCKED） | blocked | `blocked / valid=True / text` |
| `wo-orb-w7-…160133265380Z`（本轮 READY） | audit | `audit / valid=True / text`（修复前为 blocked） |

---

## 三、四次派发全记录

| # | run | 时间 | 结果 |
|---|---|---|---|
| 1 | `…142242990263Z` | 22:22–23:17 | **BLOCKED**：T3 根目录递归 14028 errors / 1997s |
| 2 | `…152126993086Z` | 23:21 | **被打断**：主表 `proposal-pending-gate` → status-gen 退出 1，无 codex 进程 |
| 3 | `…152326360547Z` | 23:23–23:53 | **BLOCKED**：T3 已修好（1143/1115/28），但自审发现 T4 两缺陷；提交 `0eef9c81` |
| 4 | `…155949893027Z` | 23:59 | **被打断**：主表 `arch-review-approved` → 同上 |
| 5 | `…160133265380Z` | 00:01–00:12 | **READY_FOR_DEEPSEEK_AUDIT**，提交 `a5322432` + tag |
| 6 | 主脑收尾 | — | 补全角冒号判据，提交 `1952160b`，tag 移至 `1952160b` |

---

## 四、未修根的第一块地基（必须由你拍板）

**现象**：本轮 5 次派发中 **2 次被主表脏数据直接打断**，且同一位置 3 小时内出现 3 个不同的自造状态词：

| 时间 | 写入者 | 状态词 | 处置 |
|---|---|---|---|
| 早期 | UltimaSentinel | `partial` | → blocked |
| 22:xx | UltimaSentinel | `open-candidate` | → pending |
| 23:21 | UltimaSentinel | `proposal-pending-gate` | → pending |
| 23:59 | UltimaSentinel | `arch-review-approved`（连工单号也改成 `wo-ultimasentinel-*`） | → pending |

**冲突点**：`queue-status-gen.py` 的 `STATES` 只有 6 态（`frozen/pending/executing/audit/blocked/cancelled`），遇任何其他词 **fail-closed 直接退出 1**，而它是派发器的硬前置 → 全项目任何一次派发都被别人一句话打断。

**两个机制修法（二选一，需你定）**：

1. **宽进严出**：`status-gen` 遇未知状态不抛异常，归入 `unknown` 分组继续生成，并在输出中列出「未知状态清单」供审计；重复 `(project,wid)` 仍 fail-closed（重复才是真数据损坏）
2. **写入门**：约束 UltimaSentinel 侧只能写 6 态，把它的自造词映射到 `audit`/`blocked`，并在其代码里加写前校验

未改动原因：这条属**标准变更**（放宽公共账本的闸门语义），不在「抢修让他上岗」的授权范围内，且你此前明确说过机制修法待拍板。

---

## 五、遗留项

- **28 项全量失败**：KWS 缺 `sherpa_onnx` 3、派发与队列进程生命周期 16、Ultima Bus 8、推理入口 1 —— 均为仓库既有历史债，本单未引入、未修、未 ignore、未 skip
- `c5f9156b`（w6）仍无 tag
- ⑦ 独立审计（DeepSeek 两轮）、⑧ 打 tag 交还 —— 本轮只做到 `audit` 入队，真正 ⑦⑧ 仍缺载体
- 主表并发写者身份已锁定为 `H:\UltimaAI\UltimaSentinel` 项目的 codex exec（PID 28720，23:52 起）
- 工作区仍有其他工单大量既有脏改动，未清理

---

## 六、可复现命令

```powershell
# 全量门（带 testpaths 生效）
H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest -o addopts= -q

# 本单专项门
... -m pytest -o addopts= -q tests/test_receipt_contract.py tests/test_orchestrate_order.py tests/test_sentinel.py tests/test_orchestrator.py tests/test_orchestrator_sentinel_integration.py

# 主表体检
... H:\UltimaAI\_shared\queue\queue-status-gen.py
```
