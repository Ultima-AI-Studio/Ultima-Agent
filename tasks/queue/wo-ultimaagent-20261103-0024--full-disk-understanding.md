# UltimaAgent｜全盘理解｜P0 全盘索引链路（只读建库）

- **task_id**: wo-ultimaagent-20261103-0024
- **stage**: 全盘理解·自管理系统 P0（目标北极星=电脑成为 Agent 意识体）
- original_work_order_id: wo-ultimaagent-20261103-0024
- revision: 3（2026-11-03 随方案 v0.4 同步：A2 沙箱不生成向量、A3 纯 Python/Tika 可选、A4 断点续扫、B4 墓碑双删双更、B5 三处注册、D1 命中率抽样排除沙箱域、4.4.1 分域索引模板、4.4.3 关联表 links.sqlite）
- authorization: 用户 2026-11-03 确认"全盘理解是完整链路是对的"+"图谱留本地不上云"；P0 只读建库，P1 图谱/网络球、P2 自管理后续单
- 状态：**待派发（2026-11-05 回收）：12:52 派发 pid 34552（run 20261105T045212052843Z）运行至 13:00 已产出 M1–M5 实施计划草案，因同项目 0021 R30 恢复轮并行在跑、违反每项目执行中 ≤1，被主脑主动停止；run 目录与草案保留，待 0021 收口后按 WIP 重派，不需重做前置分析**
- 计划：docs/plans/full-disk-understanding-delivery-plan-20261103.md（本单随方案落盘，P0 口径见 §4）
- 契约：本工单卡即契约；规划文档 §4/§5/§7/§8 为权威口径
- 草案检查点：无（本单方案由执行端分析细化，P0 口径已确认）

## goal

按规划文档 §4 P0 落地全盘索引链路（只读建库，不写不改文件）：
4.1 全盘枚举（C:–H:，跳过域清单与监听排除共用 config/disk-scan-excludes.json：系统/缓存/回收站/自身 data 目录；**每盘断点续扫**，scan-log.jsonl 记游标，中断恢复幂等；watchdog 增量监听 created/modified/deleted/moved 四类事件）；4.2 内容提取（**纯 Python 主链**：PyMuPDF/python-docx/openpyxl/python-pptx/chardet；Tika 仅环境有 JVM 时兜底；媒体只存元数据；单文件 >10s 跳过留档）；4.3 规则分类打标（确定性标签体系，不依赖 LLM）；4.4 双索引（SQLite FTS5 全文 + **fastembed bge-small-zh-v1.5 512 维向量 blob 列同库存储**，**墓碑表 tombstones.sqlite 双删双更**；**分域索引模板 v0.4：文档域全文+向量、图片/音视频/应用/归档域仅元数据无向量、应用域 lnk 解析目标、归档域仅目录清单**）；4.5 检索入口 ultima_disk_search 接入 agent_server 工具表 **+ 0017 工具白名单注册 + L2 技能白名单三处注册**；**4.6 文件间关联表 links.sqlite（图谱前置输入，P0 确定性抽取：imports/references/lnk/duplicate，similar 留 P1）**。同时落地 §5 隐私沙箱横切（敏感目录/扩展名白名单入沙箱：**只存元数据、不生成向量**，明文不进持久层，内容访问默认拒绝+征询授权三档）。技术方案由执行端（Codex）自行分析细化后按 G-TASKFLOW-001 执行。

## acceptance[]

- ACCEPT: 全盘覆盖率——C:–H: 可枚举文件入库 ≥99%（排除项清单留档：系统目录/回收站/隐藏系统文件/二进制）。
- ACCEPT: 检索命中率——抽样 20 条真实文件关键词/语义检索 ≥90% 命中（首条 top5 内；**抽样排除沙箱域，只抽常规域可内容检索文件，口径留档**）。
- ACCEPT: 增量监听——单文件新增/修改/删除触发局部更新，5 秒内索引生效（watchdog）。
- ACCEPT: 沙箱隔离——沙箱目录条目可检索到元数据，但明文不可直接读出（持久层无明文）；**沙箱条目不生成向量（A2）**；征询授权后可读，全程审计留痕。
- ACCEPT: 索引体积与耗时留档——首次全量耗时、索引体积、每盘明细写 scan-log.jsonl；**断点续扫能力实测留档（中断恢复后覆盖率不倒退）**；**删除/移动同步实测（墓碑表双删双更后检索一致）**。
- ACCEPT: 工具注册痕迹——ultima_disk_search 三处注册（agent_server 工具表 / 0017 工具白名单 / L2 技能白名单）证据齐备。
- ACCEPT: 分域索引模板——文档域有全文+向量；图片/音视频/应用/归档域仅元数据无内容向量；应用域版本/签名/lnk 目标解析正确（抽样核验）。
- ACCEPT: 关联抽取——links.sqlite 的 imports/references/launcher/duplicate 四类抽样各 20 条正确率 ≥80%（v0.4）。
- ACCEPT: 既有功能不倒退——environment.py / environment_upgrade.py / memory 三层既有行为回归通过；验收解释器=tools/venv-openjarvis/Scripts/python.exe（3.13.16）。
- ACCEPT: 独立审计 + Owner 真实体验 + 冻结 tag + 产出与回滚说明全部齐备后才关闭本单。

