# T2 E02 当前 8B 研究接口复核

当前阶段：**新验证器的到期准入修复已完成219项模拟测试，原216项全部保留，原审查者复核中。先前一次研究模拟END异常仍原因未明并保留，新惰性额度未分配，模型调用0，E02/T2和后续验收未通过。** 原工单 `wo-ultimaagent-20261101-0021` 继续执行。

源9候选 `244d2120` 上的 E01 文件摘要三轮、E03 选区改写三轮及焦点/选区负例已独立通过，结论见[验收汇总](jarvis-work-t2-e01-e03-acceptance-20261102.md)。源10新候选仍需重新完成同候选回归；当前继续解决 E02 研究任务，不越过 T2 推进 T3。

本次核对了真实失败请求、SDK 输入与原生请求、响应、资料投影、证据卡及安装版词法器源码，确认以下边界：

- 原整篇研究输出只有 S1 引用，事实和引用不支持，未写出成果文件；历史失败保留。
- 两次逐来源实验正常返回，但均明确弃用资料、产出零事实。原文、投影及实际请求一致，没有发现 SDK 把已产出的事实丢掉。
- 静态确认 TypeScript 的 `this.toolRegistry.execute(...)` 在候选生成阶段丢失 `this`，与完整语句校验得到的操作名不一致，导致该调用无法签发直接操作证据卡。
- Python 样本已有完整 `self._executor.execute` 卡仍被弃用。因此，TypeScript 缺陷只能解释部分证据表示缺口，不能据此认定研究失败原因或声称修复后模型一定通过。

独立复核对已完成分析给出 SPEC PASS、QUALITY PASS，没有阻断发现。后续验证必须分别复现历史逐来源投影和产品整目录投影，保留编号/筛选变化，检查旧引用重开，并区分合法跨行调用与断裂负例。

下一步仅准备一个固定离线对照：在隔离副本中识别 `this/super` 接收者，其他校验、来源、可见范围、48 卡上限和权限保持原样。程序准备后先独立审查，再决定是否执行一次、最多 30 分钟的 0 POST 验证。即使对照通过，也只证明证据表示行为；产品修改、真实 8B 研究调用及 E02 验收仍需各自证据。

约束保持：只用当前 `qwen3-8b-uncensored`，不使用 14B 或更大模型，不改变默认模型；不改 KWS/语音或生产进程；原 source9 的 9/9 修复计数和旧逐来源实验 3/4 POST 计数封存，空余旧槽不再使用。本阶段新增模型调用 0、产品代码修改 0。E01/E03 的技术通过不代表生产集成或 Owner 冻结通过。

代码版本仍为验证工作区 `244d2120abcd6b8d7744f74a05bd22de46a2d3a5`、生产工作区 `0a31d84169ba8e151ec2f9a2c6fea958804daa5b`。本阶段读回 21 项源文件和 5 个受保护进程身份均保持一致。

原始分析、静态推导、独立复核和控制器裁定在 `data/evidence/jarvis-work-capability/T2/e02-interface-reassessment-20261102/`。关键绑定：

- 原分析 `report.md`：`83384b770f10b34f0b7f91362a1032a967befc111a2a47731edc07fb93bb3087`
- 接收者补充 `this-receiver-addendum.md`：`55fa2a2b06fa64db3dc1c168e54661572e167a60b48812892a31b283285cce9f`
- 独立复核 `review-1/verdict.json`：`50198214f04513a2afed67fb9a4a6e608c2085a6a974d111bb15c41de8d88585`
- 边界读回 `root-reassessment-boundary-readback.json`：`bb37b33c7b8d005506e5a84f3336e687cab65ef9e38f7315e1e96a8e54130d73`

后续准备审查：离线程序首轮就绪评审给出 REVISE，两项必须修正：跟踪回调异常后可能丢失后续 SDK 调用防护；评审包对 U+2028 夹具的字节保真有误。原始夹具/产品源码保持，正在原作者 fix1/5 中修复，并做限定的无 SDK 通用防护回归。尚未执行实际 S3/S4 离线对照或外层控制器；研究模型调用 0，E02/T2 仍未通过。原准备版本和审查 verdict8a34f545 保留。

