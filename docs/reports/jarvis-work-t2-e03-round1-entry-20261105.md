# UltimaAgent T2：当前候选 E03 round1 入口已通过独立审查

原工单 wo-ultimaagent-20261101-0021，日期 2026-11-05。

**当前候选 E03 round1 的正式入口已完成，99 项离线测试通过，独立审查两项阻塞问题均已闭合。尚未签发产品用例 authority，也没有在本轮调用模型或操作测试窗口。T2 仍 BLOCKED，当前候选正例 0、负例 0。**

前一轮用户授权的一次夹具诊断已 COMPLETE/UNCHANGED：两窗口 41/39 UTF-16 文本保持，cleanup/audit/boundaries PASS；额度已耗尽。这证明该次没有复现清空，不能证明 R31 间歇问题已根治，也不计 E03 验收成绩。旧 round1 PASS 属于旧候选；正式验收从当前候选 round1 开始。

候选固定为 7975e477665c02820fa235b73d203718bd33b2c9，模型固定为当前 qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。产品源码与默认设置没有修改。新入口复用已有 Case/Owned、夹具与原观察命令、机械检查及清理前副作用一致性核验，避开已消费的旧 round2 控制器入口。

首次独审发现两项 P1，基包及 NEEDS_FIXES 收据完整保留：

- 实际 Owned.cleanup 再次写入 stop 标记时可能抛错，跳过测试进程清理。fix1 在实际清理函数中记录该错误并继续原有精确身份清理、等待退出、日志关闭和回执；结果仍为 FAIL。
- 最终完整预检之后，窗口激活和观察可能跨过准入有效期。fix1 保留激活前完整检查，在最后观察后、CLI 提交前重新校验原凭据绑定，并在文件读取之后再次采样时间；不刷新凭据，不新增原生检查造成的等待。

七项新增回归在基包上复现失败，修复后全套 **99 passed in 6.60s**（57 项入口/执行接线 + 42 项保留输入审计）。首次回归运行还暴露了 mock ready 标志遗漏；该记录也保留，修正测试后七项均出现预期 RED，再完成修复。独立 reviewer 对测试代码与日志、36 项封存文件、7 项完全复制依赖及单点 controller 差异、12 个 Python AST、41 个候选源码文件进行了只读核验，同一 reviewer 闭合 PASS；reviewer 未重新运行测试。

另一次真实依赖只读检查确认当前包的导入路径、保护基线绑定、候选 guard 和固定 41 UTF-16 样本一致。本轮最终保护回读确认七个 PID 的创建时间、可执行文件、父 PID 与命令摘要匹配，官方语音状态 ready/fresh 为 true；未发现匹配的真实用例执行进程。没有重启或结束保护进程。

时限保持原义：**60 秒是 native/source 预检凭据新鲜度，authority 最大 120 秒**；CLI 300 秒、SDK 1800 秒、控制器等待 315 秒，以及 max_turns 10、work_max_tokens 2048 均不变。fixture-only 的诊断完成计时未引入产品验收。

修订包：H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e03-source12-acceptance-20261105-r1-fix1。

- manifest SHA-256：a4fdb70c9e062b34cec82b1cbe2b9443d51386fd651269023b824d38531ea43d。
- 独审回执：independent-review-closure.json；其 SHA-256：01fe4c28fa60eeb29ab8fda066a05f90da81c85edd365ef002187d6f8f3112a3。
- 差异与测试：verification/review-fix.diff、verification/red-review-findings-2.log、verification/green-review-findings.log。
- 实际依赖与保护回读：verification/import-binding-readback-fix1.json、verification/final-protected-readback.json。
- 上版 manifest 7078209f8881b4278a07c121b280bf7a9704ccb2a38aca2a3eed8c3e8781eb0d 保留；actual/、release/ 在两个正式入口包中均不存在。

下一步的具体提案已准备：只运行当前候选的一次 E03 round1，当前 8B 将固定测试选区整理为三条要点、替换该选区并保存相同的 rewrite.md；随后对实际产出做一次只读独立事实复核。只用自建测试窗口和隔离输出，不重试，不调用音频，不改生产默认；副窗口必须不变。最近一次明确授权只涵盖已完成的 fixture-only 诊断，不能把它当作产品调用额度，因此该实际用例仍待范围确认和 fresh WIP/保护/模型预检。

机械成功只产生 PENDING_FACT_REVIEW，须核验“松林、Markdown 文档、2026年11月8日”三项原事实、实际窗口替换和 rewrite.md 一致后才可能给本例成绩。E03 其余正例/负例、同候选 E01、当前 8B 的 E02，以及 T3—T5/Owner 门仍未完成。准备包独审、离线测试和文档检查点均不能代替最终产品交付。
