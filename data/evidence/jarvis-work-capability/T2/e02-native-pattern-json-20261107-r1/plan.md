# E02 原生采样 JSON 字符串兼容修复实施计划

> For agentic workers: use superpowers:executing-plans; main session implements, independent exact plan and final preparation review.

**Goal:** 修复代码事实 pattern 在固定原生转换器中允许非法 JSON 字符串的兼容缺口，保留当前 8B、原预算、来源覆盖和严格交付门。
**Architecture:** 在既有 _research_sampler_schema 中投影已知可信代码 claim pattern，使采样字符串仅允许 JSON 字符与转义；严格 schema、writer 和 replay 事实规则保持。复用官方 llama.cpp b10488 转换机制与现有 SDK，不编写新引擎或通用 regex/GBNF 编译器。
**Tech Stack:** 既有 Python/jsonschema/OpenJarvis/HTTPX MockTransport；官方同版本 Python converter 仅作为离线参考，不安装、不修改 vendor。
**Spec:** 原单 wo-ultimaagent-20261101-0021 / T2；用户持续推进且仅当前 8B 的决定；docs/plans/jarvis-work-e02-native-writer-http500-diagnostics-proposal-20261107.md。原实际与结果独审额度均已耗尽，本计划只处理离线确证缺口。

## 范围与事实边界

冻结产品 e40a55b40c223181040dbb6a09d0c4d2da5026cf 保留在 jarvis-e02-source-coverage 工作区。新隔离候选目标 C:/Users/Administrator/.codex/worktrees/jarvis-e02-json-string-projection/UltimaAgent，分支 codex/jarvis-e02-json-string-projection；原生工具返回不同路径时只更新该路径绑定并记录，不复用已冻结目录。

新证据根 N=H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-pattern-json-20261107-r1。旧 N15 结果清单 e0fc7084754d492d7166e219e2596b15f5f2562783721e9ca80a85c2c9168b5a 不改；新 native supplement 独立保存。

已有原生日志时间/状态序列/卡 ID 对齐 5e6ea89c…，第7次500前生成840 token，truncated=0，出现 unparsed peg-native output。三段旧 claim pattern 接受的 raw 字符串均不是合法JSON。补证不是请求绑定回执，不能补填旧 transport 正文，也不能把未校验生成文本算作事实。官方 v0.32.15 的 LLAMA_CPP_VERSION=b10488；同标签 compat patch 没修改 schema converter。官方 C++ pattern 路径直接生成带引号的 regex-body，dot/否定类没有使用原生 JSON char。对应 Python reference 转换支持本计划使用的共同子集，未运行编译版原生 validator；不宣称二进制运行已经修好。

## 全局约束

- 只用 qwen3-8b-uncensored，摘要 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330；Ollama 0.32.15。
- 原题四来源、至少三来源证据、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/root275/cleanup310/seal315秒。
- context16384、messages+strict-schema32768、entity49152字节、输出256/2048上限不变；投影超原实体预算必须拒绝，不提高上限。
- 本轮 actual/model=0；无UI/音频/生产服务操作、安装、模型替换、native升级、非2xx正文读取。
- 原写入、ACK、事实/引用、一次消费、源码重放、防SSRF/清理/七保护身份门不变；E02仍0/3、T2/Owner未通过。
- 只在新候选改下述产品文件。旧产品/旧失败/九个无关文件不改；报告和镜像使用本地提交/tag/读回，先前远端 blocked by policy 不重试。

## Task 1 — 证据封存、精确接口与 RED/GREEN

**Files:** modify src/brain/agent_server.py；create src/brain/tests/test_work_sampler_json_strings.py；modify src/brain/tests/test_work_code_claim_schema.py 仅调整篡改fixture；N/verification 与 N/inputs；项目计划/报告、原单、t2、current-run、全局登记与文档镜像。
**Interfaces:**
- 保持 _research_sampler_schema(schema) 参数和返回类型。deepcopy 仍移除 sampler 的 maxLength；其他 schema 属性、enum、minLength、definitions、source/ref 分组保持。
- 新私有 _research_code_claim_sampler_pattern(pattern) 只接受 v3_phase_writer_schema 已发行的规范形状：固定前后缀中间为 re.escape(op)，op 遵守原<=200及原标识符规则。拒绝非法/未知 claim pattern；不将未知 pattern 静默变成无约束字符串。
- 只在 properties.claim 下出现 pattern 的 schema 节点投影；其他字段的安全 ID pattern 保持；组合分支继承 claim 字段身份，definitions 内照常递归。不递归修改 enum/const/default 中的普通业务数据。
- 从规范 pattern 提取 op 时，只逆转原合法标识符可能的 \. 与 \$；再次验证原标识符和 re.escape(op) 完全等于提取段，不写通用 regex parser。
- 采样 pattern 的 raw JSON 单位 J = ([^"\\\x00-\x1f]|[\\](["\\bfnrt/]|u[0-9a-fA-F]{4}))。
  boundary B 同 J，但第一否定类另排除 A-Za-z0-9_$.；dot 后边界 D 同 J，但第一类另排除 A-Za-z_$。
  输出为 ^(J*B)?escaped-op(BJ*|\. (DJ*)?)?$，实际字符串中去掉此处仅为可读的空格。
  ASCII op 保持明文约束。转义边界可能在解码后是单词字符；这是采样兼容投影的上界，必须由原严格 schema 拒绝，不授予 writer 权限。
