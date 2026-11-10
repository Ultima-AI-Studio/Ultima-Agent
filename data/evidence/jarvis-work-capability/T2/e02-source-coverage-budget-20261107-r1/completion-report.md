# E02 读取预算与来源覆盖联动补修完成

原单 wo-ultimaagent-20261101-0021 / T2；完成范围为本轮授权的两项产品修复、离线验证和独立准备审查。产品候选 e40a55b40c223181040dbb6a09d0c4d2da5026cf，基线 ee1bef61f04169c64978538dbc4ba799ef7be6c0。当前 E02 仍 0/3，T2/Owner 未通过，没有新实际研究分配。

## 实际修改

六次读取额度联动至少三来源覆盖。生成与独立重放共用相位 schema：仅从可信 catalogue 取可用来源，只认已确认的非空证据卡；已发行页和待提升的确认页按原顺序计入一次。当剩余读取数正好等于缺少的来源数时，inspect 的 source_id 只能选择尚未覆盖的可用来源。有余量或已覆盖三来源时，仍可同源补读；剩余额度或可用来源不足时关闭 inspect。页起点、来源相关性、事实和写作仍由当前 8B 决定。

未写入时 final_answer 的合法内容固定为“本次研究未交付。”；任意“已保存 research.md”不再是合法拒绝分支。只有通过原写入、读回和 proof 门的 ACK 相位才保留自由确认文字。研究失败的公开回复同样明确“未交付”；若存在写入效果则补充“部分操作可能已生效，请核对结果”，不虚称文件必定不存在。非研究失败文案保持。

复用既有 OpenJarvis inspect/write、native_react、JSON schema、ledger 和重放，没有引入新 planner、拼写事实或替模型生成报告。仅四个产品模块和三个测试文件变化；原生传输、响应解析、HTTP 诊断、默认模型和既有事实/引用/写入/ACK 门未改。

## 当前验证

旧代码新增测试 RED：39 个断言失败、1 通过、errors=0，真实 SDK mock 复现第五次同源仍消耗读取额度、虚假完成文本进入 final。修复后当前字节去重 746 项 PASS，其中产品 740、原受限导出兼容 6；新增目标测试 40 项。完整 SDK MockTransport 实际完成六次读取（S1 四次、S2/S3 各一次）、write、ACK、文件读回和独立重放，共八个模拟 POST；扩大第五次读取 schema 的一致性篡改也被重放拒绝。

初次传输回归 103 通过/1 失败保留：旧 blank_final 断言期待较晚的空白检查，新固定 enum 正确提前拒绝。仅更新该错误预期，保留无写入、无 ACK、确认页未提升等全部断言。合法拒绝 fixture 更新为固定文本；1000 字符私有诊断边界移至合法 ACK 后的独立 artifact 校验失败场景，保留敏感、超长、伪造和迟变更负例。最终所有分片重新按当前源码快照执行，旧执行不重复计数。

原审计守卫、90 秒分片和两个既有 live/HTTP/junction 排除保持。审计回执清洁，不冒称操作系统抓包；实际模型调用、实际用例、UI/音频及服务操作均为 0。计划独审 PASS，封存准备包独审 PASS_PREPARATION_ONLY。Manifest SHA256 2e6fd25cfb671552c7be87ce51b4d0fcc4b0216c65a1c042e5005b2aca7e0dd8；review SHA256 e59a105ff83691a4e13ed522b9aff268045733ee35f8ed5a24aab93215ec8fc9。

## 保全和交付边界

只读核对点 2026-11-07T09:36:27.352812+00:00、2026-11-07T09:48:02.275961+00:00 的七个保护进程身份、Ollama 0.32.15 和当前 qwen3-8b-uncensored 摘要相符；不声称连续存活。N13/N12/N11 旧失败、冻结候选、依赖清单和九个无关文件逐字节保全。上一实际例 91406fa9-5952-4e3a-99af-a94c8857c8d3 仍为 FAIL_CONFIRMED，六读只覆盖两来源，无 research.md/write/ACK，无重试。旧 E01/E03 通过记录不迁移为本候选信用。

原题四来源、至少三来源门、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8，service260/client300/root275/cleanup310/seal315 秒和上下文/实体/输出预算保持。只用当前 8B；不使用 14B。本轮证明离线约束和对接正确，不证明真实模型能完成原题；旧写入相位 HTTP500 的原生兼容原因仍未确证。

下一步先为本候选准备新的受控入口及源码/依赖绑定，更新受限测试中公开固定未交付文案与私有 final 对象的区分，不能照搬旧 candidate/manifest/authority。之后明确分配单例才能取得真实 8B 请求回执；事实、覆盖、写入和 ACK 仍按原门验收。本轮没有创建实际入口、authority、release 或模型重试。

本地产品候选保留在隔离分支 codex/jarvis-e02-source-coverage，不覆盖已封存的旧工作区。项目文档和 UltimaDocs 镜像按本地 commit/tag/readback 收口。此前 GitHub push 被自动审批以 blocked by policy 拒绝，本轮未重试，remote_synced=false。

证据根：H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-source-coverage-budget-20261107-r1
