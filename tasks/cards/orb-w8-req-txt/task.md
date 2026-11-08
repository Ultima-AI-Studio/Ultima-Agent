# 任务卡：orb-w8-req-txt

- **task_id**：orb-w8-req-txt
- **stage**：G-ORCH 编排层（v0.1）
- **标题**：原始需求原文落盘（G-ORCH 八环节冒烟）
- **创建**：2026-11-09 · G-ORCH 流程冒烟，验证 ① 的理解可被审计

## goal

让 `scripts/orchestrate-order.py` 在 run 目录创建后，把调用方传入的**原始需求原文**逐字写入 `<run-dir>/requirement.txt`，使审计环节能对照原文判断 DeepSeek 的理解是否偏离，而不只是看它自己的复述。

缺这个文件时，① 的产物只有「它说它懂了」，没有「它该懂什么」——审计无从对照。

## acceptance[]

| 编号 | 判据 | 判定方式 |
|---|---|---|
| ACC-1 | 新 run 目录执行一次编排后，`requirement.txt` 存在 | 文件存在性检查 |
| ACC-2 | 文件内容与传入的原始需求字符串逐字一致（含行尾、空白、非 ASCII） | 字节级比较 |
| ACC-3 | 空字符串入参时仍写出文件（0 字节），不跳过、不报错 | 执行 + 字节检查 |
| ACC-4 | 同一 run 目录重跑时行为显式（覆盖），代码注释写明所选策略 | 读代码注释 + 重跑 |
| ACC-5 | 改动仅限 `scripts/orchestrate-order.py` | diff 文件清单 |
| ACC-6 | `tests/test_orchestrate_order.py` 全过 | 贴 pytest 输出 |

## 范围冻结

**做**：在 run 目录校验通过后、进入 stage 循环前，写入 `requirement.txt`（UTF-8 无 BOM，内容不 strip、不规范化行尾）。

**不做**：不改 `src/brain/orchestrator.py`；不改审计/冻结脚本；不做摘要或格式化；不加时间戳、标题、分隔线；不提交 git；不打 tag。

## 回执要求

1. 改动文件清单（应只有 `scripts/orchestrate-order.py`）
2. ACC-1 至 ACC-6 逐项结果，各附实际命令与输出
3. 越界声明（无 = 写「无」）
4. 回归：`tools\venv-openjarvis\Scripts\python.exe -m pytest -o addopts= -q tests/test_orchestrate_order.py`
