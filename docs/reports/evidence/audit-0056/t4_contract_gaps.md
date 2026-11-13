# T4 · 接口、依赖与闭环审计

> 工单：`wo-ultimaagent-20261113-0056`  
> 判据：同一份文档的叙述顺承不算契约；调用方与被调方至少要对同一接口名、入参/出参、错误、超时、幂等/重放和失败收口达成同一口径。

## 1. 模块清单（三套账）

| 账 | 用途 | 本轮采用的模块/容器 |
|---|---|---|
| A 呈现三类 | 架构树第一层 | 基础能力／外部能力（三抽屉）／交付 |
| B 工程八块 | 代码归属 | Core／Senses.Voice／Shell／Surface／Memory／Middleware／Update／Lifecycle |
| C 功能桶 | 能力归并 | ①感知与交互／②语音／③理解与决策／④宿主执行编排／⑤治理与约束／⑥记忆自学习／交付域 |

横切及子模块：Console（与 queue_engine 同 pid）、Manager（Console 子模块）、治理⑤（不占运行时模块）、外部能力 Skill/Plugin/Provider、客户端与运营 UI。依据：盘点 §1.1–§1.1.1、树节点 2–86、详解页 §02–§05。

## 2. 全量跨模块边契约矩阵

符号：`✓`＝两端可对上；`½`＝只有单端名字或只有部分字段；`—`＝未定义；`N/A-R`＝纯只读调用不产生副作用，幂等可判天然成立。

