# E02 原生响应兼容性与 HTTP 失败诊断离线收口

本轮按用户“保持当前8B和原预算，先核对原生响应兼容性、补齐受限HTTP失败回执，再依据确证问题做最小修改”执行。离线补修及必要独审完成；E02仍0/3，T2/Owner未通过，没有新实际用例或模型调用。

## 完成的修改

当前候选 ee1bef61f04169c64978538dbc4ba799ef7be6c0，父版本2b42b3e19516154a26cbc895a3d9e69fabb07ab2；新隔离分支codex/jarvis-e02-http-diagnostics；代码tag ultimaagent-e02-native-http-diagnostics-candidate-20261107。仅一个产品文件src/brain/work_research_diagnostics.py及两份测试文件变动。

私有失败诊断升级v3，新增last_http：可信代次、固定路由、HTTP整数状态、请求SHA/大小、发包预留标记和有界计数。通过timeline唯一事件及wire代次/实体摘要绑定；实际状态与secured响应验证分开。支持发包前拒绝、无响应、500、200后坏JSON/schema/扫描失败、metadata失败等情况。正文、任意URL和异常文本不导出；原错误、扫描、冻结一次、16KiB上限和零验收信用保持。传输/请求构造、schema/重放、模型/预算、写入和事实门均未改。

## 兼容性核对与根因界限

当前GGUF模板支持enable_thinking=false，产品已传think=false、stream=false、temperature=0。固定版Ollama源码存在相应参数与JSON schema映射；没有确证需要重复设置参数、改采样格式或提高token上限。官方来源与本地元数据摘要见同名兼容性研究记录及证据根research/upstream/provenance.json。

前例500与原生peg-native解析告警有强时间/内容关联，仍非请求绑定回执。具体模板/schema/parser原因未确证，原生解析问题没有在本轮被宣告修好；没有从截断内容拼文稿。本次补齐的是源码已证明的诊断导出遗漏，尚无新真实HTTP回执。

## 验证及独审

38项新增测试在旧代码RED失败，未覆盖旧证据；当前字节700项产品回归（含43项HTTP诊断）与6项原受限导出helper兼容测试，共706项去重PASS。原两项HTTP/junction排除保持；未重跑整套现场harness或实际原生推理。受限Python审计记录均清洁，但不冒称OS抓包。

计划独审PASS；本候选准备独审PASS_PREPARATION_ONLY。准备manifest SHA256 26977820632f6dbac4bafa286533c48eb883907129ae6a2bb04e5beb7d2c3298，808成员；当前绑定1568项。独审回执SHA256 855a3d8eaf6dc60512ae86e099df23d5ed66b9e2dd572ab6aebb61b175a7be1e。提交后源码逐字节与测试快照匹配，候选工作区干净。报告不将离线测试/准备审查当成E02交付通过。

## 保护及后继状态

2026-11-07 16:29:29与16:44:12（北京时间）两次只读核对中，七保护身份、Ollama0.32.15与当前qwen3-8b-uncensored摘要6d7230a9…c7f9330相符；不主张连续存活。前例2501准备成员、49结果成员、4补充成员、1563原输入和9无关文件核验保持。

上一实际例be79869f-10e5-4c0d-96a9-144cd5967c12仍为FAIL_CONFIRMED，119.564秒，无research.md、write/ACK，清理PASS、retry0；该实际结果没有被覆盖。历史E01/E03不迁移到本候选。

当前CLI/search/GET/inspect/write/ACK/nativePOST以及service260/client300/root275/cleanup310/seal315秒预算全部保持；只用当前8B，永不14B。本轮actual_cases=0/model_calls=0/service_operations=0；无UI/音频。没有创建新实际harness、authority或release，当前单例分配0。后续先为新候选准备并核验接线/绑定与原预算，只有取得明确单例分配后才实跑；首个真实回执再决定原生兼容修复，失败不重试。事实、引用、覆盖、写入读回、ACK和清理仍须分别验收。

项目文档及UltimaDocs镜像按本地提交/tag收口；远端push此前被自动审批以blocked by policy拒绝，本轮未重试，remote_synced=false。

证据根：H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-http-diagnostics-20261107-r1
