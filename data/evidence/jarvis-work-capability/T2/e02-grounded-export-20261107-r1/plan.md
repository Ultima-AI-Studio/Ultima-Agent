# E02 导出诊断与研究依据改进计划

> 执行方式：superpowers:executing-plans，主会话顺序实现；独立会话审查计划、准备包和唯一实跑结果。

**Goal:** 继续当前社区 8B，在原研究目标和验收要求下定位导出失败，改善引用归属与题目覆盖，并验证一次完整研究。
**Architecture:** 复用 OpenJarvis NativeReAct、现有分页证据、schema、writer 与独立重放。只补现有导出观察器的有限诊断，以及通用研究导航与证据解释；不重写 Agent 循环，不生成后改写文稿。
**Spec:** H:/UltimaAI/UltimaAgent/docs/specs/jarvis-work-capability-contract-20261101.md，r2，R01/R02/R03/R05、E02/T2。
**Authorization:** 用户在本会话明确要求“按建议的顺序继续推进”，承接刚才报告的诊断、引用与覆盖修复、离线和独审、真实验证顺序。包括必要只读独审和准备 PASS 后一例当前 8B 原题四来源研究及结果复核；该单例失败不重试。

## Global Constraints

- 原工单 wo-ultimaagent-20261101-0021；旧失败、旧候选 1ecd75d 与全部绑定证据原位保留。新工作区 jarvis-e02-grounded-export 从该提交建立，不改生产默认。
- 当前 qwen3-8b-uncensored，摘要 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330；不使用 14B，不安装或更新依赖。
- 原题四来源 corpus SHA256 9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002。受控验证不充当真实联网验收。
- 原 CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315 秒；retry0。32768/49152 字节及 16384 context 门保持。
- 既有七保护身份基线仍绑定原文件；漂移先只读核对，无服务控制、音频或 UI 操作。原 E01/E03 信用不转移。
- N9 证据根：data/evidence/jarvis-work-capability/T2/e02-grounded-export-20261107-r1。准备 PASS 不等于 E02 通过；单例最多新候选 1/3。
- 所有源码/回执/历史失败保留；本地提交、tag、文档镜像；远端 push 先前被自动审批 blocked by policy 拒绝，本轮不重试或换通道。

## Evidence and root-cause limits

N8 服务已写出文稿，export_completed 的 verify_runtime_packet、validate_export_structure 或 preserve_completed_members 链抛 ValueError。旧回执未存分支/消息，原始 packet 未导出，不能追认某一分支为历史根因。已确认的可修问题是错误定位信息丢失。离线合成只能证明覆盖的兼容缺口，不能冒称复现 N8。

独立事实复核发现 7/14 引用不支持，2/14 有限制，任务覆盖不足。当前文档 landmark 只有坐标、没有内容提示；phase 没有说明七字段卡片的锚点与上下文区别，也没有解释“可写”不表示题目已覆盖。这是可检查的输入信息缺口；改进它不保证模型语义正确，最终仍由独立事实复核裁定。

## Task 1: 有限导出诊断

Files: N9/harness/adapter.py、test_adapter.py；N9/verification 的离线运行与绑定脚本。

- [ ] 先 RED：runtime 验证、结构检查、成员保存三个阶段异常必须保存不同阶段；原异常仍抛出、不得写 success/END。动态敏感错误文字不落盘。
- [ ] 最小实现：在原 export_completed 的阶段边界捕获诊断；仅记录固定阶段、允许的异常类别、受信源码中的函数/行号、有限错误标识或消息长度/摘要，不记录原文、locals、packet、secret。无第二次验证/重试。
- [ ] 保留 install_trusted_exports 旧失败回执；追加独立诊断文件，防止改变旧结果协议。诊断自身失败不得掩盖原异常。
- [ ] GREEN：注入失败覆盖三阶段、敏感文本、诊断写入失败，以及真实 SDK MockTransport 的完整导出成功和拒绝路径。检查当前真实元数据的离线兼容；无证据则保持历史根因未知。

## Task 2: 研究导航与事实依据说明

Files: src/brain/work_navigation.py、agent_server.py、work_research.py、src/brain/tests/test_work_grounding_context.py。

- [ ] 先 RED：文档目录缺少可选内容线索；生成与独立重放需要一致、能解释卡片坐标和覆盖要求的 phase。
- [ ] 为现有文档 landmark 附加来自安全可见原文的短内容标签；优先结构标题、保持行号和原 8 landmark/4096 字节门。代码 landmark 仍使用已有 operation，不硬编码原题或来源答案。
- [ ] 统一纯函数构造研究 phase：明确卡片 [id,kind,operation,anchor_start,anchor_end,context_start,context_end]；只能对锚点支持的原子事实做结论，邻近上下文不自动支持；TODO 只是注释，不证明运行能力；读取页不足时用剩余 inspect 寻找相关依据，三来源可写门不表示任务完成；无法覆盖时如实拒绝，不补事实。
- [ ] generation 与独立重放从各自已验证输入调用同一纯函数；writer、schema、来源/代码/事实门不放宽。全部通用指导，不加入夹具答案或生成后改写。
- [ ] GREEN：合成无关/相邻引用、标题前置装饰、多语言/超长标签、安全删行、预算边界、phase 伪造拒绝；真实 SDK mock 全链路与受影响回归。语义正确仍待实跑独审，不将字符串断言当研究能力通过。

## Task 3: 封存与独立准备审查

- [ ] 固定代码候选及输入哈希，重绑原验证框架，离线跑产品研究/导航/传输/文件兼容、harness、绑定、入口、边界检查；原两项 HTTP/junction 排除仍单列。
- [ ] 独立审查 exact manifest、源码差异、测试、旧失败保护和原预算；重要问题最多一次定点修复及必要复核，未 PASS 不实跑。
- [ ] 本地提交/tag/镜像及独立字节读回；只读核对七保护身份和当前模型，任何实际准入门失败不绕行。

## Task 4: 条件单例与结果独审

- [ ] 准备 PASS 后按本次用户授权签发一例 authority，经原入口运行原题四来源研究一次。失败停止当前序列，不自动重跑。
- [ ] 无论成功失败，保存第一结果、诊断、实际产物及清理回执；一次只读独立事实/协议复核。
- [ ] 更新原工单和镜像，分别记录代码实现、离线、实际、事实、清理结果。若失败，明确剩余缺口；若通过，仅记同候选 1/3，不越过 T2/Owner 门。

## Review Focus

- 诊断不能泄露原始错误文本或使原拒绝变成功，不能用合成测试追认 N8 根因。
- 标签必须绑定安全原文和真实坐标；预算超限拒绝或按原目录规则减少 landmark，不能截断证据正文或增加权限。
- 指导不得加入原题答案、降低事实门、强行宣称文本标签证明代码实现；模型仍可能失败。
- 独立 replay 检测 phase 篡改；不能信任模型或 wire 自报约束。
- 测试通过与真实单例独审分开；旧候选/运行证据不变，生产和语音保持。
