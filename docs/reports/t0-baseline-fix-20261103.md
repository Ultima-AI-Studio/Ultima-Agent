# UltimaAgent 0025 T0 基线四红灯修复阶段报告

- 工单：`wo-ultimaagent-20261103-0025`
- 方案：`G-PLAN-0025`
- 执行结论：`T0/T1/T2 PASS`，完整工程门已全绿；状态转 `ready_for_review`。
- 收口边界：本报告不代签独立审计、Owner 真实体验或冻结 tag，不代 0022 commit/tag/push。

## 四项修复

1. **agent_server 用户问题边界（断言更新）**
   - 确认当前行为是模型输入获得有界化北京时间前缀，事件总线仍只保留裸用户问题。
   - 测试严格校验前缀格式、单空格边界、原问题完整后缀及 `message_in` 未泄漏前缀；未改 `agent_server` 生产行为。

2. **确定性时间直答（行为确认）**
   - 保留 0020 已确认的本地时间直答，不退回 Agent 自由回答。
   - 修复 `_cn_hour(10)` 边界越界，补齐 1/9/10/11/12 点表驱动断言，同时验证 Agent/Verifier 均不被调用。

3. **生产队列只读投影（行为确认）**
   - 只读 reader 正确解析 `tasks/...` repo-relative 路径，允许任务库内的 queue/stage 卡，并兼容 H1 中文标题。
   - 库外路径仍 fail-closed；生产库指定测试在完整门内通过且前后不变异。

4. **voice-next discontinuity reset（环境依赖）**
   - 按既有 lock 将 `soxr==1.1.0` 同步到指定的 `venv-openjarvis`，import 回读通过。
   - 真实 `soxr.ResampleStream` 路径下验证 framers/model cache 断开重置；未改 KWS/唤醒词/阈值/采样率/增益，未开启麦克风或播放。

## 证据链

| 阶段 | 结果 | 关键证据 |
|---|---|---|
| T0 | `PASS / RED_CONFIRMED` | 四个点名节点各自退出 1，根因依次归类为断言更新、行为确认、行为确认、环境依赖；`data/evidence/t0-baseline-fix/T0/gate.json` |
| T1 | `PASS / GREEN` | 定向 `11 passed in 9.35s`；累计 `32 passed, 2 subtests passed in 9.63s`；`data/evidence/t0-baseline-fix/T1/gate.json` |
| T2 | `PASS / FULL_GREEN` | 最终完整门退出 0，`932 passed, 36 warnings, 120 subtests passed in 142.52s`；JUnit 1052 cases，0 failures/errors/skips；`data/evidence/t0-baseline-fix/T2/gate.json` |

## T2 续跑记录

- 上一轮中断的 `full-src/` 不作验收，本轮从头执行指定完整命令。
- attempt 1：退出 1，`930 passed / 2 failed`。恢复会话的精简 PATH 漏掉已安装 Ollama CLI；补齐 PATH 后两个原失败节点 `2 passed in 11.03s`，无源码修改。
- attempt 2/3：各退出 1，均为 `931 passed / 1 failed`。`PreferenceStore` 以毫秒精度生成时间戳，无延时连续 upsert 会碰撞；10 次原节点隔离复现为 6 PASS / 4 FAIL。该目录是本单外的既有未跟踪输入，本单未改生产实现、未弱化断言，并保留全部失败证据。
- attempt 4：原命令完整自然结束，退出 0，作为最终 T2 gate。

## 边界与回读

- 最终 JUnit SHA256：`5E8E3FF674D7CA29C114B866250B60DFE9FE61E4D59A5D3F5098797630C96D62`。
- 最终 pytest log SHA256：`26281A145F6F105BF00575B6AF7D9949E57752E52BD346E4A5212DDBEC8D04F4`。
- KWS 权威基线 SHA256 仍为 `BA6AC90F2FE1509602F6C0085AE9580E9D8849EC9FD9E8319C232FF94805828E`。
- 7 个受保护 watchdog/agent_server/voice/daemon 进程的 PID 与启动时间全部与 T0 基线一致；本单未停止或重启它们。
- `tasks/tasks.json` 是进入本轮前已有的他单 M 状态；当前文件最后写入 13:01:05，早于本轮 T2 首次启动 13:15:56，本单不暂存、不提交该文件。
- 未使用默认 Python312；未改主脑模型/推理参数；未修改 KWS 基线；未播放、录音或调用麦克风。

## 后续门

本单执行产物已具备独立审计输入。只有独立审计、Owner 真实体验和冻结 tag 全部完成后，才能关闭 0025 并继续 0022 自身的验收冻结。
