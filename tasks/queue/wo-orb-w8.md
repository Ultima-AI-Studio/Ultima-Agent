# Codex 工单 · G-ORCH 冒烟：原始需求原文落盘（wo-orb-w8）

> 版本：v0.1 ｜ 状态：可开工 ｜ 适用工具：Codex
> 用法：按 T1 执行，验收全绿即止。
> 范围依据：`docs/reports/g-orch-run-ledger-20261109.md`；编排产出 `tasks/queue/runs/smoke-gorch-20261109/stages/`
> 性质：**八环节冒烟单**。用一个真实小任务验证「理解 → 拆分 → 工单 → 排程 → 派发 → 审计 → 冻结」全链能跑通。

---

## 0. 范围冻结

**本单只做**：

1. `scripts/orchestrate-order.py` 在 run 目录校验通过后，把原始需求原文逐字写入 `<run-dir>/requirement.txt`
2. 代码注释写明重入策略（已有该文件时覆盖）

**本单不做**：不改 `src/brain/orchestrator.py`；不改审计/冻结脚本；不做摘要或格式化；不加时间戳、标题、分隔线；不提交 git；不打 tag；不改主表。

---

## 1. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T1 orb-w8-req-txt | 原始需求原文落盘 + 边界与重入 | ACC-1 至 ACC-6 全绿 |

---

## 2. 任务明细

### T1 · 原文落盘
**文件**：`scripts/orchestrate-order.py`（唯一改动文件）
**写什么**：
1. 在 `_validate_run_dir` 成功后、进入 stage 循环前，创建 run 目录并写入 `requirement.txt`
2. 内容为 `_read_requirement()` 的返回值，逐字写出：不 strip、不规范化行尾、不追加任何内容
3. 编码 UTF-8（无 BOM）
4. 同一 run 目录重跑时覆盖，并在代码注释写明"覆盖"这一策略

**验收（Gate T1）**：
- ACC-1 新 run 目录跑一次，`requirement.txt` 存在
- ACC-2 字节级比较，内容与入参一致（含中文与多行）
- ACC-3 空字符串入参 → 文件存在且 0 字节
- ACC-4 重跑同一目录 → 不抛异常，文件被覆盖，注释写明策略
- ACC-5 diff 仅 1 个文件
- ACC-6 `tests/test_orchestrate_order.py` 全过

**禁止**：用 `read_text()` 做行切分后重写；静默跳过写入；改动 `run_stage` 的接口签名。

---

## 3. 回执要求

1. 改动文件清单
2. ACC-1~ACC-6 逐项命令与输出
3. 越界声明（无 = 写「无」）
4. 回归输出：`tools\venv-openjarvis\Scripts\python.exe -m pytest -o addopts= -q tests/test_orchestrate_order.py`
