# E02 写入资格与证据范围提案独立评审

评审对象：`docs/plans/jarvis-work-e02-write-eligibility-and-evidence-scope-proposal-20261108.md`  
工单：`wo-ultimaagent-20261108-0028`  
评审性质：只读判断；不是实施、修复或验收

## 1. 一句话结论

**需补充澄清后再修。** 提案方向没有被证据推翻，但当前文本尚未给出可判定的通用任务覆盖契约，所称“两文件优先边界”未覆盖独立重放中的同一写入资格判定，而且保存 wire 的只读重建证明新增任一可渲染 S4 页面后，下一次写入请求都会先越过 `messages+schema=32768` 字节硬门，因而不足以直接支撑下一轮离线最小修复授权。

## 2. 五条建议逐条结论

| 建议序号 | 结论 | 关键理由 | 前置依赖 | 风险 | 最小落地描述 |
|---|---|---|---|---|---|
| 1. 衔接写入资格与任务覆盖 | **需澄清** | 冻结候选的 `agent_server.py:626-646` 确实把“三个已读来源”直接转成 writer 可见；`work_navigation.py:479-486` 只保留 inspect 机会，不证明任务覆盖。但提案没有定义一个可由 runtime 与 replay 同样计算、且不依赖本题 S4/URL/关键词的 coverage 输入、状态和 fail-closed 结果。 | 先批准机器可判定、任务无关的 coverage 契约；明确证据不足或容量不足时只允许继续 inspect 或明确拒绝交付。 | 把“来源数”“已下载”或提示词中的要求换名后当成覆盖，会重现本次错误；强制多读又会撞上字节门。 | 在共享契约中形成单一资格判定，并由生成与重放共同调用；未满足时不暴露 writer，不增加次数或预算。当前不能据提案直接编码。 |
| 2. 让选页服务于原题 | **需澄清** | 独审指出缺失内容位于 S2 `L41-61`、S3 `L22-24/L42-48/L58-100`、S4 `L1-4/L276-364`；现有 catalogue landmark 只是导航提示（`work_navigation.py:351-366,419-431`），不是任务相关性或证据。提案没有说明如何在不由 controller 代选页的前提下，判定选页是否覆盖原题三项内容。 | 先明确离线可审查的页选择/拒绝判据，并保持“模型选择、harness 不代选”。 | 隐含预选页面会把 controller 变成答案提供者；只强制读 S4 仍不能覆盖跨 89 行的相关区域，也不能补足 S2/S3 的漏读。 | 只允许改通用导航契约或可见提示；用保存语料验证“相关页可被选择、无充分页时拒绝”，不得固化本题页码。 |
| 3. 核验逐证据原子事实 | **需澄清** | 六条失败不是同一类：#1/#2/#4 为 `FAIL_SELECTED_ANCHOR`，#3 为 `FAIL_FACT_AND_SELECTED_ANCHOR`，#5 为 `FAIL_ANCHOR_AND_CURRENT_STATUS_SUMMARY`，#6 为 `FAIL_FULL_ANCHOR_SUPPORT`；现有 schema 能约束 evidence ID 和代码 operation，却不能仅靠 JSON 结构证明自然语言蕴含、TODO/实现状态或复合断言已被拆开。 | 明确离线独立 oracle：哪些保存负例必须被拒绝/拆分，哪些正例必须保留；不得用关键词命中作语义核验。 | 若只缩短 claim 或重复提示，可能让输出更短但仍错误；若新增语义 verifier，则已超出当前“两文件小补丁”叙述。 | 先把六类负例和第 7–9 条正例转成独立、可复核的离线判据；是否引入新证据协议或语义核验器需另行明示。 |
| 4. 只按确证问题做最小修改 | **需澄清** | 共享 prompt/schema/inspect 契约在 `work_navigation.py`，实际生成分支在 `agent_server.py`，但独立重放又在 `work_research.py:810-823` 重新计算 `eligible>=3` 并开放 writer；`work_tools.py` 只执行已签发的 writer permit，不独立判断任务覆盖。因此“两文件”只能覆盖生成侧，不能证明 runtime/replay 同构。另有源码身份偏差：提案依据是冻结候选 `43da3f0...`，当前分支缺少 `src/brain/work_navigation.py`，且当前 `agent_server.py` SHA 与候选不同。 | 明确授权的 commit/worktree；把 `work_research.py` 纳入允许修改或证明其无需修改仍可精确重放新契约。 | 漏改 replay 会使新 runtime 无法独立复核；在当前分支直接改会针对错误源码版本；暗中扩展模块会违反“小补丁”表述。 | 最小产品范围应按证据写成“共享契约 + runtime 适配 + replay 适配”，而不是预先锁死为两文件。 |
| 5. 离线通过后再准备入口 | **可执行** | 提案明确离线检查不等于语义已解决，新真实单例必须另行分配；这与当前 E02 0/3、实际用例与结果复核配额均为 0 的状态一致。 | 前四项澄清完成；离线回归、预算读回和独立准备审查均有不可变回执。 | 把离线 schema/回放通过误写成 E02 通过，或借入口准备提前消费实际用例。 | 保留旧失败与成功链路，只做零模型离线准备；没有新的明确授权时不创建真实入口、不签 grant。 |