离线首批实际结果为 INCOMPLETE：0.2999 秒即因旧 CIM 微秒基线与 native100ns 字符串全等不兼容而停止，资料比较 0、模型调用 0。775 项绑定与源文件保持，受保护进程未变化。外层控制器未产出终态、基座 Python 身份未捕获的限制保留；测试 Python 已退出后，控制器自身经原生句柄身份核验被结束一次，未终止 Python、生产或未知进程。独立复核 e35e388a 只通过失败记录真实性与保全，不认证执行成功；首次结果及1/1封口保持。

控制器裁定关闭这条离线工具分支。后续集中于原 T2 产品接口：同一 NativeReAct/ToolRegistry 主脑内提供限定资料查看工具，缩小8B每轮输入，再使用既有受限报告写入及独立读回核验。该路线此前已在接口分析中列为备选，本次只准备具体设计，尚未修改产品或放行新推理。原3来源/引用事实/三轮同候选/真实文件/真实联网和Owner门全部保持。设计 brief 为 task-2-e02-source-navigation-design-brief.md；源码10、T3及所有旧试验槽仍未放行。

按需资料查看第三版设计已独审 SPEC PASS/QUALITY PASS（review-3/verdict f6ddd91c），五项意见经两轮修订全部关闭。设计保留文档HTML投影与代码后缀边界，按实际SDK事件/实例认领请求，保留可重建的输入及引用记录，区分HTTPX已下载/应用检查/接纳/保留字节，并统一模型输出JSON格式。只算设计通过，未跑产品或模型验证。

正式设计为[研究资料按需查看方案](../plans/jarvis-work-research-source-navigation-design-20261102.md)，SHA41998861f1a0eeaad1800f61d19642656b0e19fa4b74dcf0e79366d6dc4c0eef。现在按原工单细化代码文件、接口、先失败后通过的测试、同候选回归及独审步骤；源码10、首个实际8B案例和T3均待各自门。新1CLI/8POST额度只是提议，未分配。永久仅当前8B，旧9/9、3/4、1/1封口，KWS/生产保持。

2026-11-03：实施计划独审 SPEC/QUALITY PASS（a65a30ec），唯一非阻断命名勘误已逐字读回修正，正式计划 SHAa8419b77。现有隔离C从244创建 codex/jarvis-work-navigation-v3-source10，H生产0a31不变。代码阶段新跑六文件285PASS及compat8PASS，实际加载产品路径验证通过；compat原有anyio rewrite警告与可选voice reference fallback提示保留，不能称输出全无警告。已派发第一单元实现安全来源投影/页面/canonical v3及重放；后续为请求permit/SDK写入、完整对话/有界transport。代码只放行明确allowlist及隔离测试，首个实际1CLI/8POST尚未分配，模型调用0。旧source9 E01/E03只对旧候选成立；新候选仍须完整SDK、实际E02三轮/真实联网/同版E01E03与负例/原T2审查。KWS、生产进程、其他权重及T3均不变。

Source10第一单元已完成：244→e0b04d6→494e544，仅六个允许路径。安全资料投影/页面/canonical v3/按实际窗口重放及fresh3验证已实现，原v2算法保留。e0完整回归341通过；随后nonce16字节精确性Minor修正，在494相关两文件235通过，不能把341称为494上的重跑结果。最终独审90d57d47/e371a8c3为SPEC/QUALITY PASS，无未闭意见。代码tag jarvis-t2-e02-navigation-unit1-20261103指向494；证据检查点另名unit1-evidence。第一单元只算数据接口，通过不代表实际SDK/8B研究可交付。现已启动第二单元的enrollment/permit/安全preparer/真实SDK worker与FileWriteTool测试；第三单元还需完整对话和原生transport。实际模型调用、新真实验收、harness inert、T3都未放行。生产五个CIM域身份与8756当前8B健康读回一致，根比较器初次JSON日期自动转换误拒已保留说明并用DateKind String纠正，旧基线不改，停止进程0。

