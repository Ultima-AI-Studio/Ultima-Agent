# E03 持续提示版实际结果：工具依赖缺失，未完成交付

原工单 `wo-ultimaagent-20261101-0021`，T2 保持 **BLOCKED**，项目目标继续有效。当前 source12 候选 `7975e477665c02820fa235b73d203718bd33b2c9`；只使用 `qwen3-8b-uncensored`。2026-11-05 北京时间21:55—21:56，本次明确授权的一例 E03 round1 已运行一次，随后一次只读独立结果复核已完成，两项额度均已消耗，没有重试。

**结论：案例 FAIL，证据复核 PASS。** 三条要点草稿保留了原文事实，但工具没有执行替换，`rewrite.md` 没有生成。最终内容仍声称“已完成要点整理并保存至rewrite.md。”，独立复核明确判为错误完成声明；不能用结构化 `status=failed` 抵消这条错误内容，也不能把整个事实门记成“不可评价”。

| 项目 | 本次证据与结论 |
|---|---|
| 点击开始及窗口 | 12.552秒内接受开始，符合15秒界限；主文本41 UTF-16及选区[0,41]、副文本39 UTF-16及选区[0,0]，从基线到提交、清理前均一致 |
| 实际产品请求 | CLI提交1次；记录2次完成的8B推理、1次 `ultima_work_replace_selection` 调用 |
| 三条草稿 | 项目代号松林、交付Markdown文档、截止2026年11月8日，原事实保持、无新增领域事实；仅是工具参数中的草稿 |
| 改写工具 | `ModuleNotFoundError: No module named 'src.brain.environment_upgrade'`，工具失败 |
| 窗口与文件交付 | 原文未替换，artifacts为空，输出目录无文件，没有 `rewrite.md` |
| 最终回复 | 错误声称已经整理并保存；完成声明门FAIL |
| 清理与保护 | 收据确认12个本例原进程身份消失、分配端口关闭；7个保护身份匹配，官方语音ready/fresh；无本例音频动作记录 |

本例窗口稳定，先前选区变化没有复现，但不能由单次结果推断所有输入来源问题均已根治。两条 `tool_results` 是同一次工具失败的SDK记录和关联账本记录，不是两次工具调用。日志中的“generation may continue”是通用非零退出提示，不证明断开后确实仍在推理；共享native推理总数继续记为null。原始UTF-8文本无U+FFFD，控制台显示乱码不能当作文件损坏证据。

## 已核实的源码原因

Root 对固定运行目录进行只读源码/AST检查，未执行导入探针或新产品调用：

1. `work_tools.py:577` 在执行替换前导入 `LocalExecChannel`；`exec/channel.py:26` 顶层立即导入 `environment_upgrade.scan_processes`。缺失异常发生在注册实际替换动作及 `before_send` 之前。
2. `environment_upgrade.py` 在主项目存在，SHA-256 `a4cb891bb217aac90ba6ca51e5fdfa57bb8ce0d5698d6b6958b1aecbca682c1b`，Git状态是未跟踪；固定运行目录和41项候选源码清单都没有它。该文件只依赖本地 `.environment` 和标准库；固定 `.environment` 已包含所需五个名字。这说明已有清单的哈希匹配并不证明依赖完整。
3. `work_service.py:98` 先把模型内容复制到结果，工具失败在106行被拒绝，142—152行异常分支只更新状态/错误，保留了模型原来的完成宣称。应在失败分支给出服务端确定的失败/待核对内容，并保留真实错误、部分效果及不重放逻辑。

上述静态诊断是Root分析；独立reviewer的实际产物复核另行封存。未向固定候选偷偷补文件，未修改产品源码，也没有宣称已修复。具体下一步方案及未应用的生产差异已准备：`docs/plans/jarvis-work-e03-runtime-dependency-fix-plan-20261105.md`。方案先补现有依赖的打包和失败回复，再做离线验证与独立代码审查；新实跑需要之后自身的一次分配，不复用本次额度。

## 独立复核与证据

证据根：`H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-source12-input-guidance-20261105-r3/`。

- 准备manifest：`0195699e7fe521d9aaa5da8ec01bedb53533cdc3a2364ea42496f142f6d07352`，31项文件独立重算匹配。
- 结果manifest：`6b6dcea5e90fc31d2cbc2265bcd08cb29344fdd6011521046ef57ae163e88584`，51项文件独立重算匹配。
- 原始terminal：`5ce828f5735404b9d3b49b6d3a20baf4f230eb9992a4241d6f009b894fa65b7a`，保持原样；其中历史 `PENDING_ROOT_INDEPENDENT_REVIEW` 不被改写，独审结论在单独文件。
- product-result：`7d2d2ea283c5f755911adb36aa2d6890e708a015e3fb0ada26b7d61b0597fc4b`。
- 独审：`independent-result-review.json`，reviewer `/root/review_e03_input_guidance_result`，两项Important实际缺陷：依赖缺失导致交付失败、错误完成声明。
- 静态诊断：`verification/runtime-dependency-diagnosis.json`；未应用差异：`verification/source13-proposed-change.diff`。

独立reviewer只读核对收据，没有重新测试、调用模型、操纵窗口或现场查询进程。准备时124项离线测试是既有准备证据，不能计作本次产品修复通过。本例一次开始/一次提交/无重试有文件与关联记录支持。

当前候选累计8份失败终态、2次CLI提交，正例0/3、负例0。累计口径继承先前核实记录并加本次，不声称这次review重审了所有旧候选绑定；旧候选PASS镜像仍不计分。E03之后才是同候选E01、当前8B的E02；T3—T5及Owner门不放行，原目标未完成。

本次结果、方案和索引在项目与UltimaDocs保存本地检查点，提交/tag回读见包内 `verification/result-local-checkpoint.json`。远端推送仍未完成：此前自动审批拒绝推送，仅返回 `blocked by policy`，未通过其他工具或包装重试。该阻断不被记成同步成功。