提案中被弱化或含糊的核心有三处：任务覆盖的可计算定义、生成与重放的真实模块边界、以及“再读一页”与严格字节门的冲突。第 5 条本身清楚，但不能消除前四条的设计缺口。

## 3. 边界与预算

### 3.1 T0 必读材料读回

| 项 | 实际路径与关键行/字段 | 读回结论 |
|---|---|---|
| 提案 | `docs/plans/jarvis-work-e02-write-eligibility-and-evidence-scope-proposal-20261108.md:15-19,23-27,31-35` | 五条建议、不变预算、授权限制和源码引用均已读到底；状态仍是“提案，未实施、未独审、无新实际分配”。 |
| 独立结果复核 | `data/evidence/jarvis-work-capability/T2/e02-source-grounding-controlled-preparation-20261108-r1/review/independent-result-review.md:11-21,25-31,37-41` | `FAIL_CONFIRMED`；9 条陈述仅 #7–#9 为 `PASS_DIRECT_ANCHOR`。#1/#2/#4 为 selected-anchor 失败，#3 为事实与锚点双失败，#5 为锚点与当前状态摘要失败，#6 为完整锚点支持失败。 |
| 结果 manifest | 同目录 `review/result-inputs/result-manifest.json:2-9,31,76-78` | run 为 `d0109d12-520f-4f92-88a3-938e69905ba2`，状态仍为 `PENDING_ROOT_INDEPENDENT_REVIEW`；66 个成员中实际 `research.md` SHA 为 `974feebd...`。 |
| 根 controller 只读分析 | 同目录 `verification/result-source-analysis.json:13-66,67-152,154-161` | 五次 inspect 后第 6 代选择 writer；S4 仍在 enum 且未读；分析自身记录 `model_calls_by_analysis=0`、`actual_runs_by_analysis=0`、`acceptance_credit=0`。 |
| 冻结候选源码 | `C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-grounding-r1/UltimaAgent/src/brain/work_navigation.py:419-438,464-486,501-560`；同工作树 `agent_server.py:197-202,325-326,422-425,626-646` | 两文件 SHA 分别为 `a193a2e0...`、`38627867...`，与 source-analysis 一致；提案引用的 `479-486/626-646` 实际行号一致。源码均已读到底。 |
| 实际产物 | 同证据根 `actual/E02-controlled-1/outputs/1391bd35-6744-48d5-b57f-04e1b6f00d7f/research.md:1-22` | 1,735 字节，SHA-256 `974feebd...`；内容确有 9 条陈述，但没有 S4 section，且原题要求的调度/provider/工具执行关系与独立执行底座区别未答全。 |