联合集成裁定：原生研究回归同时依赖新capability/permit与新phase/history，两批中间无法维持真实全链成功断言，因此U2/U3合并为同一实现/独审单元，不设置伪造成功、skip/xfail或默认v2后退。只调整工作拆分，不改原设计/事实门/预算。第一次完整联合回归369项中82失败已保留，用于迁移旧协议fixtures；这不是新的产品验收失败重入。另有unit2-green-2中的独立失败来自临时PageKey页面的N3哈希被实际PIIScanner当成Mastercard号，根独立重现f25302c7并定位到预检查错误调用实际暴露前scan_view。按已定职责仅移除占位页的实际扫描，保留来源/目录安全和真实inspector返回前严格扫描；该小修复正在联合实现中，完整回归及独审尚待完成。实际返回的PII样式引用仍按原策略拒绝，可用性比例未测，不声称已消除全部误判。允许仅迁移test_work_context两项research fixtures的最小改动，原E01/E03及旧快照不改。源代码494检查点与tag已推送并远端读回，后续修复不在该旧检查点中，未生产集成/未新增模型调用。

首个联合候选0e3e0ed（494→0e3，十个允许文件）完成418项完整回归+8项安全兼容、四组真实SDK/文件的脚本推理读回；这些只算代码测试。最强独审对首候选给SPEC/QUALITY REVISE（8a77a272/report161124eb）：1Critical为timeout observer退出RLock后才seal，可能放行晚到写意图；6Important为原生writer参数/原路径字节与ACK未全绑定、事件顺序/准确阶段/写前prefix重放不足、native版本/权重元数据不可重建、send前timeout重算未应用与拒绝回执缺失、旧between-snapshots负例提前return、None最终packet仍可降级纯数据验证。418+8通过不代表这些性质已通过。根已按源码核实，原作者进入联合fix1/5，以真实反例先RED后GREEN，保持所有旧失败/原冻结门；修完再同一审阅者定向复核。未分配模型、harness inert、实际案例、T3或生产发布。代码和审查输入先锚定为明确REVISE检查点，不代表通过；生产0a31和语音基线保持。


源10 FIX1当前候选：`facd68d8f94b4adcfd136e489e9ff81580d2dc0d`，首轮 REVISE 的1项Critical、6项Important已由原作者提交修复，尚未被独立确认关闭。完整449/0/0/0与兼容8/0/0/0的回执、当前源码及Git提交字节、SDK22、原报告43651字节前缀及四个新封存成果已由控制器独立读回，见 `navigation-source10-validation-20261102/code/root-unit23-fix1-before-review.json`（74d42860）。原审查人只复核F1–F7和新修复引入的问题，原首轮失败不改写。`source10` 模型推理调用0，验证适配器/惰性验证/实际E02/T3/生产集成均未放行；目前只有已授权的隔离代码和测试。

原E02输入定位已确认：`source6-native-reference/controlled-corpus-inputs/corpus.json`（9e7cdfe6），题目774字节与原实际argv一致，四份正文7236/3252/4643/13559字节及URL/哈希与原独立失败复核一致；未来使用新请求与GET绑定，不复用旧GET许可。该定位读回不是E02通过或实际调用授权。


FIX1逐项独立复核结果为SPEC REVISE、QUALITY REVISE（review-unit23-2/verdict.json e3601963）。F1、F2、F5、F6、F7已关闭；F3可接受来自错误agent的writer END，F4可接受空白或Unicode转义后命中既有scanner的ACK，N1用Decimal重算binary64时钟会拒绝合法已裁剪timeout。原prewrite与真实文件不变的反例均保留，见probe-results.json（15dd6619）。原作者FIX2仅修这3项并补反例回归；不放宽权限、时间、scanner、真实验收要求或8B-only范围。具体时钟裁定为用已记录的有限binary64原值重建与线上相同算术，不加epsilon/容差或换时钟域。


FIX2当前提交 `6b1e07c8318a334ee1f2218863eb84254e38f526` 只改work_research.py及test_work_navigation_transport.py，475/0/0/0与兼容8/0/0/0通过。root完整读回追加报告d0bb89d6、68833字节旧报告前缀、31原始输入（30个Git跟踪输入及1个原有未跟踪浏览器测试单独绑定）、SDK22、4份新报告及6组小数时钟/90个同一prepared HTTPX请求；证明见root-unit23-fix2-before-review.json（cfe4926e）。测试夹具自身两次修正及其首轮失败均保留，只有后续正确夹具上的失败用于证明相应缺陷。当前仍待同一审查人review-unit23-3确认F3/F4/N1，不能按测试数宣布T2或模型能力通过。


