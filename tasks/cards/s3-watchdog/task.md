# 任务卡：s3-watchdog
- **task_id**：s3-watchdog
- **标题**：看门狗（循环防护 + 进程守护）
- **优先级**：85（P0）
- **reasoningEffort**：low
- **category**：infra　**skill**：engineering
- **依赖**：s3-bus-kernel
- **登记核验**：已查注册表，无重复组件；承接 s2-persist 全部职责；依据 docs/plans/jarvis-reverse-architecture-20261026.md §3.6.1（看门狗防线）、docs/specs/plugin-bus-spec.md §12

## goal
看门狗 M22（LoopGuard 循环防护 + 进程守护）：
1. LoopGuard 循环防护：重复调用判定、乒乓检测、轮询预算、上下文压缩判定；单回合超时 abort 与流式空闲超时；
2. 进程守护：8756 端口无监听时自动拉起 agent_server（复用 scripts/start-agent-server.ps1），连续失败 3 次停止并留日志；
3. 守护进程与业务进程分离（独立进程，不内嵌）；
4. 异常熔断与回滚：routing 插件 5 分钟内 ≥3 次 error 主动回滚（与总线联动）；
5. 开机自启：计划任务登录时运行、Hidden、零弹窗（对齐 codex-task-queue-spec §5 零弹窗纪律）；
6. 日志留痕：自启/拉起/失败/熔断动作写 data/logs/。

**禁止**：
- 禁止改动语音 daemon / 悬浮球进程管理；
- 禁止安装第三方守护软件；
- 禁止修改系统级配置之外内容；禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：重复调用/乒乓/轮询预算/超时防护逐项生效（构造用例验证）
- [ ] ACCEPT-2：手动停 agent_server 后 60 秒内自动拉起，health 恢复 ok
- [ ] ACCEPT-3：连续失败 3 次后停止重试并留日志（不无限循环）
- [ ] ACCEPT-4：routing 插件 5 分钟 ≥3 error 触发回滚，与总线联动
- [ ] ACCEPT-5：守护进程独立于业务进程运行
- [ ] ACCEPT-6：自启注册 Hidden 无弹窗；运行期窗口枚举计数 0
- [ ] ACCEPT-7：日志完整（自启/拉起/失败/熔断）
- [ ] ACCEPT-8：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（scripts / src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：看门狗（承接 s2-persist） |
