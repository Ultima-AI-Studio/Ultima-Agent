# T2 E02 source-navigation v3 implementation plan — independent review 1

SPEC: PASS. QUALITY: PASS（含 1 项 Minor 命名修正；无 Critical/Important 阻断项）。这是固定设计的规划评审结果，不是代码、SDK、模型、P4 qualification 或 E02/T2 验收通过。implementation/source10/model/actual/T3 均未放行。

采用 SDD task-reviewer 的 SPEC→QUALITY 方法。阅读原 author brief、review brief、完整新文件 package 与两份 controller ruling；不相信 author 的“无冲突”自述，针对具名接口风险独立读取安装 SDK 和当前产品源码。Package 首次工具输出在 Task2/3 中间被显示层截断，故只补读 package L92–117 的被截断部分，没有另行重读 changed plan/analysis/report。原始 package、三个 payload、binding design 的 raw SHA256 均与 brief/manifest 一致；所有实际核对输入的完整 hash 见同目录 verdict.json。

## Strengths / 需求符合性

- Package L59–80 / plan L53–74：Task1 只承载安全不可变投影、页面、canonical v3、版本分派和 replay；顶层 stdlib、函数内 helper import 的边界能避免 work_tools↔research 初始化循环。已有 ResearchCollection 是 frozen 且原 catalogue 保存正文，writer/replay 可以沿用受限数据域，inspector 仅得到安全目录。HTML suffix、renderer 最终适配、全脱敏/空/无卡、GET linkage 与 canonical nonce 均有具体测试。
- Package L81–100 / plan L75–94：Task2 给出了 service preparer、实际配置 scanner 校验、单 enrollment epoch、exact object claim、非抛异常事件回调及写前 reservation/intent 接口。Task2 尚无 engine，明确只证明真实 SDK worker 单元，完整 service 成功留给 Task3。跨线程权限没有依赖 worker ContextVar，允许按顺序实现。
- Package L102–118 / plan L96–112：Task3 消费前两单元接口，保留真实 SDK system/query/assistant/USER Observation history，仅替换已固定格式 prefix。第三页 provisional sampler 与 raw+secured 成功后 promotion、writer dispatch 前 freeze 顺序与设计一致。上下文、精确 prepared entity、send reservation、HTTPX download/inspection/admission 三类计数、first failure、late effect 均有具名正反测试。全链脚本从真实安全目录/观察派生选择与 claims，独立 oracle 使用 fixture 原字节和坐标；没有把模型答案当 oracle。
- Package L120–144：targeted、baseline、final、compat 的 interpreter、argv、NEW basetemp/JUnit/隔离环境有定义；legacy 8 项有预加载与产品 import 路径断言。独立解析历史 XML 得 covering=285、compat=8、零失败/错误/skip，仅确认计划所述历史覆盖来源，不作为候选运行结果。原 280 suite-qualified identities 的保留和新增 13 目的需要未来 AST/identity 映射，不以 count 替代目的。
- Package L146–159：第四任务是 P4 小 adapter，单独 deterministic、inert、actual 门；不调用错误 E03 execute，不借旧 source_check 取得 source10 权限。native100ns/CIM 历史精度差异、NEW baseline、unknown 不杀、cleanup reopen+identity recheck 的真实能力均明确。首例和三轮、realnetwork、fresh E01/E03+negatives 仍独立分配，保留 research.md 固定 basename、外部真实 bytes/hash 与语义独立审查。
- Package L13–51：原 Global Constraints、固定 8B/digest、source9 封闭预算、frozen5、历史 source21 与单独 source10 candidate manifest 边界均保留。C 既有隔离与 future branch 的修订服从 root ruling，未引入第二个 worktree 或更改 H 生产。五项 frozen 文件 raw hash 当前逐项匹配。

## Issues

### Critical

无。

### Important

无。没有发现要求改变已批准架构、未定义关键消费接口或必须依赖虚构 SDK 注入入口才能实施的缺口。

### Minor

1. **F1 — 真实 SDK builder 的限定名写错。** Package `task-2-e02-navigation-implementation-plan-review-package.txt:95`（payload `revision-2/plan.md:89`）写“真实 ToolRegistry._build_tools/ToolExecutor worker”。安装 SDK `core/registry.py:121` 的 ToolRegistry 没有 `_build_tools`；真实函数是 `cli/ask.py:286`，由 `sdk.py:472–480` 导入并调用。照字面写测试会先得到 AttributeError，而不是所要求的 enrollment/permit 行为 RED。将该处改成 `openjarvis.cli.ask._build_tools`，通过真实 ToolRegistry lookup 构造，再用真实 ToolExecutor 执行。Package L55 已正确解释这个调用链，Task3 也要求真实 ask_full，所以这是局部命名修正，不是架构或可实施性阻断。

