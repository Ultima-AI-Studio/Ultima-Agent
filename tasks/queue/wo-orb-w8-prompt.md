# 派发载荷 · wo-orb-w8

> 权威源：`H:\UltimaAI\INDEX.md`（G-ORCH-001）、`docs/INDEX.md`
> 唯一工单：`wo-orb-w8`
> 任务卡：`tasks/cards/orb-w8-req-txt/task.md`
> 编排产出：`tasks/queue/runs/smoke-gorch-20261109/stages/`（decompose / work_order / schedule）

## 这是什么

G-ORCH 流水线刚修完四个断点（①任务理解、④排程产出校验、⑦两轮独立审计、⑧tag 前置审计）。本次用**一个真实小任务**做八环节全链冒烟：这个任务本身走完「理解 → 拆分 → 工单 → 排程 → 派发 → 审计 → 冻结」。

## 要做什么

严格按任务卡 `tasks/cards/orb-w8-req-txt/task.md` 的 T1 执行。

一句话目标：**让 `scripts/orchestrate-order.py` 在 run 目录里落一份 `requirement.txt`，逐字保存调用方传入的原始需求原文**——这样审计环节能拿原文对照 DeepSeek 的复述，判断理解有没有偏。

## 边界（越界即打回）

- 只改 `scripts/orchestrate-order.py`
- 不改 `src/brain/orchestrator.py`、不改审计/冻结脚本
- 不做摘要、不做格式化、不加时间戳/标题/分隔线
- UTF-8 无 BOM，不规范化行尾
- 不提交 git、不打 tag、不改主表

## 回执必填

1. 改动文件清单（应只有 1 个）
2. ACC-1~ACC-6 逐项命令与输出
3. 越界声明（无 = 写「无」）
4. `tools\venv-openjarvis\Scripts\python.exe -m pytest -o addopts= -q tests/test_orchestrate_order.py`

## 禁止

- 不要跑全量测试（用白名单，不要 recofurse 根目录）
- 不要自己打 tag——冻结由 `scripts/freeze-work-order.py` 在审计通过后执行