FIX2独立复核最终SPEC PASS、QUALITY PASS：F3/F4/N1均ADDRESSED，无新问题或范围外发现，原F1/F2/F5/F6/F7处置保持。正式verdict185472cc、报告59cc759a；控制器读回并记录unit23-result.json（bea943dd），这里只通过代码单元。当前新独立审查人审查整个源10分支244d2120→6b1e07c8的13路径、完整394277字节差异包（2d0da754）、受保护输入、SDK22及模块间调用与文件交付闭环；不复用同一任务审查人的结论代替整体判断。Task4适配器、惰性验证、原四源资料的零推理链路验证、真实8B E02三轮/联网与同候选E01/E03回归仍在后续各自门内。


整体候选独审结论SPEC FAIL、QUALITY FAIL、CODE CANDIDATE NOT READY（candidate-review-1/verdict.json e157cd0f，报告acebd119）。两项Important分别为C1：ACK及时完成后，服务最终重放/重开文件可能超原260秒仍报succeeded；C2：纯空白final_answer在被拒绝前先确认pending页面，尤其第三页会污染已发放记录。审查基于实际控制流，未冒称新增现场复现；475+8历史检查记录及原代码单元PASS保持，不能代替这两个未覆盖分支。已按最终审查流程交一位新实现者一次修复整组问题，随后仅由同一整体审查人做一次范围限定复核；不进入新一轮无界修复或更换模型。


一次集中修复提交 `118ba152b007c30d358c8bc44c51aabe8ae820f0` 仅改服务、研究视图及对应transport测试三处。C1的3个真正SDK/文件控制流用例中，首次RED在at/after错误succeeded、before正确；修复后在259.99999999999994成功、260及260.00000000000006需要人工关注，原文件、completed effect、ID与15次请求保持。C2的首次RED明确promoted=[1,2,3]多于预期[1,2]，修复后空白final在secured/页面发放前拒绝。当前479/0/0/0与兼容8/0/0/0、31原始输入/30Git跟踪+1单独绑定原有未跟踪测试、SDK22、4新报告、6组fractional/90prepared请求均已控制器读回；root-candidate-fixwave1-before-review.json（5a5cc44b）、新报告10b079f5。原整体审查人仅复核C1/C2与此修复新增问题，不进行第二次整体重审或另起无界修复波。真实模型调用0，Task4/惰性/实际/T3/生产门仍保持。


整体审查的一次限定复核已确认C1/C2 ADDRESSED、SPEC PASS、QUALITY PASS，无新问题，代码候选与Task4适配器准备ready（candidate-review-2/verdict.json 1ca4f4ab，报告74f34a7f）。控制器完整读回并签发仅准备许可harness-preparation-authority.json（0e8c2e27）及独立source10-candidate-manifest.json（cdfbfb05）：固定118ba152、31源输入/30跟踪+1原有单独绑定测试、SDK22、原P4/P1/helper及原四源语料，永久当前8B策略。只允许新建6个harness文件、隔离单元测试和回执；允许读入固定P4无副作用定义，不允许惰性启动/真实CLI或server/原语料运行profile/模型或联网调用。原P4归属与清理原语复用，旧corpus_hook的response.read完整读入钩子须分离，保持新流式限制。


Task4首版作者DONE_WITH_CONCERNS，6文件manifest14247bfe、报告47246ba8、最终37项GREEN回执f233e889；所有C产品/SDK/P4保持原字节，已归档到harness-preparation-author-r1。第一轮20个NotImplemented功能RED未同时复制旧源码，原trace/hash限制已诚实记录，后续GREEN保留完整6文件快照。实际/inert/profile/model未运行。未决正确性问题是315秒聚合上限：P4每次进程查询timeout15，单个已归属身份清理还含最长10秒退出等待及多次查询，当前adapter仅事后检查elapsed、CLI按剩余时间等待，不能证明完整操作含清理均受315约束。控制器已完整读报告和原P4函数，先进行仅限截止时间映射的只读架构核对，不把该缺口当作已通过的资格门；不降低原315或另造原生归属控制器。