- 严格 response_format 仍在 JSON 解码后用 Draft7Validator 校验；请求用 sampler，wire 同时封存两者；replay 已从 agent_server 导入同一投影函数，无需修改 work_research.py 或 work_navigation.py。

- [ ] 封存补证、官方版本快照/转换器来源、离线复现回执；备份登记并保留最后实际 FAIL，不分配新actual。精确计划独审PASS后实施。
- [ ] 创建新隔离候选，建立本计划 ledger，写新测试并在原代码下跑 RED。Expected: 旧 pattern 允许 raw quote/control/非法转义，断言失败；原产品未改。
- [ ] RED覆盖原生三段 malformed-string形状、最小引号注入/换行/裸反斜杠/非法escape；valid中国字、引号、反斜杠、合法escape、美元/Unicode操作名；正确源/证据/operation绑定，严格schema不可被投影就地修改。
- [ ] 实现上述窄投影；unknown claim pattern fail closed。修改旧 replay 篡改fixture为另一个规范但错误的operation，使它仍能构造连贯 sampler/wire hash并被原相位重放拒绝；另加未知形状直接拒绝测试，不能删除原篡改用例。
- [ ] 在原审计守卫下 GREEN。Expected: 新测试全过；只改变 JSON wire 字符串兼容，不改变严格输出事实门。参考 converter 仅 allow_fetch=false，原生模型调用0。

## Task 2 — 交付衔接回归与封存

- [ ] 真实SDK MockTransport写入成功路径包含带引号/反斜杠/中文的正确代码事实；由 JSON 序列化后符合采样 raw-body约束，经原严格验证、实际测试文件写入、hash读回、ACK与独立replay通过。Mock文本不计实际研究信用。
- [ ] 负例覆盖仅在转义层满足operation边界、缺失operation、跨来源/错误ID、sampler篡改及连贯hash、旧非法JSON均不能写入；合法未交付仍零信用。六读+write+ACK的原8POST路径与来源覆盖回归继续通过。
- [ ] 保留原90秒分片、离线审计守卫及排除项，运行新测试及 claim/reference/unique/coverage/transport/navigation/research/grounding/target/write-diagnostics/http-diagnostics/failure/native-metadata/delivery相关完整产品回归；无新现场测试。Expected: 源码不变、audit干净、fresh逐项去重PASS。失败只作本缺口离线修复，不触碰原实际额度。
- [ ] 当前候选提交/tag，输入与测试清单封存；独立准备审查绑定同一候选、计划与全部新证据。若有重要缺口，只按本计划有界修复并以RED/GREEN记录，不扩大写域。
- [ ] 更新原单/报告/镜像、本地提交/tag并逐字节读回；核对旧失败、依赖与九个无关文件保全。实际 native效果、语义交付及连续三轮均保持未通过，不以896个参考字符串或单元测试替代。
- [ ] 后继受控入口基于新候选另行准备；明确分配单例后才允许新8B请求。本计划不创建release/authority或复用上轮实际与独审额度。

## Review Focus

1. 这是 raw JSON body 的 sampler 方言，不能用其替代 decoded JSON Schema；任何 escaped词边界的过度接纳仍须被严格门拒绝。
2. 引号、反斜杠、控制字符和Unicode应可被正确JSON序列化，不能以禁止常用引号或中文来“修复”。
3. 只投影已知可信claim形状；ID正则、普通enum值、不可写终态和来源约束不能漂移。
4. 新GBNF体积/解析复杂度仍受原49152字节/时限/输出预算约束；未运行原生二进制与实际8B的限制必须披露。
5. 官方参考代码与本地服务日志仅是兼容诊断支持，不能替代产品真实写入、来源事实核验或旧结果清单。

## 执行裁定

用户持续推进总授权覆盖确证缺口的离线修复及项目规定的独立计划/准备审核；不再重复请求这些可逆步骤的许可。用户“明确分配单例后再取得真实回执”仍约束任何新实际请求。新worktree用于保留已冻结e40，不改其状态；技能通用安装/运行全仓/删除证据目录步骤按本计划边界替代为受限守卫和保留ledger。

## 官方依据

[Ollama v0.32.15固定原生版本](https://github.com/ollama/ollama/blob/v0.32.15/LLAMA_CPP_VERSION)；
[llama.cpp b10488 C++ schema converter](https://github.com/ggml-org/llama.cpp/blob/b10488/common/json-schema-to-grammar.cpp)；
[同版本Python参考转换器](https://github.com/ggml-org/llama.cpp/blob/b10488/examples/json_schema_to_grammar.py)。