| # | 调用方 → 被调方 | 调用方位置 | 被调方位置 | 接口名 | 入/出参 | 错误码 | 超时 | 幂等/重放 | 判定 |
|---:|---|---|---|---|---|---|---|---|---|
| 01 | Voice → Core（ASR 交轮） | 基线 §8–§13 只到 `processing` | 详解页 §02 Core L185–188 | — | — | — | — | — | **断链 C-01** |
| 02 | Core → Voice（TTS/会话控制） | 树节点 3/12 无调用名 | 注册分类 L41–L42 有 `tool.voice.speak/listen_once` | ½ | ½ | — | — | — | **断链 C-01** |
| 03 | Core → Memory（写入） | 树节点 8、详解页 §05 L302 `memory_boundary` | 注册分类 L99 `tool.memory.write`、基线 §17.1 | ½ | ½ | ½（越权拒绝） | — | — | **半契约 C-18** |
| 04 | Memory → Core（检索） | 详解页 §05 L303 | 基线 §17.1/§17.5 `mem/kb/exp.search`、注册分类 L100 | ½ | ½ | ½（没找到） | — | N/A-R | **半契约 C-18** |
| 05 | Core → 主脑 | 基线 §16.3 L769–L775 | 基线 §16.2/§16.4 | ✓ `brain.infer` | ✓ task_id/profile/deadline→completion | ✓ 梯子事件 | ✓ 30s | N/A-R | **完整（但 E-02 预算算术错误另计）** |
| 06 | Core → Console（计划交接） | 树节点 6“多步计划” | 树节点 47/详解页 L233“派发/依赖” | — | — | — | — | — | **断链 C-02** |
| 07 | Console → Middleware（派发） | 详解页 §05 L304 | Middleware 节点 43/44、基线 §15 状态机 | ½（只有关系名） | — | ½（八态） | — | — | **断链 C-03** |
| 08 | Console → Shell（起/停/查意图） | 基线 §15.1 L523、树节点 52 | Shell 节点 20–28 | — | — | — | — | — | **断链 C-04** |
| 09 | Shell → Manager/Console（进程事实） | 基线 §15.1 L524–L526 | Console/Manager §15.6 | — | ½（存活/无主/回收结果） | — | — | N/A-R | **断链 C-04** |
| 10 | Middleware → Shell.pty_host/进程 | 基线 §21.2 L1181–L1185 | 树节点 26/44 | ½（句柄交接） | ½ | — | — | — | **半契约 C-04** |
| 11 | Middleware → executor plugin | 详解页 §05 L305、树节点 44 | 树节点 72、基线 §18.1 | ½ `plugin.executor.<name>` | — | — | ½（宣称有 timeout） | — | **断链 C-05** |
| 12 | Middleware → MCP/tool plugin | 注册分类 L66–L76 | 树节点 70–74 | ½ `tool.exec.mcp_call` | — | — | — | — | **断链 C-05** |
| 13 | executor/plugin → Middleware（流/结果/回执） | 树节点 72 只称 harness | 树节点 43/44、注册分类 L71 | ½ `tool.task.report` | — | — | — | — | **断链 C-05** |
| 14 | Console → Surface（状态呈现） | 详解页 §05 L307 | Surface 节点 29–35 | — | ½（状态） | — | — | — | **断链 C-06** |
| 15 | Surface → Engine（叫停/恢复/设置） | 树节点 32/33 | 双域规范 §11.2–§11.3 | — | — | — | — | — | **断链 C-06** |
| 16 | Engine → Client（事件/订阅） | 双域规范 §11.2 L187–L194 | 树节点 98/99 | — | ½（事件/回调） | — | — | — | **断链 C-06** |
| 17 | Admin → Engine（受控写） | 双域规范 §11.2 L188/L195 | 树节点 107/108 | — | ½（装卸/启停/回执） | — | — | — | **断链 C-06** |
| 18 | Governance → 全模块（准入） | 详解页 §05 L308、注册分类 L87 | 树节点 53–56 | ½ `tool.policy.check` | — | — | — | — | **断链/无主 C-07** |
| 19 | 全模块 → Log Store（追加审计） | 多处要求“留事件/留审计” | 基线 §22.3 仅定义分类与 `log.query` | — | — | — | — | — | **断链 C-08** |
| 20 | Skill 采集 → Memory.kb（入库） | 基线 §18.6、树节点 68 | 基线 §17.3 L909–L915 | — | ½（内容/书架） | ½（三项校验） | — | — | **断链 C-10** |
| 21 | Update → Lifecycle（应用包） | 树节点 80–82 | 树节点 83–86、注册分类 L127–L130 | — | — | — | — | — | **断链 C-09** |
| 22 | Lifecycle → Shell（停机/重启/首启健康） | 双域规范 §七 L138–L139 | Shell §15；Update/Lifecycle 节点 | — | — | — | — | — | **断链 C-09/C-14** |
| 23 | Provider plugin → Core（外部主脑） | 基线 §23.2–§23.5 | 基线 §18.3–§18.4 | ✓ `brain.infer` 内路由 | ✓/½（OpenAI 兼容） | ✓ 六态 | ½（退避有、请求 deadline 复用） | N/A-R | **半契约，未另编号** |
| 24 | Memory → store plugin | 树节点 41 `store_backend` | 注册分类 L105、L138–L139 `plugin.store.*` | — | — | — | — | — | **断链 C-16** |
| 25 | Voice → Client（duck/播报事件） | 双域规范 §11.3 L205 | Voice §8–§13 无事件 envelope | ½（播报开始/结束） | — | — | — | — | **断链 C-11** |
| 26 | Client → Voice（DND/音量/热键参数） | 双域规范 §11.3 L204–L208 | Voice/Engine 只称接受状态位/参数 | — | ½ | — | — | — | **断链 C-11** |

矩阵汇总：跨模块边 **26**；完整 **1**，半契约 **4**，断链 **21**。矩阵的“断链 21”是边数；下节把同一根因的双向/多边合并为 18 个发现，因此不能把 21 与发现数相加。

## 3. 断链／孤儿／无主发现

