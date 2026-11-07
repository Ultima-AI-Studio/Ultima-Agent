# E02 读取预算与未交付终态实施计划

> For agentic workers: use superpowers:executing-plans; main session implements, independent plan and preparation review.

**Goal:** 在原六次读取额度内保留达到最少三来源覆盖的机会，并使未写入时的结束回复明确“未交付”。
**Architecture:** 复用OpenJarvis现有inspect/write SDK工具、JSON schema、可信ledger与独立重放；用共享相位schema辅助函数约束可选source_id和未交付终态，保持原写入/事实/proof/ACK门。
**Tech Stack:** 既有Python/OpenJarvis/jsonschema/HTTPX MockTransport；不安装依赖。
**Spec:** 用户本轮“先修复读取预算与来源覆盖的联动，并让未写入时的结束回复明确说明未交付”；docs/plans/jarvis-work-e02-source-coverage-budget-proposal-20261107.md；N13实际91406fa9…结果及FAIL_CONFIRMED独审。

## 冻结范围

原单wo-ultimaagent-20261101-0021/T2；基线ee1bef61f04169c64978538dbc4ba799ef7be6c0留在旧工作区，旧N13/N12/N11证据不写。新候选C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-coverage/UltimaAgent，分支codex/jarvis-e02-source-coverage；新证据根N=data/evidence/jarvis-work-capability/T2/e02-source-coverage-budget-20261107-r1。

仅当前qwen3-8b-uncensored摘要6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题四来源、至少三不同有卡来源、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒、context16384/messages+schema32768/entity49152、既有256/2048输出上限保持。本轮actual0/model0，无UI/音频/服务操作/安装/14B；独审只涵盖代码与离线准备。原生写入相位HTTP500未确证，不能宣告修复。

## 开源复用与接口

使用现成OpenJarvis工具schema和native_react、jsonschema严格验证与既有HTTPX测试，不引入新planner或替模型编写报告。新增代码仅描述本应用已存在的六次读取/三来源/交付状态约束。

- src/brain/work_navigation.py：共享 `v3_phase_inspect_schema(base, available, visible, used)` 和 `v3_research_final_schema(*, ack=False)`，以及固定未交付文本 `RESEARCH_NOT_DELIVERED='本次研究未交付。'`。
- src/brain/agent_server.py：从可信catalogue取可用来源；visible只取已发行页及已确认待提升页；used取ledger原计数。用共享helper构造相位schema，原SDK工具spec不变。
- src/brain/work_research.py：从已封存snapshot的可信catalogue/已重放reads重建同一helper输入；不读模型声明或prompt里的catalogue来授予权限。ACK逻辑保持。
- src/brain/work_service.py：研究失败的公开content明确“本次研究未交付”；若存在effects，继续提示部分操作可能已生效；非研究失败文字不变。不声称文件一定不存在，不泄露模型的虚假完成文本。
- 新测试src/brain/tests/test_work_source_coverage_budget.py；必要更新test_work_failure_diagnostics.py的合法拒绝fixture与公开/私有断言，使它继续测试诊断边界；不删旧负例或降低预期。

## Task 1 — 预算/覆盖联动及真实SDK验证

- [ ] 原单/DoR六项登记，独立exact计划审查PASS后实施；保全旧证据和无关文件；已存在的隔离工作区为冻结证据，新建工作区按提案执行，不安装或跑现场baseline。
- [ ] RED复现五次同源耗尽预算：真实SDK MockTransport前四次同源，第五次仍同源；新测试要求第5/6次schema为尚未覆盖的可用来源预留机会，旧代码应失败。另有自适应mock遵守合法enum并完成write+ACK，证明可达交付而非只拒绝。
- [ ] 共享helper严格验证used为int0..6、visible页数<=used、available唯一合法且不越过base source_id能力；只认原v3_source_reference_map中的非空卡。可用来源与已确认visible来源不一致则拒绝。available来自可信catalogue，非法/不可用/未确认/模型自报不计覆盖。
- [ ] `remaining=6-used`、`missing=max(0,3-covered)`。remaining不足missing，或尚未覆盖可用来源不足missing，或读满6时不提供inspect。remaining==missing且missing>0时enum仅允许未覆盖来源；有余量或已达3来源时保留合法同源补读。页起点和相关性仍由8B选择。
- [ ] live与replay同时接入共享helper，pending confirmed页在当前代计入，未确认页沿原边界拒绝；旧writer、实际read port、时限、扫描和一次消费不变。
- [ ] GREEN覆盖计数边界、重复/空卡/不可用来源、余量、布尔/浮点/负数/越界、真实SDK拒绝同源耗尽、最大六读+write+ACK八POST成功、重放schema篡改拒绝。

## Task 2 — 诚实未交付终态与离线收口

- [ ] RED：未write时final_answer='已保存research.md'应被严格schema拒绝；合法未交付文本可结束但无写入信用；公开失败content必须含未交付；保留partial-effects警示与非研究旧行为。
- [ ] prewrite final schema以enum固定未交付文本；ack=true保留原非空<=1000字段，只能在原_verify_file和ACK准入后使用。共享helper用于live/replay，不强写不足来源、不移除合法拒绝、不生成虚假proof。
- [ ] 更新合法拒绝测试fixture为固定文本；原“任意私有最终文本不应泄露”断言改为验证公开字段无私有final_answer对象，保留敏感/超长/伪造/迟变更负例；新增不真实完成文本负例，不能仅删除旧断言。
- [ ] 在原审计守卫下跑新目标RED/GREEN和相关完整产品回归，原90秒分片、排除的真实HTTP/UI类测试保持；原受限导出兼容检查采用当前候选和正确公开/私有契约。汇总去重且记录源码快照/audit/JUnit，不把旧706/339当新执行。
- [ ] 当前产品提交/tag、当前输入清单与准备包封存后做独立准备审查；只读核对七保护身份和8B元数据，旧证据/9无关文件哈希保全；报告/原单/镜像本地提交/tag/读回。远端此前blocked by policy不重试。
- [ ] 当前E02仍0/3、T2/Owner未通过；本轮不创建新实际authority或运行入口、不调用模型。后继受控实跑须基于新候选重新准备绑定和明确分配。

## Review Focus

确认覆盖约束只缩小inspect合法source_id，不选择事实或固定页序；边界剩余2/缺2和剩余1/缺1必须到达第三来源机会。不能用卡为空/未确认页抬高覆盖。可用catalogue必须来自受信ledger和已验证snapshot，不能从模型prompt扩大权限。真实SDK的旧错误序列要拒绝，新合法八POST序列应实际write/ACK并通过重放；仅mock返回成功不合格。prewrite严格未交付与postwrite ACK区分；部分effect不能虚称无文件。所有预算和原生请求构造/HTTP诊断不变，旧失败不覆盖。

## 执行裁定

本轮用户已授权两项产品最小修复及必要离线验证/独审，无需重复询问实施。技能默认安装、全仓现场测试和删除工作区不适用冻结/保护边界，保留审计ledger。Task2消费Task1的visible/read-count/schema接口，必须在同一候选对live和replay同步校验。修复成功只是离线准备通过，不替代实际研究验收。
