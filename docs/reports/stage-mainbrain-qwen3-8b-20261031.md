# UltimaAgent 主脑 qwen3-8b 无审查版切换阶段报告

- 工单：`wo-ultimaagent-20261031-0010`
- 日期：2026-10-31（Asia/Shanghai）
- 执行端：Codex
- 工程解释器：`tools/venv-openjarvis/Scripts/python.exe`（Python 3.13.16）
- 证据目录：`docs/reports/evidence/mainbrain-qwen3-8b/`
- 当前结论：T0、T1、T2 已通过；T3 的回归、内存与报告门已通过，冻结命令待执行。

## T0 环境盘点与模型实测对比

- [x] C1 `ollama list` 基线确认 `qwen2.5:14b`（9.0 GB）仍在，`nomic-embed-text`（274 MB）未动。
- [x] C2 指定模型拉取成功；短名 `qwen3-8b-uncensored` 建立成功，与源模型同 ID `6d7230a92342`、大小 5.0 GB。
- [x] C3 两模型用同一脚本同一参数完成 52 项指标样本（5+5+5+27+10），含首响应和 `ollama ps`。
- [x] C4 预热/启动盘点完成：无可执行预热命令写死 14B；`scripts/start-ultima-agent.ps1:21` 有一处启动注释引用，T2 同步。
- [x] C5 正式证据：`t0-probe-20261031-121741.txt`。

T0 Gate：通过。

## T1 选型定案

| 五项指标 | qwen2.5:14b | qwen3-8b-uncensored | 14B 九成门槛 | 判定 |
|---|---:|---:|---:|---|
| 人设五条 | 100.00% | 100.00% | 90.00% | 通过 |
| ≤2 句 | 100.00% | 100.00% | 90.00% | 通过 |
| banned 原始输出无命中 | 60.00% | 60.00% | 54.00% | 通过 |
| 9 工具原生调用（27 样本） | 62.96% | 85.19% | 56.66% | 通过 |
| JSON 结构输出（10 样本） | 100.00% | 100.00% | 90.00% | 通过 |

选型结论：五项均达到 14B 基线九成，采用指定的 `qwen3-8b-uncensored`；无需拉取或切换任何回退候选。8B 的 `ultima_subagent` 三个样本均改选了底层直接工具，这是已记录弱项，但九工具聚合指标仍显著高于 14B，且不改变工单封闭判定。

性能与资源：14B/8B 驻留分别为 9.5/5.4 GB，实降 4.1 GB；8B 首次冷加载较慢（64.861s），热态首响应均值约 0.071s，快于 14B 的约 0.386s。

T1 Gate：C1 判定、C2 回退规则核对、C3 结论落盘均通过。

## T2 切换接线

- [x] C1 `agent_server.py:46` 仅把本单模型值改为 `qwen3-8b-uncensored`；`ENGINE_KEY`、8756、AGENT、TOOLS 与其余逻辑不动；专用解释器 `py_compile` 退出 0。
- [x] C2 `scripts/start-ultima-agent.ps1:21` 的启动注释同步为新短名；未发现可执行预热命令写死 14B。
- [x] C3 真实重启 8756；`/health` 返回新模型、`native_react` 和 9 工具；启动日志无 RU-05 失败行。
- [x] C4 现有真机文本探针完整通过 interaction → agent_client → 8756 → Ollama → filter_reply，HTTP `/ask` 200，输出 2 句且 banned 命中为空。

证据：`docs/reports/evidence/mainbrain-qwen3-8b/t2-switch-20261031-122004.txt`。

T2 Gate：通过。

## T3 回归收口与冻结

- [x] C1 专用解释器全量回归最终为 `786 passed, 120 subtests passed, 0 failed`（301.33s）。首次运行因瞬时 DNS/SSRF 判定出现 5 个 `example.com` 相关失败；目标文件立即复跑 4/4 通过、DNS 恢复公网解析，未改代码；首次失败完整保留在证据中。
- [x] C2 生产同口径 16K context `ollama ps`：14B=12.0 GB，8B=7.3 GB，下降 4.7 GB；恢复 8B 后真实 `/ask` 与 `/health` 再次通过。
- [ ] C3 commit、tag `ultimaagent-mainbrain-qwen3-8b-20261031`、`git push --tags`：待执行并由命令回读核验。
- [x] C4 本阶段报告已覆盖逐 Gate 数据、首次失败诊断、内存数据、回滚与越界声明。

证据：`docs/reports/evidence/mainbrain-qwen3-8b/t3-regression-memory-20261031.txt`。

T3 Gate：C1/C2/C4 已通过；C3 完成后才进入 T4。

## T4 八字段回执

冻结成功后在最终执行端回执中输出。

## 越界声明

截至 T3-C2 无越界。未删除 `qwen2.5:14b`，未改 `nomic-embed-text`、KWS 基线、`voice_profile.py`、`voice-listen-daemon.py`、工单 C/D 约束栈；未拉取非指定模型或依赖。`agent_server.py` 中执行前已有的 HUD 事件总线差异原样保留，不纳入本单提交。