## dependsOn[]

- 0022 中间层 v1 收尾（当前 executing，本单 pending 排队）
- 既有环境快照 L3（src/brain/environment.py）+ M16（environment_upgrade.py）——只读扫描经验复用，不倒退
- 既有向量检索 fastembed bge-small-zh-v1.5（src/brain/memory/vectors.py）——复用嵌入链路
- s3-guard-resident 权限闸门 + L8 征询（沙箱授权复用）
- G-TASKFLOW-001 工作流（登记→计划→执行→审计→验收→冻结）

## fileDomain[]

- `H:/UltimaAI/UltimaAgent/src/brain/disk_index`（新模块落位，执行端可按既有 src 结构微调）
- `H:/UltimaAI/UltimaAgent/src/brain`（检索入口接入 agent_server 工具表）
- `H:/UltimaAI/UltimaAgent/data/disk-index`（索引/向量/图谱/scan-log 数据域）
- `H:/UltimaAI/UltimaAgent/docs`
- `H:/UltimaAI/UltimaAgent/tasks/queue/wo-ultimaagent-20261103-0024--full-disk-understanding.md`
- `H:/UltimaAI/UltimaAgent/tasks/queue/runs/wo-ultimaagent-20261103-0024`
- `H:/UltimaAI/UltimaAgent/data/evidence/disk-index-p0`

## priority

- 80

## reasoningEffort

- high

## category + skill

- 架构·数据 / 索引与检索；executing-plans、test-driven-development、verification-before-completion；方案分析 + 分阶段执行。

## receipt

- data/evidence/disk-index-p0/ 各阶段记录原单/阶段/run_id、输入哈希、执行端、真实退出、证据、越界声明和开源选择。

## retryCount

- 0；审计 REVISE 最多两轮，继承本单失败历史和修订，不新建原单重置额度。

## 写什么与禁止

1. 先分析细化技术方案（读规划文档 §4/§5/§7/§8），分阶段执行；M1（全盘枚举+跳过域+断点续扫+元数据入库）→ M2（内容提取+分类打标）→ M3（双索引 FTS5+向量+墓碑）→ M4（ultima_disk_search 工具三处注册+沙箱闸门）→ M5（watchdog 增量四类事件+回归）。
2. 分类打标必须确定性规则（扩展名/路径特征/关键词），不依赖 LLM；标签体系按规划 §4.3。
3. 隐私沙箱：敏感目录/扩展名白名单（钱包/密钥/聊天/密码库/凭证，清单见方案 §5.3）条目**只存元数据、不生成向量**，明文瞬时内存使用，持久层无明文；内容访问默认拒绝→征询授权（本次/会话/长期三档，持久化见方案 §5.4）→审计留痕。
4. 全部只读：禁止修改/移动/删除用户文件；禁止写系统配置；功耗/自管理不在本单（P2）。
5. 禁止改主脑模型与推理参数；禁止改 production 默认行为（environment/memory 既有语义）；禁止重启现有语音/daemon 进程；禁止跳过前序验收、伪造完成或冻结。
6. 开源优先（G-OPEN-001）：os.walk/SQLite FTS5/fastembed(复用)/watchdog/networkx 已列；任何新增依赖先出开源替代排查表，无自研模块。

## 开源替代排查

| 子功能 | 现成件 | 采用与理由 |
|---|---|---|
| 全盘枚举 | os.walk（标准库） | 采用；够用不引 Everything SDK |
| 内容提取 | PyMuPDF / python-docx / openpyxl / python-pptx / chardet（纯 Python 主链） | 采用；Tika 降级为可选（需 JVM，默认不依赖 Java） |
| 全文索引 | SQLite FTS5（标准库内置） | 采用；零依赖 |
| 向量嵌入 | fastembed bge-small-zh-v1.5（既有接线） | 复用；512 维已有落地 |
| 增量监听 | watchdog（Python） | 采用；单文件事件局部更新 |
| 沙箱加密 | DPAPI（L8 既有）/ 或 SQLite 加密扩展 | 复用 L8 模式；默认持久层无明文不依赖加密 |
| 检索接入 | agent_server 工具表既有模式 | 复用 |

## 2026-11-03 建卡补记

- 用户 2026-11-03 拍板："图谱留本地不上云"+"全盘理解完整链路开工"；愿景=电脑成为 Agent 意识体（自管理系统/资料/功耗）。
- 本单=P0 只读索引建库；P1 关系图谱+网络球（0025）、P2 自管理巡检/资料/功耗（0026）后续单。
- 2026-11-03 用户拍板：**P1 图谱暂缓**，0025 不建卡不派发；P0 索引预留关系抽取输入（路径/标签/正文 FTS5/向量），随时可增量建图无需重扫（方案 v0.3）。
- 隐私口径：沙箱化授权（放沙箱、内容访问需授权），默认拒绝+白名单+审计，复用 s3-guard+L8。
- 当前 0022（中间层 v1）执行中、0023（Jarvis P0）pending，WIP 一单一进程 → 本单登记 pending 排队。
- 18766 UltimaManager 服务离线，登记走全局主表，待服务恢复后由主脑补登接口。