| 编号 | 主类 | 严重度 | 调用方 → 被调方 / 位置 | 缺项与判定依据 | 后果 | 一句话修法 |
|---|---|---|---|---|---|---|
| C-01 | 断链 | **BLOCKER** | Voice ↔ Core；基线 §8–§13 vs 详解页 §02 Core/Voice | 没有 transcript/turn 交接接口、session_id/turn_id、ASR 终态/错误或 TTS 请求/完成事件 | 唤醒和识别即使各自能跑，也交不到理解；Core 的回复也交不回会话/TTS，主对话链断在模块边界 | 固化 `voice.turn.final`→`core.handle_turn` 与 `core.reply`→`voice.speak` 两个 versioned envelope，含 turn/session、deadline、错误和取消。 |
| C-02 | 断链 | **BLOCKER** | Core → Console；树节点 6 vs 节点 47/详解页 L233 | Core 承诺多步计划，Console 承诺派发/依赖，但无 plan schema、handoff API、接收拒绝码；H-01 是节点空壳证据，本条为跨模块断链 | “理解成功”后没有可派发对象，执行链永远起不来 | 以 H-01 的 versioned plan schema 为唯一交接物，定义 `console.submit_plan` 与拒绝/回写。 |
| C-03 | 断链 | **BLOCKER** | Console → Middleware；详解页 §05 L304、基线 §15 | 只有“Console 决定，Middleware 跑起来”，没有 dispatch 请求/响应、deadline、去重键、状态/票据绑定 | Console 可排优先级但不能可靠启动一次执行；重试会重复派发或形成无票据 run | 定义 `middleware.dispatch(plan_id, step_id, executor, fileDomain, deadline, idempotency_key)` 与唯一 run/receipt。 |
| C-04 | 断链 | **HIGH** | Console ↔ Shell/Manager 与 Middleware→Shell；基线 §15.1、§21.2 | “起/停/查意图”“上交存活/无主/回收结果”“句柄交 Middleware”均只有角色叙述，无命令/事件名、ack、超时和错误 | Console 发停机后无法证明 Shell 已接受/完成；Manager 也无法把同一个 host task 的结果关联回意图 | 定义 `host.control`/`host.fact`/`pty.open`，统一 host_task_id、instance_token、command_id、ack/final 和超时。 |
| C-05 | 断链 | **BLOCKER** | Middleware ↔ executor/MCP/tool plugin；树节点 72、注册分类 §④、基线 §18 | 只有 ID 与“harness 有重试/超时/schema”字样；没有 prepare/start/stream/cancel/finalize、标准错误、幂等和 receipt ABI。与 H-04 同根，**本报告总数以 C-05 计一次** | 已知 D2 即使把真实 harness 接上，各适配器也不能互换，取消/失败会各说各话 | 冻结 executor/tool SPI 与能力协商，再实现 D2；禁止先按具体 Codex/DeepSeek 私有字段接线。 |
| C-06 | 断链 | **HIGH** | Engine/Console ↔ Client/Surface/Admin；双域规范 §11.2、详解页 §05 L307 | 三条箭头没有端点/transport、版本、auth、event_id/sequence、snapshot/reconnect；与 H-03 同根，**总数以 C-06 计一次** | 8756 虽存在，壳与运营端仍无法可靠订阅、恢复或提交受控操作；重连会漏/重放状态 | 固化 8756 API/event schema、版本协商、local auth、cursor snapshot、ack/reconnect 及只读/受控写权限表。 |
| C-07 | 无主 | **HIGH** | Governance → 全部；注册分类 L87 `tool.policy.check`、详解页 L308 | policy 工具有名字，但没有哪个执行入口必须调用、在注册/路由/执行的哪个顺序调用、拒绝如何回任务态 | 权限策略可能只存在于规则库而未成为强制门；模块可绕过治理直接执行 | 在唯一 dispatch/tool gateway 中硬绑定 preflight+pre-side-effect 两次 policy hook，返回 versioned decision_id 并写审计。 |
| C-08 | 断链 | **HIGH** | 全模块 → Log Store；基线 §22.3 | 全文 `log.append/audit.append/日志写入` 0 命中；只有 `log.query` 与“必须留痕” | 权限拒绝、主脑换型、外部调用等承诺事件没有统一落点，哈希链也无写入者 | 定义唯一 append API、分类 schema、脱敏器、prev_hash 原子追加、背压和存储失败策略。 |
| C-09 | 断链 | **BLOCKER** | Update → Lifecycle → Shell；树节点 80–86、双域规范 §七 | manifest/签名、安装执行、进程起停分别存在，但没有 staged package→停机→切换→首启健康→commit/rollback 契约；与 G-08 同根，**总数以 G-08 计一次** | 更新包通过签名后仍无法安全应用，半更新无法自动恢复 | 由 Lifecycle 拥有 update transaction，调用 Shell quiesce/restart，并以首启健康回执驱动 A/B commit/rollback。 |
| C-10 | 断链 | **HIGH** | `kb.collect.*` Skill → Memory.kb；基线 §18.6 vs §17.3 | 无 ingest API、source/license/content hash、用户确认 token、分块失败/回滚或重放去重 | 采集完成的内容不知道如何原子入书架；失败可能留下正文无索引或重复书 | 定义 `kb.ingest(batch, shelf, source, license, consent_id, idempotency_key)` 与整批/逐项回执和补偿。 |
| C-11 | 断链 | **HIGH** | Voice ↔ Client；双域规范 §11.3 L204–L208 vs 基线 §8–§13 | duck、DND、音量语速由客户端策略，但引擎只称“给事件/接受参数”，无事件名、有效期、ack 与异常恢复 | 播报开始可能未 duck、异常退出无法还原音量；DND 在客户端和语音状态之间漂移 | 定义 `media.playback.started/ended/aborted` 与 `client.audio_policy` 快照，command_id+ack，异常/断连强制恢复。 |
| C-12 | 孤儿 | **HIGH** | `tool.habit.read/update`、`skill.habit.extract`；注册分类 L101–L103 | 精确 ID 全文分别只命中注册表 2/1 次；R-21 只说每次交互必读，没有 Core/interaction loop 调用边 | “越交流越聪明”所需能力虽登记却无人调用，习惯既不会注入也不会形成闭环 | 指定 Core context composer 为 read caller、每轮 post-turn pipeline 为 extract caller，并定义 update/negative-sample 回执。 |
| C-13 | 孤儿 | **MED** | Console 多端调度；树节点 50、基线 §19.2 | 全文 6 次命中均为定义/释义/验收措辞，没有设备 registry、transport 或客户端消费者；与 H-02 同根，**总数以 C-13 计一次** | v1 单用户前提下仍挂一个“跨多用户设备”的承诺节点，无法调用也无法验收 | v1 收窄成单用户显示端投递并接 C-06；多用户设备能力移到明确版本门。 |
| C-14 | 无主 | **HIGH** | Console/Lifecycle/Shell 安装链；注册分类 L78/L81/L127 | `tool.console.toggle`、`skill.console.install_flow`、`tool.install.run` 各只命中一次；Console 又被禁止碰进程/磁盘，实际装卸执行者在 Lifecycle/Shell，但无分层契约 | Console 可能被实现成直接写盘/起安装器，或三模块都等别人执行，装卸不闭环 | Console 只拥有意图与进度；Lifecycle 拥有安装事务；Shell 只执行进程命令，三者用 command/ack/final 契约串联。 |
| C-15 | 孤儿 | **MED** | `skill.freeze.audit` → `tool.freeze.tag`；注册分类 L91–L92、R-34 | `tool.freeze.tag` 精确 ID 全文仅 1 次；虽写“外脑审、主脑打 tag”，没有 audit PASS 产物、主脑触发接口与失败回传 | 审核通过后可能无人打 tag，或主脑在未验证审计身份/产物时直接落本地副作用 | 定义 signed audit decision→`freeze.apply`，校验任务/commit/auditor provider，tag 失败回 `BLOCKED`。 |
| C-16 | 断链 | **HIGH** | Memory → `plugin.store.*`；树节点 41 vs 注册分类 L105/L138–L139 | Memory 写 `store_backend` 内部件，注册表又把 sqlite/file/vector 称插件，但没有 store SPI、选择规则或降级数据迁移 | 停用/换存储插件时 Memory 不知道如何保持 schema、索引和已有数据；“SQLite→文件降级”会变成第二套数据源 | 固化 store SPI 与能力矩阵；v1 只允许一个 authoritative backend，切换须离线迁移+条数/哈希对账。 |
| C-17 | 断链 | **HIGH** | Middleware/Tool 失败 → Console/业务补偿；基线 §15 状态机、§21.5 | 有 FAILED/retry 与“快照不撤销外部副作用”，但没有 partial-result/side_effects/compensation 票据或回滚责任人 | 多步执行第 2 步失败时，前一步写盘/发消息/提交仍生效；简单回队会重复副作用 | 每 step 票据记录 side_effect id、commit point、compensator 和人工确认；无补偿的副作用失败必须 BLOCKED，不自动回队。 |
| C-18 | 断链 | **HIGH** | Core ↔ Memory 写/查失败；详解页 §05 L302–L303、基线 §17 | 只有入口名/“没找到”，无 timeout、存储错误码、写失败时回复是否继续、重试/去重、已回复后写失败补偿 | Memory 锁住、卷离线或索引失败时，Core 可能卡死会话、重复写习惯，或向用户宣称“记住了”但实际没写 | 定义 memory result/error contract；读超时降级空结果，写采用 idempotency key，只有 commit 回执后才能对用户确认已记住。 |

