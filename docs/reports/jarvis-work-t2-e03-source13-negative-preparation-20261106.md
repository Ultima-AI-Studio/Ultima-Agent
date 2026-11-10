# E03 source13目标变化负例准备完成

原工单wo-ultimaagent-20261101-0021，候选269aca511d88412dbb9c15d23911138469a37aa2，固定当前qwen3-8b-uncensored。E03三正例3/3保持；本次仅完成负例准备，不增加实际用例或验收credit，E03整组与T2仍未通过。

本包完成255项离线检查，0失败/错误/跳过；一次全包独立准备审查PASS，0 Critical/Important/Minor。审查代理`/root/review_e03_source13_negative_entry`。产品源码、默认8B、KWS/语音未改，全部旧失败保留。80文件manifest SHA-256 `b98dcf3ff92f623238fd15cea6c7929875bba056dee3dae74245e89b44a7266f`。

三个原terminal/review/registration逐项绑定同候选、不同任务、递增时间与累计行。新测试对重复task、逆序时间及缺累计行做一致重新绑定，补齐原PREP-M1所述覆盖。运行恢复另绑定用户手动启动记录、新Ollama PID5708及其余六个原身份；旧round3事后环境FAIL不改。原恢复快照缺的created_utc仅在新输入从FILETIME精确派生，原件和旧candidate注释保留，7核心身份字段零变化。

负例路径不启动Agent服务器或工作CLI，不调用模型，不做音频操作。一个未来实际用例含两个场景：焦点移开后由产品validate_work_target重新观察原绑定目标；选区改变后由真实replace_selection重新读取并拒写。两个场景的目标变化后都重新检查同一authority/proof及原期限。任何未执行、准入过期、未知错误、before_send、原生replace或非空产物都不能算通过；失败仍记录部分观察、释放capture、清理owned夹具并闭合审计。

**本次纠正的方案假设：**旧Case.negative把单独焦点变化当成必须拒写；真实冻结provider的离线RED证明它会重新观察并允许原目标继续，契约E03也允许“重新观察或明确停止”。因此新焦点场景只验证重新观察原绑定目标，不声称验证焦点丢失后的完整替换链。选区场景才验证拒写。原生observe审计代理记录实际读取，对意外replace硬拒绝并记录，代理拒绝不能冒充产品目标拒绝。独审接受这一修正。

测试证据：前置资格RED27/30失败后GREEN30/30；新路径RED23/31失败后GREEN31/31；整包251/251后增加每场景proof/authority到期四项，最终255/255。所有RED保留。父191项按函数/参数数量保留，正例专属CLI提交断言适配为零CLI；新增64项。测试加载冻结WorkContextProvider和实际Case.negative，仅替换native I/O，不能替代现场。Python I/O guard denied/allowed/open-owned-listener均0。源代码输入在测试期间不变。

root及独审分别核对80封存文件、父56封存、57源码、7依赖、1346 SDK文件、九前轮原件和三恢复副本。485/8产品回归仅核验历史绑定，本轮未重跑。独审测试数量来自封存XML，不宣称reviewer运行测试。

独审完整原回执`independent-preparation-review-original.json` SHA `e75862e5454e3c24419fad3a759ba04fd344af8ee920091b78806ff883b9cf34`。同一reviewer仅澄清机器字段PASS_PREPARATION_ONLY等价于本scope下PASS；标准回执`independent-preparation-review.json` SHA `1959e61bec45a273c3b2b160c2b4cf7f35d2f43ec35a2006d4325b1a9a6b98bd`，preparation_only=true。不是第二次审查，root没有自行改写独立verdict，代码和manifest未改。

root接受六项审查范围限制：实际Windows行为尚待现场；focus完整写入链未验；运行状态只属时点观察；三个旧正例仅验证资格、不重做事实复核；485/8未重跑；E01/E02/T2/Owner/完整目标没有通过。逐项见verification/review-disposition.json。

执行裁定保持：延用用户既定inline持续推进离线准备；永久保留证据根及RED；采用已有产品guard零推理负例；新恢复观察解除旧环境缺失的当前准入障碍但不改旧FAIL；依原契约修正focus场景；用既有Windows隔离runner和永久ledger替代技能临时脚本。这些裁定不增加现场授权，代价/限制分别是准备不等于产品通过、证据需继续维护、完整8B任务仍待E01/E02、保存快照不保证持续存活、focus完整写入未验、ledger不是技能脚本生成的提交范围。

北京时间12:01:58只读后查：Ollama0.32.15/当前8B摘要匹配、七身份匹配，官方语音ready/fresh。后查收据另存verification/preparation-runtime-readback.json，不计入80封存payload，也不充当下一次fresh proof。恢复报告：jarvis-work-t2-runtime-restored-20261106.md。

下一步具体提案位于verification/next-case-proposal.md：一个e03-negative（两个场景）和一次只读独立结果复核；需用户新分配，当前实际/结果复核均0、无release或actual。失败不重试；15秒手动开始、20秒fixture、60秒proof、120秒authority保持。通过后依次同候选E01、仅当前8B E02，再按原T2出口进入T3—T5及Owner。

计划与两份报告同步UltimaDocs同名镜像。本地准备tag计划为`ultimaagent-t2-e03-source13-negative-prep-20261106`，实际commit及字节读回见verification/local-checkpoint.json。原服务启动与Git推送曾被自动审批以blocked by policy拦截；用户已手动恢复服务，助手无启动重试，远端推送没有换通道重试，本报告不声称远端已同步。