T4-D315-01裁定：315秒是完整封存并独立观察成功的资格截止，不承诺任意失败OS调用均可物理抢占。单一monotonic_ns原点位于准入前，工作/清理/最终见证分别275/310/315秒；原260服务、300客户端、315外层及零重试上限保持，明确记录实际客户端窗口缩减。仅在原P4私有I/O边界和真实Popen实例等待裁剪，保持原生归属/句柄/清理算法不变；未知或未完成清理永不通过。根裁定144be9bc、修正brief00d3f819已交同一实现者，六文件准备权限0e8c不扩展，首版37项及其RED缺失旧源码限制保留。

Task4截止时间修正完成准备：schema11、私有P4 I/O借用、RootInvocation一次调用及关闭后外层见证已实现；最终75/0/0/0，receipt4709905e、manifest eb30d3fd、报告b6110151（原13665字节前缀保留）。控制器读回9轮/所有旧37标识/六文件最终快照/C31与30Git+1绑定未跟踪/SDK22/64pins，独立proof420ab4b5；完整101263字节新文件差异包29b24917进入首次功能/质量独审。修正RED201732具备六文件副本但没有显式before/after字段，该字段自201803起具备；不升级历史证据。没有惰性、profile、模型或实际放行。

Task4首次独审SPEC FAIL、QUALITY NEEDS_FIXES，报告a71a802d、verdict a2b0dae2。13项阻塞涵盖子进程argv/单次原生启动绑定、实质见证与seal摘要、清理后文件一致性、完整redirector/base/listener证明、正确protected5、固定解释器/import来源、安全大包导出、首次失败、完整运行pin终态、socket剩余时间、CLI/service一致及观察阶段准入/测试遮蔽；H10/H11两项minor登记。原75测试证据仍保留，证明其不足而非验收通过。原作者按同六文件修复，旧P4/P1/产品118/SDK/64pins不变，修复后原审查人限定复核，不触发模型或惰性执行。

Task4修复1已封存：manifest b6723110、报告594584b5/52443字节、最终123/0/0/0回执392957d4；13项阻塞及H10/H11两项minor均报告改动。控制器完整读追加报告并核对16轮新回执、所有原75标识、六最终快照和64固定输入，旧30837字节b611前缀保留，proof f9d4b904；基于eb30归档生成124196字节精确修复差异b7528734。原审查人仅复核H01–H15及此差异新问题，未再次整体重审。合成资料真实verifier读回正例/虚拟OS的实质见证不算原始语料profile或运行资格；原首次FAIL/所有中间失败保留，无模型/惰性/实际放行。

Task4修复1限定复审SPEC FAIL/QUALITY NEEDS_FIXES（报告62b66419、verdict b47f96af）：H03–H13及H15共12项ADDRESSED（含两项minor）；H01唯一原生base绑定、H02回环响应未封存、H14逐目录时限仍开放。新增F1-N01未知字段安全/F1-N02许可后迟到启动/F1-N03清理前已观察差异未参与判定，全部纳入原作者第2轮同六文件修复；123单元证据和前次失败保留。未把测试通过当资格门，原8B/产品118/P4/SDK不变，无惰性/profile/模型/实际放行。

Task4修复2已封存：manifest e16609e1、报告6f9926ac/69552字节、最终145/0/0/0回执15666551（保留123基线、无-k）；控制器完整读追加报告，独立proof36f47e5b核对20轮（针对性选择单独记录）、六最终快照/64pins和旧52443/594前缀。差异85101字节9877e351，基于b672归档交同一审查人仅复核H01/H02/H14/F1-N01–03及此修复新增问题。包括逐目录停止、实际模拟GET封存、严格布尔、typed字段扫描和临时产物差异；均不算实际资格/profile/模型事实验收，无新运行放行。