## 4. 三类计数与全文孤儿依据

- **断链 13**：C-01/C-02/C-03/C-04/C-05/C-06/C-08/C-09/C-10/C-11/C-16/C-17/C-18。
- **孤儿 3**：C-12/C-13/C-15。
- **无主 2**：C-07/C-14。
- 合计 **18** 个物质性发现；分级 **BLOCKER 5 / HIGH 11 / MED 2 / LOW 0**。
- 孤儿全文检索：`tool.habit.read/update` 仅注册表 2 行，`skill.habit.extract` 仅 1 行，`tool.freeze.tag` 仅 1 行；“多端调度”6 次均是定义/释义/验收，没有消费者接口。上述搜索范围固定为八份被审文件。

## 5. 失败与回滚专项

| 场景 | 已有 | 缺口/结论 |
|---|---|---|
| 执行域失败 | 八态 FAILED、retryCount、reworkCount、worktree | 部分副作用与补偿无人负责，见 C-17；运行中取消不可达见 E-01；幂等重放见 G-05。 |
| 记忆写入失败 | 权限拒绝、容量告警、索引一致门 | Core↔Memory 无错误/确认契约，见 C-18；跨卷 crash-consistency 见 G-07。 |
| 本地主脑超时 | 30s→重试1次→R-47 梯子 | **查过，闭合**；但输入/输出预算互斥见 E-02。 |
| 外部主脑/provider 超时 | `unreachable` 指数退避 3 次、`rate_limited` 不重试、外部主脑坏回本地 | **查过，主路径闭合**；provider 请求字段仍为半契约（矩阵边 23），未另立严重发现。 |
| 更新失败 | 签名、灰度比例、口头“必须回滚” | 应用事务断链，见 G-08/C-09；灰度止损缺失见 G-09。 |

## 6. T4 Gate

- 跨模块边：**26**，全部逐边检查接口、入出参、错误、超时、幂等/重放；完整 1、半契约 4、断链 21。
- 三类发现分别计数并给出全文孤儿依据；容器节点没有冒充接口。
- 每个 C 条目均有两端位置、缺项、运行后果和一句话修法；与 G/H/E 同根者明确指定总报告的唯一计数编号。