工单卡写作中的 `outputs/.../research.md` 是相对 `actual/E02-controlled-1/` 的省略路径；完整路径存在并与 manifest/独审哈希一致，不构成缺件。源码行号则只对冻结候选 commit `43da3f014a763b8ea3963872a8f1ce8ebea77531` 成立：当前工作目录分支 `codex/voice-fsmn-new-path` 没有 `src/brain/work_navigation.py`，当前 `src/brain/agent_server.py` SHA-256 为 `d97dc1e9...`，与候选相差 650 行新增、18 行删除。下一轮必须先确定实际修改对象。

### 3.2 最小改动边界

**边界结论：部分成立，不能按“两文件足够”直接授权。**

- `work_navigation.py:419-438,464-560` 拥有共享提示、inspect 保留规则、writer/schema 合约，适合作为单一共享契约所在地。
- `agent_server.py:626-646` 拥有实际生成时的 eligibility 和 action alternatives，是 runtime 适配点。
- `work_research.py:661-665,810-846` 独立重建相同 eligibility、allowed actions、strict schema、输出预算与字节门，是第三个真实的 replay 适配点；提案只说“同步生成与重放”却没有把它列入优先文件边界。
- `work_tools.py:349-417,611-635` 执行 writer claim、reservation、intent 和物理写入绑定，但它信任上游已签发的 expected action，不自行判断任务覆盖；当前证据不要求先改它，但必须有回归证明新资格不能绕过其 permit 链。
- `work_service.py:125-155,191-200` 同时注册 inspect/write 并在完成后验证 runtime/replay；它不决定每一代是否暴露 writer。当前证据不要求先改它。

因此，若修复改变 writer 可见资格，最小产品候选范围至少是 `work_navigation.py + agent_server.py + work_research.py`；若方案作者主张仍可只改两文件，必须先给出新契约下 replay 精确相等且无需改 `work_research.py` 的离线证明。

### 3.3 预算尺寸

只读计算使用保存的 `trusted-runtime.raw` 与 `trusted-replay.raw`，按冻结候选的 canonical JSON 和纯 `build_page` 逻辑重建；五个实际页面均与保存 wire 精确相等。没有模型调用、网络请求、实际用例或仓库写入。

| 门 | 当前实际第 6 代 | 新增一个可渲染 S4 页面后再写（紧凑下界/范围） | 判断 |
|---|---:|---:|---|
| `messages+schema <= 32768` | components `24421 + 5574 = 29995`；门实际计算 canonical `[messages,schema]` 为 **29998**，余量 **2770** | 对 S4 全部 284 个可渲染起点重建为 **33837–39147** | **全部超限**，最少超 1069；当前提案未给出合规容量解法。 |
| `entity <= 49152` | **31754**，余量 **17398** | **35831–42481** | 单项仍在门内，但不能覆盖前一字节门失败。 |
| `context=16384`、输出 `<=2048` | native `prompt_eval_count=8019`；按 `8019+512+2048=10579` 看实际轮有 5805 token 余量；实际输出 601/2048 | 新页后 writer 的精确 estimator 值取决于最终 coverage/schema 设计 | **需离线预演实测**；缺的是经澄清后的最终 schema/消息形状。即使 token 可容纳，当前字节门已先失败。 |
| 次数 | 实际 CLI1/search1/GET4/inspect5/write1/ACK1/nativePOST7 | 若把第 6 代改为 inspect，再 writer、ACK，则 inspect6/nativePOST8 | 计数理论上恰好触顶，不得再加读取或 POST；但当前写入请求会被字节门拒绝。 |
| 时间 | 实际仍落在 service260/client300/rootwork275/cleanup310/seal315 秒内 | 多一代的时间结果未由本单运行 | 保持原值；只能在后续获批的离线准备与独立审查中核对，不能由本单外推通过。 |

这说明“强制再读必要页面”不是当前预算内可直接实施的最小修复。容量方案不得通过删减原题、丢来源、减少必要证据、提高 `context/messages/entity/output`、增加 inspect/POST，或把 S4/URL/行号写死来获得通过。

