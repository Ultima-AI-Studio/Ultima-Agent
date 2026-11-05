# UltimaAgent T2：E03 round1 单例失败，独立复核完成

原工单 wo-ultimaagent-20261101-0021，日期 2026-11-05。

**用户授权的一次 E03 round1 已执行，结果 FAIL。失败发生在夹具启动检查，产品 server/CLI 尚未启动，本例没有提交模型推理，也没有 product-result 或 rewrite.md。独立证据复核 PASS，案例验收 FAIL，事实核验为 NOT_EVALUABLE_NO_PRODUCT_OUTPUT。当前额度已消费，不重试。**

用户授权来源为 request_user_input_async/call_bb0bb9e67948461783de3269bdb5e149/0：“授权一次 E03，并独立复核产出（推荐）”。已使用本次新 authority、原预检 proof 和当前准备包，未复用 R31 或 fixture-only 额度。actual 下仅 e03-round1，一次 attempt，run exit 2。

候选仍为 7975e477665c02820fa235b73d203718bd33b2c9；模型仍为 qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。两处候选工作树、模型默认及生产语音/KWS保持。执行前完成来源、当前模型、七保护身份、WIP及独审绑定检查；准备包 99 项离线测试和独审 PASS 的结论仅属于准备层。

事件时间线（UTC；北京时间加 8 小时）：

| 事件 | 时间 | 证据 |
| --- | --- | --- |
| 本次 authority 签发 | 11:19:39.244069 | 绑定新用户授权与原 proof，最大120秒 |
| 单例 admission 消费 | 11:19:44.469316 | 独占 actual/e03-round1 |
| 两个启动探针完成 | 11:19:44.908–44.909 | 主41、副39 UTF-16，哈希符合固定样本 |
| 主窗口文本清空 | 11:19:45.115900 | EM_REPLACESEL，41→0，随后读回仍为空 |
| 审计闭合 | 11:19:46.343 | 两个窗口均有闭合记录 |
| 执行终态 | 11:19:57.153454 | FAIL；清理、审计和保护边界PASS |

实际错误为 Fixture audit startup probes incomplete or unexpected event arrived。两个 probe 均在；额外输入事件使启动检查拒绝。初始主窗口正确包含三项固定事实并选中，随后主窗口被清空。legacy 审计15条，其中probe 2、input 8、programmatic 1；origin消息24条并闭合。

EM_REPLACESEL 的来源为 0/unavailable，depth 0，无祖先，未识别发送进程。键盘消息为 hardware_or_uiaccess；不能据此确定是真人键盘、某个程序或断定键盘/IME导致清空。这里只确认清空及同期输入事件，完整根因仍未知。

副窗口在原始 UTF-8 文件中保持固定文本，含 U+2014、无 U+FFFD，39 UTF-16，SHA-256 fd914d31fab8a2a85e9fa2dc2920d7270295676f8a8da4a2af6ffa2412e6ec9d。早期工具显示中的替代字符没有对应原始文本变化；派生说明的纠正记录和此前版本均保留。

cleanup记录的四个owned/observe-only原身份均不存在；七个保护身份的创建时间、可执行文件、父PID和命令摘要匹配基线，官方voice run_id相同、ready/fresh为true。没有另行结束保护进程。context.port尚未分配，因此port_closed=true不能描述为关闭了一个已启动的产品服务器端口。audit PASS表示日志结构、闭合和计数吻合，并不表示窗口没有变化。

独立 reviewer 以只读方式核对36个封存文件、approval/authority/proof/admission绑定、terminal与stdout、事件哈希、代码先后顺序、原始副窗口文本和保护/清理收据。确认server/CLI启动语句均未到达、没有产品产物。**本例产品推理提交为0；共享daemon全局原生调用数量仍未知。** 没有产品输出，不能验收松林/Markdown文档/2026年11月8日这三项事实是否被模型正确保留，也不能验收三条要点、选区替换或同文保存。

证据根：H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e03-source12-acceptance-20261105-r1-fix1。

- 包 manifest SHA-256：a4fdb70c9e062b34cec82b1cbe2b9443d51386fd651269023b824d38531ea43d。
- 原 terminal SHA-256：4a43a012578ff53563f65f925821d1d3e7228a0ab2e26ca36b12aba7f89322f9。
- 独立结果收据：independent-result-review.json，SHA-256 eabd5491fb3e07a3eb8765214095bb1c3203fd2f3fa5c90b351135c49754f3a7。
- 原实际证据：actual/e03-round1；保持原 terminal 的 facts=PENDING_ROOT_INDEPENDENT_REVIEW，最终不可评价结论写在独立收据中。
- 只读回读：verification/e03-round1-result-readback.json、post-case-protected-readback.json；result-evidence-manifest.json为原始文件哈希清单。
- 原始actual/release内容留在本机；提交摘要、哈希和审查收据。

原R31和此前失败、一次未复现的fixture-only诊断、准备包首次NEEDS_FIXES及修复闭合全部保留。按此前已纠正的5份当前候选失败，加本次新失败，目前6份当前候选失败终态；原先累计1次CLI提交不因本次增加，正例0/负例0。

下一步应先诊断测试窗口激活后的非预期输入与文本清空，保持启动审计和验收标准。当前证据不足以判断8B改写任务的能力；不更换模型或放宽门槛。本次执行和一次结果复核额度均耗尽，后续实跑需新的具体范围。T2出口、E03剩余用例、同候选E01、8B的E02以及T3—T5/Owner门均未满足，项目目标继续保持active。
