# 验收证据 · s3-heartbeat（主动心跳（M27））

- **task_id**：s3-heartbeat
- **状态**：COMPLETED
- **验收时间**：2026-10-27

## ACCEPT 清单
| 项 | 结果 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | TICK 周期调度生效（test_tick_cycle） |
| ACCEPT-2 | PASS | 消息抢占：新消息到达心跳让位（test_message_preempt） |
| ACCEPT-3 | PASS | 空闲思考预算封顶：超过即静默不无限自转（test_idle_budget_capped） |
| ACCEPT-4 | PASS | 主动发言边界：仅空闲态发声，speaking/listening 等待（test_speak_only_when_idle） |
| ACCEPT-5 | PASS | 忙态等待后预算复位（test_budget_reset_after_busy）+ 回执自校验 0 issues |

## 产出文件
- `src/brain/heartbeat/ticker.py`
- `src/brain/heartbeat/tests/test_heartbeat_s3.py`（5/5 OK）
- `tasks/cards/s3-heartbeat/acceptance-evidence.md`、`receipt.json`

## 边界未触碰
- 未向 fileDomain 之外写文件；未扰动守护进程。
