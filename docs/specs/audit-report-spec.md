# UltimaAgent 统一审计报告规范

版本：1.0

适用范围：`wo-ultimaagent-20261108-0026` 起的单 Agent 独立审计报告

权威生成器：`src/brain/guardrails/audit_report.py`

## 1. 目的与边界

统一报告只呈现现有确定性审计结果，不建立新的审计角色、严重度或交付门。
分级固定复用 `reviewer.py` 的 `blocker / major / minor`；交付门以
`ReviewResult.ok` 为第一依据。LLM 审计输出只能先经严格适配器转换为
`ReviewResult`，不能在报告层覆盖 gate。

报告生成使用 Python 标准库，不引入模板引擎或另一套 JSON Schema 依赖。

## 2. 固定报告骨架

每份报告必须按以下顺序包含七个二级小节，标题不得自由改名：

1. `报告头元信息`
2. `审计范围与方法`
3. `分级汇总`
4. `逐项发现`
5. `交付门结论`
6. `证据索引`
7. `复测记录`

生成器输出 UTF-8 Markdown，文件以单个 LF 结尾。

## 3. 字段契约

### 3.1 报告头元信息

| 字段 | 必填 | 对齐来源 | 说明 |
|---|---:|---|---|
| `work_order` | 是 | receipt `work_order` | 原工单号，不创建替代身份 |
| `report_id` | 是 | 报告身份 | 本报告的稳定唯一标识 |
| `generated_at` | 是 | audit_log `ts` | ISO 8601 UTC 时间 |
| `reviewer_role` | 是 | ReviewResult `role` | 仅 `eng.audit` / `eng.security` |
| `audit_session_id` | 是 | audit_log `session_id` | 本次审计会话标识 |
| `source` | 是 | audit_log `source` | 审计记录来源模块 |

### 3.2 审计范围与方法

- `scope`：被审计的契约、代码、报告或证据边界。
- `methods`：实际执行的方法，例如 unittest、hash 链校验、回执独立回读。
- 未声明时仍保留小节并明确显示“未声明”，不得把空白解释为已检查。

### 3.3 分级汇总与逐项发现

- 汇总固定按 `blocker / major / minor` 三行输出，计数来自
  `ReviewResult.as_dict()`。
- 每项发现固定呈现序号、`severity`、`item`、`detail`；不得增加
  `critical` 等平行分级。
- 无发现时明确显示“无发现”，不因此自动判定交付通过。

### 3.4 交付门结论

结论仅允许：

| Gate | 条件 | 语义 |
|---|---|---|
| `FAIL` | `ReviewResult.ok == false` | blocker 未清零，禁止交付 |
| `HOLD` | `ReviewResult.ok == true` 且证据索引为空 | `EVIDENCE_REQUIRED`，不得出现“通过”结论 |
| `PASS` | `ReviewResult.ok == true` 且至少有一条完整证据 | 确定性 gate 与证据门均满足 |

报告层不得把 `major/minor` 隐藏，也不得用 LLM 的自报 gate 替代上述计算。

### 3.5 证据索引

每条证据字段固定为：

| 字段 | 对齐来源 | 说明 |
|---|---|---|
| `evidence_id` | 报告内部引用 | 稳定 ID，例如 `EV-001` |
| `path` | receipt `evidence[].path` | 可独立读取的证据路径 |
| `kind` | receipt `evidence[].kind` | `report/test/log/code/...` |
| `summary` | receipt `evidence[].summary` | 证据实际证明的内容 |

四字段任一为空时生成器 fail-closed，不输出报告。路径存在性由独立验收和
`ReceiptValidator` 复核；生成器不把字符串存在误当成文件已验证。

### 3.6 复测记录

每条复测固定包含 `command / result / evidence`。`evidence` 必须指向证据 ID
或明确证据路径；无复测时显示“未复测”，不得推断为通过。

## 4. Markdown 安全与确定性

- 表格值中的 `|` 转义为 `\|`，换行转为 `<br>`，避免审计数据改变报告结构。
- 字段顺序、章节顺序、严重度顺序固定，便于机检与 diff。
- 生成器不执行模板表达式、不解析 HTML、不访问网络。

## 5. 机检要求

- 单测必须断言七个固定小节全部存在。
- 单测必须覆盖 blocker→FAIL、证据为空→HOLD 且全文无“通过”、
  有证据且 blocker 清零→PASS。
- 示例报告必须由 `write_audit_report()` 生成，不得手写模拟生成器输出。
