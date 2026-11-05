# UltimaAgent T2：输入来源诊断准备独审闭合

日期：2026-11-05；原工单：`wo-ultimaagent-20261101-0021`。

**同一独立 reviewer 已完成审查及唯一缺陷的限定复核，诊断代码准备通过；E03 与 T2 仍未通过。** 用户授权为“一次只读独立审查”。全程只有一名 reviewer，首次检查补丁与证据归属，修复后仅复核其唯一发现及修复引入的风险，没有新增运行授权。

首次包 manifest `90926b30faaed229eee1e8b206b506ac53a39fa7fe9b0a17a8bb2d751717515b` 的结论为 NEEDS_FIXES。审查发现 `ORIGIN-PREFIX-01`：记录中同一祖先可被描述为不同的祖先链，原校验却仍通过。这会影响对嵌套输入的解释。首次包和失败结论已原样保留。

修订仅为每个观察到或被引用的消息 ID 建立唯一描述：消息编号、窗口句柄、接收线程和完整祖先前缀。每次引用必须一致。原 recorder、fixture adapter、controller 和 legacy tests 均未修改。修订在新目录 `e03-fixture-input-origin-20261105-fix1` 中完成，未改产品候选代码。

新增测试先证明旧代码会错误接受三类矛盾记录，再验证修订会拒绝它们，并保留三种合法嵌套情形。**42 项离线测试通过，包含全部原 36 项和新增 6 项。** 同一 reviewer 只读核验了 12/12 个文件哈希、实际 diff、5 个 Python 文件的语法、原测试模块的全部 28 个顶层 AST 节点，以及已存在的 RED/GREEN 日志；没有重跑测试或执行代码。限定复核为 PASS，绑定 fix1 manifest：

`c6cf3099e916ccc86ae1f6719637a5ba06e4eb0ba18554867f77e972984735c2`

首次独审也确认了验收归属纠正：source12 目录中的 round1 通过记录来自旧 `118ba152...` 候选，不能转移给当前 `7975e477...`。在明确枚举的当前 source12 原始用例范围内，5 个不同终态全部失败，1 次 CLI 提交，正例通过 0、负例通过 0。历史 11 月 2 日的完整通过门和旧 round1 PASS 均保留。该结果经独立核对，不是手工清零历史成绩。

R31 的现场结论仍是：初始文本 41 UTF-16 单元，冻结基线为空；同一控件记录一次 41→0 的 `EM_REPLACESEL` 变化；server/CLI 之前停止，cleanup 和 boundaries PASS。用户无法确认当时是否输入，现有日志无法确定操作者。**本次没有新增 Windows 现场用例、模型调用、录音或播放，因此不能宣称“文本被清空”已修复。** 当前候选和当前社区 8B 均保持，14B 不使用。

接下来的工作是准备一次有界的夹具诊断：保持初始化、置前台与冻结基线读取顺序，只采集缺失的消息来源和嵌套证据；不启动产品 server、work CLI 或模型，不重置文本，不修改输入法。该运行 wrapper 尚未提供或审查，新运行额度尚未签发；原 R31 `case_cap=1` 已消费且禁止重试。准备通过不等于运行放行。

正式产品验收顺序继续为：当前候选 E03 round1→round2→round3→原负例，随后同候选 E01 回归，再处理 E02。T2 出口未通过前，T3—T5 和 Owner 门均未放行。

当前状态文件更新为“诊断代码已独审通过、未运行”。原 manifest 中的 `current-run.json` 是准备时的外部状态快照；审查后的状态推进另存修改前副本与哈希，不改旧 manifest。历史 source10 一次性脚本如需再用，必须明确读取保存的 466 字段旧状态或迁移到 schema 2；它们没有重放权限。此次没有找到当前产品或队列对该文件的读取实现，但不能据此断言所有外部读取方均兼容。

主要证据：

- `data/evidence/jarvis-work-capability/T2/e03-fixture-input-origin-20261105/review/independent-review.json`：首次 NEEDS_FIXES 与独立证据核验。
- `data/evidence/jarvis-work-capability/T2/e03-fixture-input-origin-20261105-fix1/independent-review-closure.json`：同一 reviewer 的限定复核 PASS。
- `data/evidence/jarvis-work-capability/T2/e03-fixture-input-origin-20261105-fix1/verification/green.log`：42 项离线测试。
- 两份报告与文档镜像已落盘，本地准备 tag 已保存。GitHub 推送仍因配置的本机代理无法连接而未完成；推送失败不改变本地检查点，也不构成产品验收。