Task4修复2限定复审SPEC FAIL/QUALITY NEEDS_FIXES（报告38d49ba3、verdict8f6fb218）：H01/H02/H14/F1-N02/F1-N03 ADDRESSED，原12保持，共17关闭。F1-N01仍有重复JSON键遮蔽和错误位置entity将数值字符串转换成免扫数字；新增F2-N01合法Observation ACK误拒、F2-N02空任务目录漏检，均纳入同一作者第3轮。F2-N03仅minor，256数据+固定索引计数一致性顺手处理或登记延期，不单独延长阻塞轮。所有反例仅虚拟资料和内存发布替身，未写不安全数据/未运行资格。145测试证据继续保留，不等于适配器或模型验收。

Task4修复3封存：manifest84b85517、报告51cd77d1/94969字节，final162/0/0/0回执d34ab34e；控制器完整读新增报告，proof246d2425独立核对6轮（针对性与整套分开）、原145标识、六最终快照/64pins/69552字节6f旧前缀。e166归档至新版本精确差异52378字节fc4b790a，交同一审查人只复核F1-N01/F2-N01/F2-N02、相关minorF2-N03与此差异回归。标准JSON重复键检查、精确producer路径/角色解码、ACK普通文本、空任务目录和256数据+固定索引边界均需独立确认；未把作者结果当资格。生产只读b86db6b3另确认5身份/CIM域/H0a31/健康接口current8B未变，非native新baseline/语音性能验收。

Task4修复3限定复审SPEC FAIL/QUALITY NEEDS_FIXES（报告0ac789eb、verdict c8bddf17）：F2-N01/F2-N02/F2-N03关闭，原17保持，共20。F1-N01仅余生产者声明类型未强制：SDK ToolResult.content与实际file_write是字符串，work_tools原样存入execution.files.result；将此值换成可检出数值的JSON整数或含整数对象，现有导出仍通过模拟发布点，字符串控制却正确拒绝。本轮无新回归/无实际不安全写出。按SDD规则第4轮由fresh gpt-6-astra/high工程实现者接手同六文件，产品模型仍永久当前8B，产品/SDK/P4不改，原162与全部历史失败保留。

Task4 fix4：新工程代理按实际SDK/产品字段声明补充导出前类型校验。完整173项通过，原162项全部保留；6份源快照/64固定输入及94969字节旧报告前缀均已独立读回。整数/对象反例通过原重放后被拒于写盘前；初始延迟夹具序列化错误及纠正后的真实RED均保留。作者报告b8fb39ee、manifest935b3e3b，root读回f2169bd9。仍由原审查者只复审F1-N01和本次修复新增风险，不据测试宣布运行或研究验收通过。

Task4 fix4独审通过：SPEC PASS/QUALITY APPROVED，唯一F1-N01关闭、此前20项维持，无新增发现。审查报告7e4ada38、verdict7d1d239f，173项测试与64固定输入均独立核验。六文件仅获准备代码通过；下一步是复用RootInvocation/headless.run_inert的具体ROOT外层入口准备和独审，之后才另签一次惰性运行额度。没有运行许可、native基线、approval或实际authority被创建。

Task4C隔离运行入口准备完成：50项完整测试通过，5轮原始记录/每轮80份前后源快照及当前文件已独立读回。调用现有RootInvocation/headless合约，单次消费、最早时间起点、精确五进程原生身份、外置不可回写见证均已实现并进入独审；这里只是代码准备，不是实际惰性运行。manifest83a55d08、报告06ba572d、root读回ea0b02a3；早期三轮简版回执缺失字段保持null，没有升级成后期证据。

Task4C首审FAIL：6项P1、1项P2（RC-01至07），分别为控制JSON二次读取替换、过期准入、claim创建前失败后重复使用、其他UUID遗留attempt漏查、已签发authority/baseline在实际准入前被替换、首因被后续控制错误覆盖、结果未完成fsync/关闭即暴露canonical文件。50项测试证据有效但不足以通过代码门，失败审查690b0bf9/verdict5be27e9c保留。ROOT协议T4C-ALLOC-01选择实例HELLO/go及先封存的ROOT消费记录，保持现有P4与已通过六文件不变；实际准入仅加私有返回值/原字节绑定检查。原作者修7项，未创建任何运行许可或原生基线。

