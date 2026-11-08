# 任务卡：orb-w9-receipt-contract

- **task_id**：orb-w9-receipt-contract
- **stage**：G-ORCH 编排层（v0.1）
- **标题**：回执契约随派发载荷下发（G-ORCH 端到端复验）
- **创建**：2026-11-09 · 卡点 B 修复后的端到端复验

## goal

验证派发器自动追加的「回执格式契约」是否真能让执行端写出判读器要求的标记词，使一条内容完整的回执被判为有效（`receipt_valid: true`、`state: audit`），而不是落到阻塞。

顺带产出一个可留档的验证记录文件。

## acceptance[]

| 编号 | 判据 | 判定方式 |
|---|---|---|
| ACC-1 | `docs/reports/g-orch-smoke-verify-20261109.md` 存在且非空 | 文件存在性 + 字节检查 |
| ACC-2 | 文件内容写明本次验证对象是回执契约，且不超过 12 行 | 逐行计数 + 内容核对 |
| ACC-3 | 只新增该文件，未改动其他已跟踪文件 | `git status --short` 除该文件外无改动 |
| ACC-4 | 越界声明写明「无」或列明 | 回执自述 |
| ACC-5 | 回执含派发载荷要求的交审标记，使判读器判为有效 | 派发器 `done.json` 的 `receipt_valid` 为 true |

## boundary

**做**：新建上方那一个记录文件。
**不做**：不改任何脚本、测试、工单、主表；不提交 git；不打 tag。
