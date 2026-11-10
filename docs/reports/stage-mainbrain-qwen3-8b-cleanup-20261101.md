# UltimaAgent 主脑 qwen3-8b 残留清理阶段报告（2026-11-01，2026-11-08 续跑）

## 工单

- 工单：`wo-ultimaagent-20261101-0013`
- 目标：清理 8B 切换后的残留引用并完成回归、冻结与八字段回执。
- 当前结论：2026-11-01 的 `BLOCKED_BEFORE_T0` 已由 2026-11-08 全局登记解除；本轮 T0–T3 均 `PASS`，冻结 tag 为 `ultimaagent-mainbrain-qwen3-8b-cleanup-20261101`。

## 准入预检

| 检查项 | 结果 | 证据 |
|---|---|---|
| 项目 INDEX 与必读权威规范 | PASS | 已依次读取项目 INDEX、G-TASKFLOW-001、Codex 执行端范式、根目录范式、根 INDEX、G-WO-NAME-001、项目接入与派发范式及工程铁律 |
| 前置冻结 tag | PASS | `ultimaagent-mainbrain-qwen3-8b-20261031^{commit}` 可解析为 `09a7abc77ebb7fd9d4a9aba6cc9dc82314a5649d` |
| 指定解释器 | PASS | `tools\venv-openjarvis\Scripts\python.exe --version` = `Python 3.13.16` |
| 当前执行身份 | PASS | PID 24460 为本工单 `codex.exe exec`；未发现 0027、旧监视器或另一 UltimaAgent 执行会话 |
| 全局主表登记 | PASS | `global-queue-index.md:13971` 命中本工单，状态 `pending`；主表仅只读核对 |
| 工作树隔离 | PASS | 当前分支有 0021/E02 既存改动；与本单写域不重叠，保持原状并在提交时逐文件显式暂存 |
| 开源替代排查 | PASS / 不适用 | 无自研、无新模块；仅既有模型短名、配置和断言同步 |

## Gate 状态

| Gate | 状态 | 说明 |
|---|---|---|
| T0 | **PASS** | 5 文件 `py_compile` 退出 0；除 `engine.py:120` 明确保留的 14B 次级回滚键外无旧主动引用，见 `t0-gate.txt` |
| T1 | **PASS** | 首跑暴露 Ollama `:latest` 规范名差异；有界修正短名断言后，定向 `21 passed`、五目标文件 `66 passed`，verify `5/5`，见 `t1-gate.txt` |
| T2 | **PASS** | 全量 `1008 passed + 122 subtests passed`、0 failed；Ollama 双模型在位；8756 health 为 8B；残留均为回滚键/测试候选或历史证据，见 `t2-gate.txt` |
| T3 | **PASS** | 实现提交 `da85b88d33cdff69698418785aa63b4bce095e60`；仅显式暂存本单 15 文件；收口提交后 tag 创建、免代理推送并远端回读，见 `t3-gate.txt` 与执行端回执 |
| T4 | **PASS** | 八字段回执由执行端在冻结远端回读后输出 |

## T0 说明

工单同时写有“`engine.py` 保留 14B 次级回滚键”和“五文件 grep 14B 零命中”。两者不可同时成立。本轮按更具体且安全优先的禁止项执行：不得删除 14B 回滚能力。因此 T0 的可执行判据为四文件零命中，`engine.py` 仅允许 `_model_keys` 的唯一回滚键命中。该命中不代表主动默认模型；首键与所有默认值均为 `qwen3-8b-uncensored`。

## T1 有界修复

五目标文件首跑为 `65 passed, 1 failed`。唯一失败是 `ollama list` 返回规范全名 `qwen3-8b-uncensored:latest`，而工单给出的短名断言仅接受无 tag 字符串。测试断言改为接受短名或同短名的显式 tag，保持“8B 模型在库”语义，未修改被测实现。修正后失败文件 `21 passed`，五目标文件全套 `66 passed`，verify 脚本 `5/5`。

