# E02 source13 外层入口准备记录

原工单 `wo-ultimaagent-20261101-0021`，T2。当前 E01 固定样本 3/3、E03 同候选三正一负已通过；E02 真实研究、T2 出口与后续门仍未通过。

## 当前结论

用户在 `call_e84ac425972c431b843164937a72fe99` 授权同一 R1-followup 缺口的最小补修、离线验证及必要独立准备复核。补修已完成，完整离线检查 **89/89 PASS**，44.77 秒；当前精确源码独立复核待完成，准备门为 `NOT_READY_PENDING_HANDOFF_SOURCE_REVIEW`。实际 profile、模型与结果复核分配均为零。

产品候选固定 `269aca511d88412dbb9c15d23911138469a37aa2`；仅当前 `qwen3-8b-uncensored`，摘要 `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`。冻结产品工作树本次只读核验仍干净；B profile/SDK 与原 1,461 项依赖保持。当前七个保护身份仅有历史基线，本次未查询其生产运行状态。

## 补修行为与证据

此前等待循环只预留当前已知成员的清理成本。HELLO 晚到后再花两次各 15 秒身份查询，可能使余量不足；查询中才发现的解释器又会扩大清理范围。现在从启动前到资格确认完成，持续保留预计成员、启动器、未执行查询和可能的控制台观察成本。

- 原 `entry.start` 和 `NativeBackend.start/qualify` 在启动、HELLO 等待、HELLO 验证后、每次身份查询前后及句柄取得后检查余量。只有实际成员身份和只读句柄确认后才解除待确认状态。
- `Owned.cleanup`、原 `Deadline/PrivateIO` 与 275／310／315 秒截止保持；没有新增终止器。已确认无控制台的两个／四个成员仍预留 132／214 秒；新角色准入预留 195／277 秒，典型 reader 须在 origin 后 38 秒前准入。HELLO 等待保留 180／262 秒，典型等待在 origin 后 135／53 秒前结束。更保守窗口可能拒绝原本及时的消费者，不代表完整享有 275／310 秒消费时间。
- 新增 6 个 worker/reader 边界用例：安全到达、迟到、HELLO 校验期间越过边界。使用生产 start/qualify、原清理源码与真实 Deadline/PrivateIO；仅 OS 效果和时钟为合成替身。两次资格查询确实各消耗 15 秒，解释器在启动快照后才登记。检查成员消失、日志关闭、完整 10 秒终止准入及原 315 秒内最终证明。
- RED：6 项中 4 项失败、2 个安全路径通过；失败实际复现清理查询余量耗尽以及应拒绝时仍发生两次查询。修复后定向 6/6、完整 89/89。原 83 项均保留，原固定 B runner 557 项是另一份历史证据，不合并为产品验收数量。
- 本轮没有执行原生 worker/profile、模型、DNS/HTTP、窗口、音频或服务操作。离线 runner 的 Python I/O 拒绝记录为空；这不是整台电脑 OS 活动测量。任意 OS、文件阻塞或未知进程树下的无条件清理仍未获证明，5 秒文件余量只是保守余量。

## 封存及审查入口

证据根：`H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-root-entry-20261106`。

- 当前包 344 项，manifest SHA-256 `c5a0df11f2d1b060de841b47d6345eecf1640e70001dfa24b5664c7f40c6dfd7`。
- 当前运行输入 38 项，entry manifest SHA-256 `8b63f148aa43f923b85ac5fa97a40a358e4eff5ab85e7adb2dde8f29951e542f`。
- 定向与完整收据：`offline/handoff-red`、`offline/handoff-green`、`offline/handoff-full-green`；汇总 `verification/handoff-fix-readback.json`。
- 新权限记录：`verification/handoff-fix-authorization.json`。具体成本裁定：`inputs/handoff-cleanup-ruling.json`。
- 旧 227 项、284 项包与失败报告分别完整保存在 `history/reviewed-83312d5`、`history/reviewed-a19a00b`；两份旧 NEEDS_FIXES 仍有效描述其原源码，未删除或升级为通过。
- 当前精确源码交给新 reviewer 只读审查。审查 PASS 也仅允许准备门通过；实际原资料零推理接线验证仍须按 `execution-proposal.md` 另行明确分配。它可能进行原正常 SSRF 的受限 DNS，不调用模型；即使成功也不计入 E02 真实 8B 研究三轮。

本地 commit/tag 与 UltimaDocs 镜像将在检查点收据记录。远端 push 保留此前自动审批 `blocked by policy` 阻断，本轮不重试或绕过，不宣称已同步。
