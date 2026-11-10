# E02 ee1bef6 受控入口与绑定：待整包独审

原单 wo-ultimaagent-20261101-0021 / T2。产品候选 ee1bef61f04169c64978538dbc4ba799ef7be6c0 冻结且干净；本轮只准备新证据根中的受控入口，产品源码没有改变。本轮用户指令只分配准备工作，actual0/result-review0/model0；没有 release、actual、controller-authority 或 controller-ledger。

已把 N11 的 source-only harness 与绑定迁到当前 C12，固定 68 个产品源文件、1567 个输入文件；adapter 的完整 check_inputs 连同入口依赖核对1570项。原题、四来源 corpus、当前8B摘要、七保护身份、P4/P1辅助器和全部预算保持。adapter/bindings 的函数与类 AST 和 N11 相同；entry 只在 read_release 直接消息分支增加严格整数 actual1/review1/retry0 检查。旧 grant、旧 actual 和旧自动分配脚本均未复制。

入口缺口由 RED 复现：34项测试产生25个预期拒绝断言失败（含24个子用例），errors0，审计拒绝记录为空。最小修复后入口34、绑定16、边界11全部通过；准备消息无法被提升为actual1，run_once在消费前拒绝且不调用run_released，明确分配的合成正例仍通过。缺字段、0、多例、布尔、浮点、字符串和None均覆盖。

完整 adapter 离线回归：base-a79、base-b140、recovery19、export32、failure-export10，原始280，扣除两个重复测试后278。加上入口/绑定/边界61，当前新执行去重339项，全部PASS。各组沿用原审计守卫和时限，源码前后摘要一致；无模型、产品实跑、UI、音频、服务操作。N12原706项仅作已封存产品基线，未冒充本轮新执行。

新增三个测试经当前产品 SDK MockTransport 和原 adapter.install_trusted_exports 完整执行：500不读私有正文，200坏JSON/扫描失败保留HTTP200且validated_response=false；私有v3回执的代次/索引/路由/请求SHA/字节数、公开摘要和磁盘SHA一致，大小<=16KiB；首个失败结果完整保留，write/ACK/complete/acceptance均不被提升，无research.md。这些是模拟传输测试，不是现场HTTP回执。

2026-11-07 17:06:53北京时间只读核对：原七身份一致，11434监听属于既定Ollama，版本0.32.15，qwen3-8b-uncensored摘要6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330，18799空闲。这仅证明核对点状态。N12清单808成员/1568输入、N11清单2501成员/49结果/4补充成员及9个无关文件保持；C12 HEAD和工作树清洁。

独立计划审查PASS_PLAN_ONLY，整包准备审查待manifest封存后进行。后续须以独审PASS绑定harness-approval，再read_ready读回；该approval只代表准备。明确单例分配和新鲜grant是后续独立输入。执行范围见 execution-proposal.md。

上一N11单例仍FAIL_CONFIRMED；当前新候选实际0例，E02 0/3、T2/Owner未通过。真实HTTP状态、原生响应兼容性根因和读取到交付是否成功仍待明确分配后的一例实际回执决定。本次没有兼容性产品修改、预算放宽或失败重跑。