## Targeted independent interface checks

| 具名风险 | 实际读取 / 证据 | 结论 |
|---|---|---|
| name builder 不能注入对象或 engine= | installed sdk.py:271–314,443–498；cli/ask.py:286–344；registry.py:121 | ask_full tools 是名字列表，通用类零参数构造；checked borrow 可保留，F1 除外无虚构接口。 |
| START 不含对象、worker 不继承 ContextVar、subscriber exception 被吞 | tools/_stubs.py:375–463；core/events.py:137–165；native_react.py:327–356 | caller START→bounded worker→caller END；metadata 可带 JSON dispatch/adapter/seq，result 10240 chars 截断，计划 3072 UTF8 bytes 可完整比较。非 raising callback+worker identity claim 是可实施的。 |
| preparation scanner 与 borrow security 一致、guard 后完整历史 | 当前 agent_server.py:305–332,376–428,431–481；installed security/guardrails.py:75–88,167–218 | 现 guard 有真实 scanner 顺序和 mode，输入/输出扫描各有边界；计划 leaf 核对 post-scan messages、view 核对 post-scan output 能落在真实接口。 |
| service lock / 原收集对象 / nested SDK file IO / v2 历史 | work_service.py:63–98,118–145；work_tools.py:29–64,103–130,220–249,299–330；work_research.py:51–57,68–145,529–557 | preparer 在 runner 前单独取得/释放 ask_lock，不要求嵌套非可重入锁；collection 与 ledger 可冻结；Task2/3 明确替换 fresh 接线，保留普通 work。 |
| whole SDK history / max turns | native_react.py:233–280,327–356；sdk.py:487–498；六项 sdk-sources 原 hash 逐项重算相同 | 实际 max_turns=10 基线足够容纳 6read+write+ACK 的 8turn；运行前仍核对，SDK compress/loop guard 的替换或合成观察必须失败。 |
| 旧 negative/回归与 compat 是否真实存在 | test_work_research.py 的现有 collection/probe waiver/path/file false-success/native guard/reopen/budget/late effect 用例；source9 run_compat.py；covering.xml/compat.xml/identities.json | six-file 覆盖与 8 compat 真实存在，fresh direct-writer 用例需要改成真实链或拒绝；计划显式保留这些目的及 v2 historical-only 分支。 |
| P4 owned launch / cleanup 精确权限 | controller.py:139–246；acceptance_adapter.py:75–139；work_context_acceptance.py:112–113 | launcher retained handle GetProcessTimes，后代 identity 为 reopen readback；cleanup 只重开并核对已知 identity 后 terminate。P4 构造还调用 legacy protected()，future adapter 必须审清 source10 protected/native baseline 映射，不能把新 baseline 文件本身当成已接通。计划已单独 qualification 并允许停在 concern，无本次缺失 runtime 成功。 |

## Cannot verify / 后续准确的门

1. 本次没有实现，不能证明测试能运行、RED 原因正确、SDK chain 成功、页尺寸、真实 guarded history 大小或 context 完整保留。Task1→2→3 的 NEW receipts、hash/import-path/JUnit 与独立候选审查才回答这些问题。F1 修正必须在执行测试前明确。
2. 未执行 actual8B、网络、HTTPX stream、scanner/lexer、模型或进程实验；8B 理解/归属/条件/替代/原题覆盖只由后续实际 E02 和独立事实审查判断。
3. 未建立新的 native baseline，未导入/启动 P4。P4 import 顶层有 helper hash 校验/sys.path 添加和 P1 导入，future adapter 需要按计划审查这些依赖和受控加载位置，不能声称任意 import 都无副作用。legacy protected() 的精度策略及 NEW source10 authority 映射仍须独立 adapter review/inert qualification；这是已安排的下一门，不在本次静态结果中补写成功。
4. 当前 HEAD/index/生产进程/health 取 root 本轮 static ruling 背景，不由本 reviewer 重新运行 git、CIM、HTTP。未证明任何代码放行或生产切换。

## Scope flags / Assessment

只执行文本读取、stdlib AST/JSON/XML/hash 与三个新文档输出。没有 product/SDK/scanner/lexer/HTTPX runtime import，没有测试、model/network/UI/audio/进程实验，没有 git 操作、依赖安装、代码或原 evidence 修改，没有 subagent。approved v3 设计原数值/版本/限额/cleanup 权限保持 binding。

Task quality: Approved for planning gate with F1 Minor recorded. 三个代码单元的依赖和后续独立验证任务可实施；真正的代码与运行证明仍按计划逐门取得。SPEC PASS / QUALITY PASS 不改变 E02/T2 NOT_PASSED、T3 closed 或预算未分配状态。
