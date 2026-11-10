# 派发载荷 · wo-orb-w9（回执契约复验）

工单：`wo-orb-w9`
仓库：`H:\UltimaAI\UltimaAgent`（分支 `codex/voice-fsmn-new-path`）
权威入口：`docs/INDEX.md`（先读它，再读工单正文与任务卡）

## 你要做的事

只做一件事：新建 `docs/reports/g-orch-smoke-verify-20261109.md`，写一段不超过 12 行的验证记录，说明本次复验的对象是「回执契约随派发载荷下发」。

## 必读材料

1. `docs/INDEX.md` —— 全局入口与规范
2. `tasks/queue/wo-orb-w9.md` —— 本工单正文（范围冻结、任务明细、禁止项）
3. `tasks/cards/orb-w9-receipt-contract/task.md` —— 任务卡与 ACC-1~ACC-5 判定方式

## 硬性边界

- 只新增一个文件 `docs/reports/g-orch-smoke-verify-20261109.md`
- 不改任何脚本、测试、工单、主表
- 不提交 git、不打 tag
- **不要**临时改名、隐藏或删除 `config/.env`

## 回执要求

按本载荷末尾追加的「回执格式契约」写收尾标记。

## 执行提示

工程测试解释器：`tools\venv-openjarvis\Scripts\python.exe`（Python 3.13.16）
pytest 必须带 `-o addopts=`