### 3.4 禁止路径

1. 硬编码本题的 S4、URL、行号、标题、预制答案或三项内容模板。
2. 把“已下载”“已编目”“三来源已读”或“来源 ID 命中”当作任务覆盖或语义蕴含。
3. 增加 CLI/search/GET/inspect/write/ACK/native POST 次数，或提高任何时间、context、字节和输出预算。
4. 为过容量门删减原题、移除来源、减少必须证据或放松 exact-anchor 规则。
5. 由 controller/harness 代选页面、代拆答案、改写失败产物或给模型提供本题答案。
6. 用关键词、标题、TODO、邻近上下文或旧 E01/E03 信用替代直接语义核验。
7. 修改既有 run、review、`current-run.json`、terminal、grant、E02/T2/Owner 字段或全局主表来制造通过状态。

## 4. 必须澄清项

以下各项均须在代码授权前得到明确“是/否”答复：

1. **是否确认下一轮修改对象必须固定为 commit `43da3f014a763b8ea3963872a8f1ce8ebea77531`（或明确等价的新候选），而不是当前缺少 `work_navigation.py` 的 `codex/voice-fsmn-new-path` 工作树？**
2. **是否同意把 `src/brain/work_research.py` 纳入最小产品修改候选，以保证 runtime 与 independent replay 使用同一写入资格契约？** 若否，方案作者是否承诺先提交“只改两文件仍能精确重放”的离线证明？
3. **是否同意在提交可由 runtime/replay 同算的任务无关 coverage 状态机前，不授权代码修改？** 该状态机须明确：输入是什么、何时允许 writer、剩余读取或容量不足时是否只允许 fail-closed 拒绝。
4. **是否确认下一轮修复范围同时覆盖“写入时机”和六类 selected-anchor/事实表达失败，而不是只让模型多读一页？** 若否，本提案不能声称足以解决本次 `FAIL_CONFIRMED`。
5. **是否同意把 `messages+schema` 的 33,837 字节最小重建值视为当前设计阻断门，并要求新方案在不删题、不丢来源、不加预算的条件下给出 `<=32768` 的离线数值证明？**
6. **是否确认离线验收必须同时满足：共享资格契约、runtime/replay schema 精确一致、六条保存负例被拒绝或正确拆分、第 7–9 条正例不退化、四项预算门通过、无 controller 代选/改写？**

任一项回答“否”都需要把差异写入新提案；不能在实现中默认为已获授权。

## 5. 建议下一步授权范围

**立即下一步建议只授权“提案补充与独立复审”，不授权代码修改。**

- 模型调用：`0`。
- 实际用例：`0`；结果复核配额：`0`；不创建真实入口。
- 是否允许改代码：当前阶段 `否`。
- 允许写入的内容：仅新版本设计澄清文件及其独立评审回执；不得覆盖本报告、既有 run/review/terminal 或队列表。
- 产品源码：`work_navigation.py`、`agent_server.py`、`work_research.py`、`work_tools.py`、`work_service.py`、`profile.py`、`test_profile.py` 均保持只读。
- 本阶段验收判据：六个澄清项逐项得到是/否答复；锁定源码 revision；给出通用 coverage 契约；明确 runtime/replay 三处归属；在原预算下给出新增必要证据后的 `messages+schema <=32768`、`entity <=49152`、context/output 估算及 fail-closed 路径；独立复审结论唯一。

若上述澄清全部通过，可另行建议一张“离线最小修复”工单：模型调用和实际用例仍为 0；产品修改候选仅限冻结 revision 的 `src/brain/work_navigation.py`、`src/brain/agent_server.py`、`src/brain/work_research.py`，另加事先点名的定向测试文件；`work_tools.py`、`work_service.py`、`profile.py`、`test_profile.py` 默认只读。任何新增证据协议、语义 verifier、渲染/写入语义或第四个产品修改模块，都必须先单列差异并重新独审，不能沿用“小补修”授权。