Task4C fix1准备完成：完整77项通过，原50项ID全部保留；4轮新记录、81固定输入/646份原始前后副本及14779字节旧报告前缀已独立读回。ROOT实例绑定握手、过期边界、原始准入结果绑定、首因/后续否决分离、关闭后原子发布等7项进入同一审查者的限定复审；manifestb05bbe5d、报告a8181920、root读回95a36d8e。旧FAIL与夹具错误保留，真实握手/惰性/模型未执行。

Task4C fix1复审：RC-01至07全部ADDRESSED；新RC-08（原始准入在后置拒绝前已可能查询替换后的PID/端口）和RC-09（关闭后的pending路径在硬链接前被替换，canonical内容与原结果不一致）保留为待修。报告529715ab/verdict80e93a8c，77项测试及646份快照有效但不等于代码通过。ROOT T4C-READ-02裁定只增加私有实际读取绑定和发布后原字节校验，六文件适配器不变。纯标准输入回显探针已验证TTY交接，PID31004/会话90460正常退出；它不是实际入口握手、原生/惰性运行或模型验证，不消费案例额度。

Task4C fix2：实际原始准入的两条私有读取按原签发字节校验后才交给原算法；发布前保留一次序列化内容，硬链接后再按原字节比较canonical文件。完整84项/原77项ID及490份原始副本已独立读回，manifestd4b73f6c、报告aaa309dd、root读回62df339e。只复审RC-08/09和本轮修复新增风险，尚无运行许可。另一次生产只读核对d4c40fa6确认5进程CIM身份、生产0a31和8756当前8B健康保持；它不是native100ns基线、语音性能或惰性验收。

Task4C fix2独审通过：RC-08/09关闭，前7项维持，无新增发现；报告e460fee4/verdict2d99db59。Root已按当前84项/82输入及代码、审查原字节独立封存CODE门和harness-approval，范围只含已审查适配器与具体入口，不自动运行或分配模型。原生身份/监听/清理/315秒闭合证据属于下一次另签惰性额度；原T2研究理解、三轮、真实联网和同候选回归要求均保留。

真实惰性1已封口失败：ROOT见证在46.146秒读到已闭合数据，但eligible=false。原P4 cleanup报告进程已退出/端口关闭；适配器保持严格10061拒绝判据，1秒connect_ex返回10035，故不能确认端口关闭。原中文问题774字节传参、5原生保护身份和源码pins、22文件封存/hash均已独立读回，root证据f37eb5d7；模型调用0。后续只读3秒探测在2.014秒收到10061、旧ownedPID也已不在、生产健康仍为当前8B；这些只用于诊断，不反向升级旧失败。旧额度不重试，旧V/harness/Wcaller/approval/authority/results全部保留；下一修订必须在新命名空间先完成代码准备/复审再单独分配，不自动进入模型或研究任务。

T4-PORT-REV2：仅把现有两处私有单次端口证明的上限从1秒改为3秒，两种模式共享；构造和设置耗时占用原分配上限，仍按原阶段截止时间裁剪，只有明确10061才算关闭。原275/310/315秒和零重试要求不变。新目录V2候选a5b16aed、216项/76固定输入/全部旧173项均由Root独立读回（54c16a65），保留所有RED与中间测试失败记录。当前仅准备代码，独立审查尚未裁决；原生/模型/研究草稿/实际联网/同候选回归均未通过。

T4-PORT-REV2首轮独审FAIL/NEEDS_FIXES（27d598e3/44cbd804）：PORT2-I01在构造耗尽3秒后仍调用raw.settimeout；零connect不等于零额外调用，须在私有与阶段截止前准入。原21项审查结论维持，216项/173保留事实维持；原作者按新修订Task1的第1/5轮修复，旧实际额度不重开。

FIX1最新219项完整模拟通过，保留前次218通过/1项研究write-END失败与孤立复查通过；端口实现从该次失败到最新通过保持27100afd不变，仅新增失败状态诊断，未放宽原断言。原因仍未知，带入原资料零推理画像和同候选T2读写验证，不声明已经修复。原作者报告41676字节/02f813a3，Root五新阶段/76输入/原216ID/16751原报告前缀与六文件均独立读回（a4a13980），等待限定复核PORT2-I01及新改动。
