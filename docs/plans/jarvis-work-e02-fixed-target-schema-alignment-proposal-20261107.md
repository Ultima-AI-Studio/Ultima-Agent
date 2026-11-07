# E02固定研究文件目标：schema与writer契约对齐提案

原工单wo-ultimaagent-20261101-0021 / T2。诊断候选6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696的一次实跑08d8377b-e1d2-40ba-8b7e-e20e1c66dfbd失败；安全诊断INVALID_TARGET对应唯一静态拒绝Research target must be research.md，长度35和SHA一致。实际传入path没有导出，不能称其为绝对路径或猜测其具体值；也不能倒推前轮失败原因相同。无research.md，E02/T2仍未通过。

## 已核实的接口不一致

work_navigation.py::v3_writer_schema目前向模型声明path为任意1至2048字符的string；work_tools.py::WorkResearchWriteTool.run却只接受字面值research.md。agent_server的阶段提示已经写Write only research.md once，且把同一v3 schema传入现有SDK/native JSON Schema输出约束、执行本地Draft7验证与运行证据重放。因此可以在现有接口中收紧一处schema，让模型生成约束和实际可执行目标一致。

## 最小补修范围

从6cb9284新建隔离候选；仅将v3_writer_schema的path限制为type:string、enum:[research.md]（可保留现有长度约束），添加必要回归；候选路径/哈希重绑。使用已有JSON Schema enum机制，不增加模型调用或另建研究框架。保留writer的精确research.md检查；不接纳任意绝对路径、不改写模型响应或原生证据字节、不放宽请求目录、引用、事实、扫描、END、ACK、文件读回、清理与时限。

离线先证明旧schema接受other.md/绝对路径/遍历等并与writer要求不一致，再验证新schema只接受字面research.md；通过原SDK mock transport验证发出的native format绑定该enum、坏路径在dispatch前拒绝且没有文件副作用、合法research.md仍完整写入/ACK/读回。所有既有拒绝与相关回归保留。原schema允许的其他path本就不能完成研究写入，此修改将拒绝前移并约束生成，不改变合法交付目标。

## 顺序与有界验收

1. 最小schema补修，RED→GREEN和受影响离线回归；本地候选commit/tag，封存与必要独立准备审查。
2. 仅审查PASS且提交/tag/镜像读回后，按新分配运行一次当前qwen3-8b-uncensored、原题四来源受控研究，并一次只读独立结果复核。失败不重试，保留首结果。
3. 成功仍最多登记新候选受控1/3，后续同候选研究、真实联网、E01/E03及T2出口门均保留；不能借用旧候选信用或把本轮807项离线PASS当实际研究通过。

原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/rootwork275/cleanup310/seal315秒不变。仅当前8B，禁止14B；四来源和原题不变，无UI、音频或生产服务操作。七个保护身份、其他工作区修改及旧失败保持。

本提案尚未实施，没有创建新候选或分配新实际例。当前诊断范围的一例运行已结束，结果独审按同一授权完成后结束该序列；后续产品schema修改及新单例需要新的明确范围。远端push仍受此前自动审批blocked by policy阻断，本地交付不重试或绕行。

## 2026-11-07 已授权接续

用户call_409cc146033c4184879042b1abac6383明确授权本补修、必要独审、通过后一例当前8B原题四来源研究及一次结果复核；失败不重试。本范围不再重复询问。旧失败及旧候选信用保留。

## Task 1: 固定目标schema补修与离线准备

从6cb9284新建隔离候选。先添加schema合法/非法路径与真实SDK mock transport用例，保存RED；仅收紧v3_writer_schema.path为现有字面research.md的enum，保持长度约束。证明native format和本地strict schema都保留enum、错误路径在writer派发前拒绝、合法交付/ACK/读回通过；原writer路径拒绝与事实/引用/END/时限原门保持。完成受影响回归、候选重绑、独立准备审查和本地commit/tag/镜像。

## Task 2: 已授权的单例和结果复核

准备PASS及提交读回后签发一次TTL120秒分配，原题/四来源/当前8B实跑一例；失败不重试。保留原始首结果、完整可用证据、清理和保护身份，做一次只读独立结果复核并按实际结果登记、提交/tag/镜像。不得把离线通过、旧候选信用或准备PASS作为研究通过。

## Review Focus

schema与writer都只允许research.md；native sampler和strict replay使用同一enum且没有改写响应；错误参数在派发前拒绝、合法完整链路保留；唯一现有产品源文件变化限于schema；原8B/语料/预算/时限/保护/清理门和所有历史失败不变。