## T2 全量回归与运行态

- 指定解释器：`tools\venv-openjarvis\Scripts\python.exe`，Python 3.13.16。
- 全量回归：`1008 passed, 36 warnings, 122 subtests passed in 217.51s`，退出 0，0 failed。
- Ollama 库：`qwen3-8b-uncensored:latest`（5.0 GB）与 `qwen2.5:14b`（9.0 GB）均在位；`nomic-embed-text:latest`（274 MB）保留。
- Ollama 驻留首样本：14B 临时占用 12 GB（16K context，15%/85% CPU/GPU）及 embedding 323 MB；到期后复读仅剩 embedding 323 MB。未人为停止、卸载或重启模型。
- 常驻服务：`127.0.0.1:8756/health` 返回 `model=qwen3-8b-uncensored`、`agent=native_react`、9 工具；PID 17136 自 2026-11-03 启动，本单未重启。
- 测试临时数据：运行前对 `data/test-tmp` 2097 文件做字节快照；结束后删除新增 26 个、恢复被覆盖 3 个，tracked diff 为空。

## 残留盘点与无害性

| 类别 | 残留 | 结论 |
|---|---|---|
| 主动实现/配置 | `orchestration/engine.py:120` | 唯一实现残留，明确要求保留的 14B 次级回滚键；8B 为首键 |
| 测试/verify | `test_orchestration_m4.py:74`、`test_bootstrap_m6.py:205,217`、`verify_bootstrap_entry.py:53` | 仅验证回滚层级/候选池；高复杂度与首键断言均为 8B |
| scripts/config | 无 | 无 14B 残留 |
| 历史 docs/tasks/logs | 旧工单、里程碑、计划、报告、stderr/receipt | 历史事实、迁移说明或只读对照提案，不参与运行 |
| data/evidence / credential audit | 冻结快照、主表 before 副本、credential key-id 审计 | 不参与运行；未改历史证据，未暴露凭证值 |

完整分类与代表路径见 `evidence/mainbrain-qwen3-8b-cleanup/t2-gate.txt`。主动默认/主路由的 14B 引用为 0；允许保留项不构成主脑 14B 残留。

## T3 冻结

- 实现提交：`da85b88d33cdff69698418785aa63b4bce095e60`（`工单 0013 8B 残留引用清理`）。
- 暂存纪律：两次提交均逐文件显式 `git add -- <paths>`；未使用 `git add -A` 或 `git add -u`；既存 0021/E02 改动未混入。
- 冻结标签：`ultimaagent-mainbrain-qwen3-8b-cleanup-20261101`，指向包含本节与 `t3-gate.txt` 的收口提交。
- 推送：仅推该 tag，显式清空 `http.proxy`、`https.proxy` 与 GitHub 专属 proxy；本地 `rev-parse` 与远端 `ls-remote` 的最终 SHA 一致性由执行端回执列出。

## 开源替代排查

无自研/无自写模块。本单仅同步已有 Ollama 模型短名、路由顺序、配置与测试断言，不引入第三方组件或新算法，因此无需替代选型。

## 越界声明

最终仅改动/纳入工单点名的 4 个仍有残留的实现/配置文件、5 个测试/verify 文件及本单阶段报告/证据；`agent_server.py` 已正确，仅编译与运行态核验。未修改 HOST/PORT/TOOLS/AGENT/工具注册/路由/RU-05、nomic-embed-text 与记忆结构、KWS/voice_profile/voice-listen-daemon、工单 C/D 约束栈；未下载/删除模型，未停止或重启 agent_server/Ollama，未写全局主表。仅停止了本工单自行发起且已核实身份的 3 个滞留只读 grep PowerShell 子进程；用户后台服务保持不变。测试临时文件已恢复/清理，不纳入提交；既存 0021/E02 工作树改动保持未暂存、未提交。
