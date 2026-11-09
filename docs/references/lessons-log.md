# 教训库（Lessons Log）

- **版本**：v1.2 · 2026-10-29
- **性质**：M10 教训持续捕获的唯一落点（`docs/references/lessons-log.md`）；任何人/代理遇到问题**当场登记**，禁止等总结
- **登记规则**（governance M10）：
  1. 触发即登记：失败/返工/卡点/绕路/工具坑/超时/环境坑 → 当场写一条
  2. 条目必填：现象 / 根因 / 规避 / 复发标记（N 次）
  3. 审计轮强制扫描：新问题类型未登记 = 审计缺陷
  4. 新问题先查本库：已登记=复发（深挖根因），未登记=新类型（登记+评估升级范式）
  5. 教训升级范式走 M3；范式新增必须回填本库
  6. **所有问题进工程记录（2026-10-29 用户明确要求）**：不仅失败/卡点，凡排查过的"问题"（含误判、绕路、旧接口失效、字段解析踩坑、进程识别误解等）一律登记；重大修复另写 `docs/reports/fix-*.md` 详细报告并在此登记条目号

## 维度兜底表（M10-④，逐格检查防遗漏）

| 维度 | 已覆盖教训（条） | 待捕获 | 最近检查 |
|---|---|---|---|
| 执行质量 | 见下方 L 条目 | — | 2026-10-16 |
| 治理机制 | 见下方 L 条目 | — | 2026-10-16 |
| 产品交互 | 见下方 L 条目 | — | 2026-10-16 |
| 环境基建 | 见下方 L 条目 | — | 2026-10-16 |
| 工具链 | 见下方 L 条目 | — | 2026-10-16 |
| 数据备份 | 见下方 L 条目 | — | 2026-10-16 |
| 协作交接 | 见下方 L 条目 | — | 2026-10-16 |
| 安全合规 | — | 待捕获 | 2026-10-16 |
| 性能资源 | 见下方 L 条目 | — | 2026-10-16 |
| 人因认知 | 见下方 L 条目 | — | 2026-10-16 |

## 教训条目

### L01 大目录递归统计拖垮命令（性能资源）
- **现象**：迁移核对时对目标目录全量递归统计文件数/大小，命令超 15s 自动转后台，最终仍长时间不返回，只能终止改轻量方式。
- **根因**：GB 级目录 + 数十万文件，`Get-ChildItem -Recurse` + `Measure-Object` 全量遍历成本极高；foreground 命令有 15s 上限。
- **规避**：大目录统计先分层（顶层目录数/大小用轻量聚合），需要全量时用后台任务 + 分段读取，或先看进程/日志等轻量判据，不一次全量遍历。
- **复发**：0

### L02 上下文压缩后细节丢失（人因认知/协作交接）
- **现象**：多轮长会话后上下文被 summary 替换，历史工具结果与细节只能靠保留机制恢复，存在信息衰减风险。
- **根因**：上下文窗口有限，长任务必然压缩；压缩策略保留结论但丢失过程细节。
- **规避**：关键事实/ID/结论必须落盘（范式/台账/报告），对话不承载长期记忆；跨轮任务开工前先 Read 权威文档（README/范式/报告）补上下文。
- **复发**：0

### L03 PowerShell 下 Python 输出静默丢失（工具链）
- **现象**：PowerShell 直接执行 Python 脚本，stdout 有时静默丢失，看起来"没输出"。
- **根因**：PowerShell 对子进程 stdout 编码/缓冲处理不一致。
- **规避**：Python 输出必须 `*> file` 重定向落盘，再用 `Get-Content -Encoding UTF8` 读回；不依赖直出 stdout。
- **复发**：0

### L04 看门狗孤岛自治（治理机制）
- **现象**：主脑/宿主被杀后，独立运行的看门狗继续回写任务库、派发任务，替不存在的老板干活。
- **根因**：看门狗设计为独立进程/计划任务，与父进程无生命周期绑定。
- **规避**：已固化为 governance M9-C3 生命周期绑定（父死即降级只读静默+失联标记+优雅退出；先停守护器再退主脑）。
- **复发**：0

### L05 终端窗口闪跳（执行质量/工具链）
- **现象**：派发/探活/计划任务拉起子进程时，用户桌面弹出控制台窗口，闪几下或挂到任务结束。
- **根因**：裸 `os.system`/`cmd /c`/`python.exe` 拉起会新建控制台窗口的子进程。
- **规避**：已固化为 ops-selfcheck F1 全程无窗口纪律（CREATE_NO_WINDOW / pythonw / -WindowStyle Hidden）。
- **复发**：0

### L06 失败回执不结构化（执行质量）
- **现象**：任务失败只写"失败"二字，无命令/错误原文/根因/下一步，无法判断是否该重派。
- **根因**：缺少失败回执格式约束。
- **规避**：已固化为 acceptance-spec I3 失败回执结构化（失败命令/错误原文/根因判断/下一步计划，缺一不可重派）。
- **复发**：0

### L07 长任务全程静默（执行质量）
- **现象**：超过 15 分钟的任务无分段进度，审计无法区分"在跑"与"卡死"。
- **根因**：缺少分段上报约束。
- **规避**：已固化为 project-flow I4 长任务分段上报（>15 分钟分段写进度；60 分钟超时脚本处理）。
- **复发**：0

### L08 证据不足被猜测性判 PASS（治理机制）
- **现象**：回执/证据不全时仍判完成，假完成混入。
- **根因**：自动化判定没有 fail-closed 约束。
- **规避**：已固化为 acceptance-spec B1 判定 fail-closed（证据不明确一律 UNCLEAR/BLOCKED 留主脑）。
- **复发**：0

### L09 失败任务未修正继续派发（流程管理）
- **现象**：存在 FAILED/BLOCKED 未修正任务时仍派发后续，错误堆积。
- **根因**：缺少串行闸门。
- **规避**：已固化为 project-flow B2 串行闸门（未修正失败任务 → 不派后续）。
- **复发**：0

### L10 重启无根因，挂起缺陷反复卡死（运维）
- **现象**：daemon 探活挂起缺陷未修复就重启，重启后再次卡死。
- **根因**：重启前没有根因判断门。
- **规避**：已固化为 ops-selfcheck A2 重启根因门（无根因不重启；挂起缺陷未修复先记录不可用状态）。
- **复发**：0

### L11 常驻服务被误判为"在干活"（运维）
- **现象**：进程探测把永远在跑的常驻服务计入活跃判定，导致误判忙/误回收。
- **根因**：未区分"常驻服务"与"干活会话"。
- **规避**：已固化为 ops-selfcheck C4 进程识别规范（只认干活会话，探测脚本附排除清单）。
- **复发**：0

### L12 重复开发 / 旧版本混入（产品/治理）
- **现象**：历史开发中出现大量冗余、重复开发文件，旧版本混入现行区。
- **根因**：缺少能力注册表与单一现行版本约束。
- **规避**：已固化为 governance M1 能力注册表 / M6 单一现行版本 / M7 版本归档物理隔离 / M8 版本标识。
- **复发**：0

### L13 自清理边界缺失（治理机制）
- **现象**：看门狗对垃圾文件/状态无统一清理哲学，可能误删证据或留垃圾。
- **根因**：清理边界未定义。
- **规避**：已固化为 governance M9 自清理边界（状态级自愈自动、文件级保守不删，删除交人工/定期策略）。
- **复发**：0

### L14 文档新旧混放 / 版本漂移（治理机制/人因认知）
- **现象**：新计划写进旧文件、新段落追加后头部版本未动、正文残留旧段落——2026-10-16 文档结构化审计一次抓到 7 处（product-plan 标题/头部/日志三个版本打架等）；Owner 明确担心"新旧混在一起"。
- **根因**：文档更新无强制纪律——改内容后头部版本号或权威登记未同步（"改完就忘"的人因盲区）。
- **规避**：已固化为 governance M6-DOC（docs 正文区单一现行版本）+ version-plan-spec §5.1 文档新旧隔离纪律（跨版本/主题必须新开文件、更新三步一体、正文只留当前版、三处一致性强制）+ ops-selfcheck 文档新旧隔离检查（审计轮 MUST 抽查）。
- **复发**：0（首登记）

### L15 外部天气接口失效未预检（工具链/环境坑）
- **现象**：2026-10-29 天气直达路由首版用中国天气网 `weather.com.cn/data/cityinfo/{code}.html`，实测 HTTP 200 但返回 HTML 而非 JSON，`query_weather` 全部返回 None。
- **根因**：旧接口已停用（返回 WAP 页面）；未在接入前验证接口响应体格式。
- **规避**：接外部接口先发真实请求看响应体（JSON vs HTML）再写解析；失败降级返回 None 走 14B 兜底，不阻断主链路。已切换 wttr.in（`?format=j1&lang=zh`）。
- **复发**：0

### L16 按文档猜字段结构导致解析被静默吞掉（工具链/执行质量）
- **现象**：wttr.in 解析 `weatherCode` 按列表 `[0]` 索引（实际是标量 int 113），异常被 except 吞掉返回 None，且日志无任何提示——沈阳返回成功、北京返回 None 时才发现。
- **根因**：未先打印真实响应 keys/类型就写解析；except Exception 静默吞异常掩盖了结构假设错误。
- **规避**：解析外部 JSON 前先 dump 真实 keys 与类型；except 里至少 log 异常（或返回 None 时留诊断口）；多城市用例覆盖后再收口。
- **复发**：0

### L17 窄意图指令落入 LLM 自由发挥导致绕圈/甩链接（产品交互）
- **现象**："查天气"走 14B agent 兜底 → 119.84s 绕圈达到轮次上限返回英文报错 `Maximum turns reached without a final answer.`；此前还出现过甩一长串天气网链接让用户自己看。
- **根因**：确定性窄意图（天气/时间/计算等）没有专用直达路由，交给 LLM 自由发挥；14B 推理 + 搜索工具来回转圈，慢且答非所问。
- **规避**：已实现 interaction.py 第 5.5 步天气直达路由（`_WEATHER_INTENT` 正则 → wttr.in 直查 → 一句话秒答，1~5s）；失败才降级 14B。后续类似确定性意图（时间、日期、计算器）应同模式加直达路由。
- **复发**：0（首登记）

### L18 venv python.exe 是 redirector，父子对被误判为双实例（运维/执行质量）
- **现象**：2026-10-29 把 agent_server 进程对 15620(6MB 无监听)→22004(63MB 监听 8756) 误判为"双实例竞态"并杀掉 launcher 15620，实际是 venv redirector 的正常 launcher→解释器父子对；杀 launcher 连带解释器退出，靠 watchdog 20:05:24 自动拉起恢复。
- **根因**：不了解 venv python.exe 的 redirector 机制（launcher 不监听端口、解释器才是真服务）；仅凭进程大小/监听判断实例数。
- **规避**：判断进程实例数先看父子关系（ParentProcessId）+ 锁文件 pid + 端口监听者，不凭单进程表象；venv-asr/venv-openjarvis 的 python.exe 均为 redirector，杀 launcher 会连带解释器。
- **复发**：0

### L19 修改语音链路代码后未重启 daemon 导致改动不生效（运维）
- **现象**：天气直达路由改完 interaction.py/weather.py 后，运行中 daemon（旧进程已加载旧代码）不会感知新路由；若不重启，语音实测仍是旧行为（119s 英文报错）。
- **根因**：daemon 常驻进程加载模块后不重新 import，代码改动需重启进程生效；没有"改代码→重启 daemon"的流程记忆。
- **规避**：已固化：改 interaction.py/weather.py 或 daemon 本体后必须重启 voice daemon（杀进程对 → 锁文件由接管机制自动处理 → 核对新锁 pid + 日志 warmup/监听循环 + 输入设备解析），再语音复测。
- **复发**：0（首登记）

### L20 重采样算法用朴素线性插值导致唤醒置信度损失（工具链/执行质量）
- **现象**：2026-10-29 灵敏度调研发现 daemon 用 `np.interp` 做 44.1k→16k 降采样，用户"贾维斯"需喊两遍才唤醒；阈值已 0.04（低于基线 0.08）仍不灵敏。
- **根因**：44.1k→16k 正确做法是多相滤波（147:160 有理数重采样）；`np.interp` 线性插值引入频谱混叠/能量损失，唤醒词特征置信度被压低（业界明确警告 naive 插值）。
- **规避**：降采样改用 `scipy.signal.resample_poly`（多相滤波）；阈值降无可降时先查信号链路（重采样/增益/设备）而非继续压阈值。
- **复发**：0（首登记）

### L21 代码改参未同步权威基线文档（治理机制/L14 变体）
- **现象**：2026-10-29 调研发现 daemon 阈值已 0.04、44.1k 插值，但基线文档（kws-wakeup-params-baseline.md）仍写 0.08 + 16k 原生禁止插值，kws_listener 也仍 0.08——三处漂移，实际生效参数与文档不符。
- **根因**：改 daemon 参数/算法时只改代码注释（19:2x 那次），未按基线规则"改动前先读、改动后回填变更记录"同步权威文档；KWS 参数基线文档是唯一权威源，却成了事后静态快照。
- **规避**：KWS 相关任何改动（阈值/采样/增益/算法）必须①先读基线文档②改完立即回填基线文档变更记录 + 同步 kws_listener（产品主入口）③重启 daemon 实测。审计轮检查代码与基线一致性。
- **复发**：0（首登记）

### L22 ASR 通道同样用 np.interp 线性插值降采样致指令识别跑偏（工具链/L20 同源）
- **现象**：2026-10-29 21:00 真机：唤醒后说"查一下珠海天气"，ASR 识别成"查一下庭。"→ 天气路由 miss → 落入 14B 兜底 29s 返回空 reply，用户反馈"没回复"。
- **根因**：`src/brain/voice/asr.py` `_run_sherpa` 降采样 44.1k→16k 也用 `np.interp` 线性插值（与 L20 同源）。离线 A/B 同段录音：linear→"查一下庭。"（关键词丢失）vs sinc→"查一下武海天气。"（含"天气"命中路由）。注意：采集段自动增益后录音电平正常（peak 0.6），问题纯在 ASR 降采样算法。
- **规避**：ASR 通道降采样统一改用窗口 sinc 多相滤波（与 daemon `_resample_16k` 同款冻结实现），并抽公共辅助函数 `_resample_16k_sinc`；修复后重启 daemon 并用历史失败录音端到端复测（`data/logs/verify_asr_fix.py`）。排查语音"听不清"时同时检查 KWS 与 ASR 两处降采样。
- **复发**：0（首登记）

### L23 天气直达路由命中但 wttr.in 瞬时网络超时→静默 40s（外部依赖）
- **现象**：2026-10-29 21:07 真机（ASR 已修复识别出"查一下上海天气信息。"含"天气"关键词）：天气路由正则命中，但 reason=未命中 reply="" elapsed=48.87s——wttr.in 8s 超时返回 None → 降级走 14B 兜底 40s+ → 14B 也返回空 → 静默未命中。用户反馈"又没回复"。
- **根因**：wttr.in 境外公开服务瞬时抖动（独立进程实测 21:10 已恢复 HTTP 200、query_weather 秒答 4/4 场景）；`_try_weather_fallback` 查询失败返回 None 走 14B，而 14B 兜底既慢（40s+）又可能返回空 → 用户感知"没回复"。
- **规避**：①weather.py `_fetch_weather` 加重试一次（共 2 次、超时 8s→6s、总 ≤12s）；②interaction.py 天气意图命中但查询失败时直接返回降级话术"天气服务暂时不可用，请稍后再试。"（reason=天气查询），不再静默干等 14B。语音链路对外部依赖（wttr.in）要有快速失败出口。
- **复发**：0（首登记）

## 变更日志

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-16 | 初版：教训库落点 + 维度兜底表 + L01~L13 条目（含 M10 触发即登记规则） |
| v1.1 | 2026-10-16 | 新增 L14 文档新旧混放/版本漂移（governance M6-DOC + version-plan-spec §5.1 + ops-selfcheck 检查配套回填） |
| v1.2 | 2026-10-29 | 强化登记规则（用户要求"所有问题进工程记录"）；新增 L15 天气接口失效未预检 / L16 猜字段结构被吞 / L17 窄意图落 LLM 绕圈 / L18 launcher 父子对误判双实例 / L19 改码未重启 daemon；配套修复报告 `reports/fix-voice-chain-weather-20261029.md` |
| v1.3 | 2026-10-29 | 新增 L20 重采样朴素线性插值致唤醒置信度损失 / L21 改参未同步权威基线文档（三处漂移）；配套调研 `research/kws-sensitivity-research-20261029.md` |
| v1.4 | 2026-10-29 | 新增 L22 ASR 通道同源 np.interp 线性插值致指令识别跑偏（天气"查一下珠海天气"→"查一下庭。"）；修复：`src/brain/voice/asr.py` `_run_sherpa` 降采样换窗口 sinc；配套验证脚本 `data/logs/verify_asr_fix.py` |
| v1.5 | 2026-10-29 | 新增 L23 天气直达路由命中但 wttr.in 瞬时网络超时→静默 40s；修复：weather.py 重试一次 + interaction.py 天气失败快速降级话术（不再干等 14B） |

### L24 daemon 重启后 KWS 唤醒失灵——USB 麦克风设备/驱动层不送有效信号（硬件/系统层，非代码回归）
> **【已修订 · v1.7】本条目根因结论被推翻，以 L25 为准**。用户实机反馈"我现在就是用这个麦克风跟你说话"（豆包语音识别正常）+ 双路径说话探针（MME/WASAPI 同时采到 peak≈0.034 正常语音）+ 在线复刻全链命中「贾维斯」（t=17.5s）共同证明：麦克风硬件、驱动、系统设置、采集路径、KWS 处理链全部正常；真正的坏件是 21:22 重启的 daemon 旧实例的 MME 句柄（23:00:24 PortAudioError -9999 [MME error 6] 后半死：读静音、CPU 满载空转、间歇性恢复后再次失效）。L24 当时在"用户未开口"的测试盲点下采样（探针未提示用户说话），误将 MME 句柄失效归因为硬件层。修订保留原记录，结论以 L25 为准。
- **现象**：2026-10-29 21:22 重启 daemon（锁 38132）后，21:22:37 起环境电平持续 peak=0.0000（数字静音），21:23~21:45 用户 7+ 次喊"贾维斯"全部"kws 强信号未命中"（ring 多数仅末块有能量 0.01~0.05；21:38:00 曾连续 5 块 0.0024~0.0222 仍 miss）；用户感知"进程崩了、系统把进程都中断退出了"。实测 38132 一直存活（21:22 启动、22:09 仍在写日志），并非进程被终止。
- **根因**：**USB 麦克风（惠普 USBAudio2.0，VID_4C4A&PID_4155）在设备/驱动/物理层不送有效信号**。决定性取证：①WASAPI 48k/2ch 直开 USBAudio2.0 录 4s = 40 块全 peak=0.00000（非零仅 44/384000，真数字静音）；②MME 44.1k/1ch（daemon 同款打开方式）录 4s = peak=0.000061 rms=0.000015（正常说话 peak≈0.03 的约 1/500）；③pycaw 系统级：USBAudio2.0 静音=False 音量=100%、Steam Streaming Microphone 静音=False 音量=53.7%；④隐私权限 HKCU+HKLM 均 Allow；⑤PnP 设备状态 OK、录音端点 DeviceState=Active、Properties 无 FxProperties/APO。系统录音音量/静音/隐私/设备枚举全部正常，但两条采集路径（WASAPI 原生 + MME 共享）都只收到近数字静音 ⇒ 非系统音量设置问题，指向设备/驱动/物理层（物理静音开关误触、USB 线缆/接头松动、硬件故障、或音频服务级独占降位）。
- **关键判据（排除代码回归）**：daemon（20:48:35）/asr（21:04:37）代码在成功实例（21:07 命中）与失败实例（21:22 后全 miss）间零改动；离线复测（probe_kws_recheck.py）用当前 sinc 链路对含唤醒词的 19:36 样本双阈值均命中。
- **规避**：语音链路"整体失灵 + 环境电平数字静音"时，先按 系统音量→静音→隐私→PnP→采集实测（WASAPI/MME 双路径） 顺序排查，**不要改 KWS/ASR 参数**；代码层与 21:22 重启前一致且离线复测命中 ⇒ 改参数无意义。恢复手段需用户物理配合：检查麦克风物理静音开关、重插 USB/换口/换线、Windows 音频服务（audiosrv）重启、或切换替代输入设备（Steam Streaming Microphone 等）。
- **复发**：0（首登记）

### L25 daemon 旧实例 MME 句柄半死致唤醒失灵——探针盲点误判硬件，重启换句柄即恢复（正确根因，修订 L24）
- **现象**：21:22 重启的 daemon（锁 38132）在 21:23~22:50 采到强信号却全部"kws 强信号未命中"（peak 0.0058~0.0502，含 21:38 连续 5 块真实语音 0.0024~0.0222）；23:00:24 PortAudioError -9999 `[MME error 6]` 后 InputStream 读静音（23:01~23:32 环境电平恒 0.0000，用户 23:30 说话无任何记录）；38132 CPU=7917s≈全程单核满载（read 立即返回空→主循环极速空转）。用户感知"进程崩了"。
- **决定性新证据（推翻 L24 硬件定论）**：①用户实机反馈"我现在就是用这个麦克风跟你说话"（豆包语音识别正常）；②双路径说话探针（probe_speak_confirm.py，用户配合开口）：**MME idx1 44.1k 与 WASAPI idx30 48k 同时采到正常语音 peak_max≈0.034/0.034**（此前所有"静音"探针均未提示用户说话，属测试方法盲点）；③在线复刻全链（probe_online_replica.py，完全复刻 daemon 处理链：MME 44.1k→sinc→增益→分块喂同一 sherpa spotter，threshold=0.04）：**t=17.5s 命中「贾维斯」peak=0.0020 gain=28.7 active=4/5**；④全日志核对：20:49 启动的旧 daemon 在 21:00:05/21:07:25 均正常命中（0.0076/0.0281），失灵集中在 21:22 重启后的第二代。
- **根因**：非硬件、非代码、非参数——**daemon 旧实例的 MME 采集句柄在驱动级异常（MME error 6）后半死**：读静音或返回损坏数据，KWS 无法解码；主循环因 read 不阻塞而满载空转。同代码、同参数、同设备的新进程（在线复刻探针）17.5s 命中 ⇒ 处理链本身完好，坏的是旧实例持有的音频句柄。
- **修复（已执行并真机验证）**：停止旧实例（38132/30068）→ 用 venv-asr python -X utf8 + stderr 重定向重启（launcher pid=15248 → 真解释器 pid=28600，锁=28600）→ **00:06:55 新 daemon 真机命中「贾维斯」active=5/5 → 00:07:02 采集指令 → 00:07:09 ASR"查一下江海天气。" → 天气查询 reason=天气查询 reply="沈阳现在晴…" TTS 已播放**。端到端闭环打通。
- **教训（方法层面）**：语音链路排障的"采集实测"探针必须**提示用户开口说话**再下结论；未确认用户是否发声的静音采样不能作为"采集路径失效/硬件故障"的证据。设备/驱动层结论（如 L24 的硬件定论）必须有用户实机发声对照才可成立。
- **遗留**：SenseVoice 将"珠海"识别为"江海/上海/武海"（城市名弱信号固有偏差，L23 遗留）本次复现（"查一下江海天气。"→ 未解析珠海，回退默认沈阳）；新 daemon 尚未做 CPU 占用回归验证；sinc 除零 RuntimeWarning（daemon.py:80、asr.py:182 边界 d=0 NaN 风险）未清理。
- **复发**：0（首登记）

### L26 daemon `log()` 无锁 → 双线程改造后 async-play 日志 JSONL 并发写竞态（工单 0007 T4 暴露）
- **现象**：0007 三派 T4 真机验证时 `data/logs/voice-listen.log` 第 2453 行损坏，仅余半行 `ress\\reply-338.wav"}`；相邻 2452（"输出设备解析"）与 2455（"played: …reply-338.wav"）完整。Codex 探针无法把该损坏行当作有效 `async-play` 首字时间戳。
- **根因**：`voice-listen-daemon.py` 第 87-90 行 `def log()` 用 `with open(LOG, "a")` 无任何全局锁；单线程时代每次调用单句原子追加（安全）。工单 0007 T1 引入识别线程后，主线程（async-play/round 事件）与播放线程/识别线程并发 open-append-close 同一文件，两条 write 在同一 offset 交错 → 半行覆盖。属**线程安全缺陷**，由双线程改造暴露（工作树版本才存在；运行中旧 PID 22844 单线程不受影响）。
- **规避/修复方向**：`log()` 加进程内 `threading.Lock`（或单写者队列），T4 时间戳提取对损坏行做防御性解析。修复并进 0007 冻结门统一落地（红线：运行中 daemon 未停未重启，工作树改动冻结后一并生效）。
- **复发**：0（首登记）

### L27 回放端点音量残留 6.3% → "播放成功但物理无声"（运维/工具链）
- **现象**：0007 五派修复重测中，响亮 1kHz 测试音（0.5 幅）经 MME idx4（POISON 耳机）播放，daemon 环境电平恒 0.0000、双端点对照（WASAPI idx30 + MME idx1）均只采到底噪（peak 0.0002-0.0005），一度判定"回放物理无声"。恢复端点音量后 daemon 即采到强信号（peak 0.0139-0.0625，17:50）。
- **根因**：Windows 输出端点"耳机 (POISON M@LOFREE)"主音量=6.3%（pycaw 实测 vol=0.063 mute=False）——第四派曾调 6.3%→12%→20% 但只动了探针侧 gain/未持久，Windows 端点实际仍 6.3%。sounddevice 播放不报错（PortAudio 不管 Windows 端音量），播放"成功"但物理声极弱。0.5 幅测试音 × 0.063 ≈ 0.03 弱声 + 密闭耳机漏音不足 → 麦收不到。
- **规避**：排查"播放成功但采集全静音"时必须先查**输出端点**的 Windows 主音量/静音（pycaw：`dev._dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL).GetMasterVolumeLevelScalar()`），再查输入端点；端音量残留是"物理无声"的第一嫌疑。探针定型：`tools/probe-endpoint-volume4.py`（pycaw 全端点音量/静音 + 恢复）。
- **复发**：0（首登记）

### L29 KWS 真机命中需「唤醒词后静音确认窗」+ speech 阶段 KWS 暂停互斥（#136 验收期）
- **现象**：① 12s CV3 长句整句连读，离线 KWS 命中（hits=["贾维斯"]），真机 3 次播放持续强信号（peak 0.13-0.27）零命中；改 MeloTTS 7.87s 紧凑版仍零命中。② 长指令播放（18:43:53-18:44:25）落在上一轮 speech round（18:43:26→18:44:49 elapsed 82.81s）内，daemon 单线程 speech 阶段 KWS 监听暂停，播放声无人听。
- **根因**：① KWS 流式解码在唤醒词后需静音间隙确认（命中日志 peak 恒为语音结束后的静音块）；整句连读无确认点 → 不输出命中。② daemon 主循环单线程：命中→采集→speech（Agent 回答+TTS+async-play 播放）期间 KWS 不监听。
- **规避**：① 长指令夹具构造=已验证短音频前段唤醒词（1.6s）+ ≥0.8s 静音 + 指令正文（TTS 合成）拼接，总 9.39s → 真机 3/4 命中（首字 +4s）；1 次偶发未命中为 #133 score=2.0 已知现象。② 批量回放须按 speech 周期（~90s）排队，避开 speech/async-play 窗口（probe-t4-queue.py / probe-t4-long3.py）。
- **复发**：1（L27/L28 同类物理耦合链；本条为内容与时序层新增根因）

### L28 密闭耳机与 USB 麦无物理声学耦合 → T4 物理布置需操作者固定回放单元（硬件/物理层）
- **现象**：POISON 输出端点音量恢复 100% 后，0.4 幅测试音播放仍只采到 0.00029（WASAPI30）；换 AG273 显示器（NVIDIA HDMI，电竞显示器无喇叭）播 0.00008 仍无声；daemon 却能采到环境强信号 0.0139-0.0625（采集链路活）。播放唤醒词 3 次 daemon 恒 0.0000。
- **根因**：密闭式耳机播放声被耳罩吸收/定向，与 USB 麦之间无直达声路径；机器无可用外放单元（显示器无喇叭、SPDIF 无音箱、Steam 虚拟输出）。物理耦合（回放单元→麦 3-5cm 直达声）无法软件建立，是 T4 标定的硬前置。
- **规避**：T4 物理耦合布置必须由操作者把回放单元（POISON 耳机或任一可外放设备）固定到 USB 麦（麦克风 USBAudio2.0，WASAPI idx30 / MME idx1）正前方 3-5cm；软件侧先恢复端音量 + 重启 daemon，用"强信号未命中/命中"日志判采集链路活，再播唤醒词判耦合达标（门控块峰值 0.01）。
- **复发**：0（首登记）

### L30 声音链路一致性：KWS 提示音与 TTS 音色必须同源；完整链路冷启动需预热（2026-10-30 真机反馈）
- **现象**：真机两轮实测（19:40/19:41，reply-346/347）唤醒/识别/意图/回复全对，但：① 用户听感"KWS 提示音是以前的女声，TTS 回复是新合成的贾维斯克隆声，两者不一致"；② 用户觉得 CV3 克隆音"怪异"，要求把声音换回去；③ 重启后首轮 elapsed=68.19s（全链路冷启动）、热机 18.17s，体感"答应了却没动静"。
- **根因**：① 声音归因（采样率取证）：KWS 提示音 wake-prompt.wav=44100Hz（MeloTTS 女声，与 10/26-10/27 历史 reply 224/241/242 同源）；当前 TTS 配置 engine=cv3 使 CV3 克隆声（24000Hz）永优先，与提示音音色不同源 → 听感断裂。② warmup() 只预热 ASR（5.9s），Agent 14B 首 token 与 TTS daemon 均冷启动 → 首轮 68s。
- **修复（已执行并验证）**：① `voice-profile.json` engine cv3→sherpa，`tts.py` 增加显式本地引擎直达（sherpa/piper/edge），`voice_profile.py` 白名单扩为 {cv3,edge,sherpa,piper}；验证输出 44100Hz sherpa-melo-tts（1.07s），与 KWS 提示音同源同率。② warmup() 扩为完整链路三段：ASR（2.4s）+ Agent 8756 health+ask 预热（31.9s，首 token 加载）+ TTS 按 engine 预热（37.8s 累计），监听 20:01:43 恢复。**注意：agent_server 端口为 8756（agent_client.py L16），勿探 8080**。
- **教训**：① 音色变更必须全链路同步（提示音+回复同一引擎/采样率），冻结音色前先真机听感验证，避免"技术正确但用户觉得怪异"；② 用户否决冻结音色（CV3）= 推翻 0005 frozen 决策，换回旧女声，属基线变更需回填报告。
- **遗留**：换回 sherpa 后仍需真机复测确认延迟与听感；0005 CV3 冻结状态待 Owner 裁定（保留可用但非默认）。
- **复发**：0（首登记）

### L31 长回复"后半段断续"根因=播放走 MME 与采集同 hostapi 并发欠载；输出改 WASAPI 解耦（2026-10-30 真机反馈）
- **现象**：用户真机反馈「喊了两遍才应（第二遍回复）→ 查天气时说的前半段正常、后半段断断续续」（20:26:53 强信号未命中 peak=0.0504 → 20:26:58 命中 active=3/5 → 20:27:03 final "查天气信。" → 20:27:06 reply="沈阳现在多云，气温8度，体感5度，北风19公里每小时。" → async-play reply-349.wav → 20:27:07 KWS 采集重新打开 → 20:27:11 played）。
- **取证**：① reply-349.wav=44100Hz/单声道/4.45s，50ms 块能量连续、停顿全部落在句内逗号处；10ms 全零仅 1.08-1.11/1.81-1.82/2.74-2.76s，弱块特征与 Melo 时代旧回复 reply-40/42/77/85（同为 44100Hz）一致 ⇒ **合成音频健康、无丢帧**。② 设备表（tools/_dev_list.py）：MME POISON 耳机=idx4(44100)、DirectSound=idx15、WASAPI POISON=idx24(44100)、WASAPI 默认输出=24；系统默认输出=4(MME POISON)。daemon `resolve_out_device()` 按设备枚举顺序名字匹配 → 命中 **MME idx=4**（播放与 KWS 采集 MME idx1 **同 hostapi**）。③ 播放实现 `play_wav()`=sounddevice `sd.play()+sd.wait()` 阻塞式（后台线程 `_play_safe`），播放期间（20:27:07）主循环已回到 wait_wakeup 重新打开 KWS 采集流。
- **根因**：播放线程与采集线程在 **MME 同一驱动栈上并发**（输入流 idx1 + 输出流 idx4），采集满负荷读时 MME 输出缓冲欠载 → 长回复后半段断续；短提示音（~1s）来不及显现，长回复（4.45s）后半段累积欠载。
- **修复（已执行并验证）**：`resolve_out_device()` 改为**优先 WASAPI 输出**（idx24 POISON 44100Hz，与 MME 输入流不同驱动栈解耦），回退链 = WASAPI POISON → 任意 hostapi POISON → 系统默认。验证脚本（tools/_outdev_verify.py）真实设备表返回 idx=24 WASAPI 44100。daemon 第 5 次重启（PID 27164，20:35:00 监听恢复，warmup 三段完成 asr 5.8s/agent 32.7s/tts 41.4s）。
- **基线勘误**：**PLAY_DEVICE=26 已漂移**——当前 idx=26 为 WASAPI "扬声器 (Steam Streaming Microphone)" 48000Hz（名字与 POISON 无关），WASAPI 下 POISON 耳机实为 **idx=24（44100Hz）**；daemon 名字优先规则命中 idx4 是 MME 枚举，而非基线 WASAPI 26。
- **遗留**：① 若 WASAPI 播放后仍断续，下一步排查方向=播放期间暂停 KWS 采集（互斥）或播放改常驻 OutputStream 减少流创建开销；② "唤醒两遍才应"本次复现（20:26:53 peak=0.0504 未命中→第二遍命中）= #133 score=2.0 已知间歇现象，用户在真机多次遇到，待根治方案。
- **复发**：0（首登记）

### L32 第二轮真机「渐弱→杂音→无声」：端点音量残留 31.5% + 播放/采集并发未根除，播放期暂停采集收口（2026-10-30）
- **现象**：用户复测「喊一遍即应✅（20:38:46 命中 active=4/5）→ 问现在几点 → 回复前半句正常、随后声音越来越小→变杂音→最后无声音」。round：20:38:50 ASR final="现在几点了？" → 20:38:53 reply="请允许我查看一下当前时间。\n现在是北京时间下午两点整，先生。"（pushed_seq=350）→ async-play reply-350.wav（idx=24 WASAPI 44100）→ 20:38:54 KWS 采集重开 → 20:38:59 played。
- **取证**：① reply-350.wav（44100Hz/5.24s）50ms 块能量连续、无丢帧、无整体衰减（RMS 前 4912/中 4021/后 3342 属正常尾音，2.25-2.45s=换行停顿）→ **合成健康，问题在播放层**；② **POISON 输出端点音量=0.315（31.5%），非 100%**（pycaw probe-endpoint-volume4 实测）——上次 L27 恢复 100% 后再次被拉低，"声音越来越小"最直接解释；③ 播放期间（20:38:53-59）KWS 采集流仍在 MME idx1 满负荷读（20:38:54 重开），虽输出已切 WASAPI idx24 不同 hostapi，但采集线程 CPU/总线竞争仍在 → 长回复后半段 WASAPI 输出欠载。
- **修复（已执行并重启验证）**：① `probe-endpoint-volume4.py` 恢复 POISON 端点到 vol=1.0 unmuted（**已执行**）；② daemon `play_wav`/`_play_safe` 增加 **`_PLAYING` 互斥事件**：播放置位、播完 finally 清除；`wait_wakeup` 循环检测 `_PLAYING.is_set()` 时 sleep(0.05) 跳过采集 read → **播放期间完全暂停 KWS 采集，输入/输出零并发**。daemon 第 6 次重启（launcher 2464→本体，20:44:15 启动、20:45:15 监听恢复，warmup asr 6.0s/agent 35.7s/tts 44.9s）。收口断言：播放期日志应出现 `KWS 采集打开` 只发生在播放结束后（非 20:38:53-59 期间）。
- **代价**：播放期间（≤6s）KWS 不监听、不可唤醒；用户正在听回复，可接受；播完立即恢复唤醒。
- **遗留**：① 端音量被拉低的原因未定位（Windows 应用/系统策略？），需观察是否再次漂移；② 唤醒两遍（#133 score=2.0）仍为已知间歇项；③ 若播放期互斥后仍出现杂音，下一步=WASAPI OutputStream 常驻化 + 显式 blocksize。
- **复发**：1（L31 首登记，本条为同根因第二轮：WASAPI 解耦后未根除，追加互斥）

### L33 第三波三连问题收窄：ASR 近音误识进归一化映射 + 征询误触发三重收窄（2026-10-30 真机反馈）
- **现象**：用户三连抱怨「①KWS 触发不灵敏、②ASR 解析不清晰、③回答内容不精准」。逐层取证定位：22:14 轮 ASR final 完全正确（"给我看一下明天上海的天气怎么样。"），但 round reason="征询中"、reply 把上一轮 21:07 遗留的"水量天听"套进征询模板播给用户 → "回答内容不精准"= 征询误触发 + 跨轮引用旧文本两因素叠加；"水量天听"溯源=21:07 轮 intermediate"查一下明天的水平听听清"→ final"查一下明天的水量天听。"（"天气"近音误识），被 14B Agent 兜底原样引用。
- **根因**：① `_CONSULT_INTENT = r"(?:你觉得怎么样|怎么样|如何|行不行|行吗|OK吗|可以吗|感觉如何|是否满意)"` 含"怎么样"，天气句"…天气怎么样"在天气直达（原 5.5 步）**之前**先被 `_CONSULT_INTENT` 命中 → `_on_consult` 把遗留 last_summary（"水量天听"）套进征询话术输出；② idle 态纯征询/确认短句（"你觉得怎么样"）在去掉 phase 前置后漏到 6 步 `_try_agent_fallback` 14B 兜底 → 自由发挥答非所问；③ ASR 近音乱词（水量天听/水平听听清）无入口拦截，直接进 Agent 被引用。
- **修复（已执行并验证）**：interaction.py 四处收窄——① 天气直达整体前移至 handle() 1.4 步（调整指令之后、子智能体/征询/确认之前）；② `_CONFIRM_INTENT`/`_CONSULT_INTENT` 拦截加 `and self.phase == _PENDING_CONFIRM`（仅待确认态拦截）；③ 新增 2b：非待确认态命中征询/确认且不含查询动作词（`_QUERY_ACTION_RE`=查/看/问/天气/任务/队列/进度/状态/多少/什么/哪/时间/安排/计划）的纯短句提前静默返回"无待确认结果"（防漏 14B 兜底）；④ `_normalize_utterance` 新增 `_ASR_NEAR_HOMOPHONE` 近音映射（水量天听→天气、水平听听清→天气、水平听→天气、明天上海的这→明天上海的天气）。
- **验证**：回归探针 `tools/_regress_int.py`（ProbeLoop 子类，phase 必须用真实常量 `_IDLE`/`_PENDING_CONFIRM`=idle/pending_confirm，不能用字符串字面量否则 phase 判断全落空）5 例全绿：22:14 复现→天气查询（不再征询）、normalize(21:07)="查一下明天的天气"、纯征询待确认态→征询中、天气句 idle→天气查询、确认→确认通过；pytest `test_interaction.py`+`test_interaction_orb.py` **28 passed**（原失败用例 test_consult_without_result_stays_idle 恢复绿：idle 态"你觉得怎么样"应静默 assertFalse(r.handled)）。daemon 第 7 次重启（launcher 39400→本体 23728，22:37:34 监听恢复，warmup asr 4.2s/agent 11.0s/tts 18.5s）。
- **教训**：① 意图正则含泛词（"怎么样"）必须排在精确意图（天气直达）之后，否则吞掉真实查询；② 征询/确认闭环词只能在其状态机语境（待确认态）生效，跨态应静默而非落 LLM 兜底——LLM 兜底是"最后手段"，不是"所有未匹配句的垃圾桶"；③ ASR 近音误识要入口拦截（归一化映射），不能指望 14B 自纠，它会原样引用乱词。④ 探针/测试里 phase 常量必须与产品代码共用同一常量对象，字符串字面量会静默破坏所有 phase 分支判断。
- **遗留**：① KWS 漏唤醒（#133 score=2.0）仍为已知间歇项，基线冻结，待专项 A/B（threshold=0.08/score=2.0 不擅动）；② last_summary 跨轮残留收敛（非待确认输入时清空/每轮覆盖）未实现，2b 已挡大部分误征询，但"上轮结果后直接问新问题"仍可能翻旧结果，下一轮治理项；③ 端音量漂移复发观察中。
- **复发**：0（首登记）

## 变更日志

| 版本 | 日期 | 变更 |
|---|---|---|
| v2.3 | 2026-10-30 | 新增 L33 第三波三连问题收窄：②ASR 近音误识（水量天听/水平听听清→天气，_normalize_utterance 近音映射）+ ③征询误触发（_CONSULT_INTENT 含"怎么样"先于天气直达拦截 → 天气直达前移 1.4 + 征询/确认仅待确认态拦截 + 纯征询/确认短句非待确认态静默 2b 防漏 14B 兜底自由发挥）；探针 5 例全绿 + 单测 28 全绿；daemon 第 7 次重启（22:37:34 监听恢复） |
| v2.2 | 2026-10-30 | 新增 L32 第二轮真机渐弱/杂音/无声：POISON 端点音量残留 31.5%（probe 恢复 1.0）+ 播放/采集并发未根除 → daemon 增加 _PLAYING 互斥（播放期暂停 KWS 采集），第 6 次重启 PID 2464 监听 20:45:15 恢复 |
| v2.1 | 2026-10-30 | 新增 L31 长回复后半段断续根因（MME 播放与采集同 hostapi 并发欠载）+ 修复（输出解析改优先 WASAPI idx24 解耦）+ 基线勘误（PLAY_DEVICE=26 漂移→WASAPI POISON 实为 idx24 44100）；daemon 第 5 次重启 PID 27164 |
| v2.0 | 2026-10-30 | 新增 L30 声音链路一致性（KWS 提示音与 TTS 音色同源）+ 完整链路三段预热（ASR/Agent 8756/TTS）；engine cv3→sherpa 换回 MeloTTS 44100Hz 女声（用户否决 CV3 克隆音"怪异"）；agent_server 端口勘误 8756 |
| v1.7 | 2026-10-30 | L24 根因修订：用户实机发声对照 + 双路径探针（MME/WASAPI 同采 peak≈0.034）+ 在线复刻全链命中（t=17.5s）推翻"硬件不送信号"定论；新增 L25 正确根因=daemon 旧实例 MME 句柄驱动级半死（MME error 6 后读静音、CPU 满载空转）；修复=重启换句柄并真机验证（00:06:55 命中贾维斯→00:07:09 天气查询+TTS）；教训=采集实测探针必须提示用户开口，未发声静音采样不能作硬件故障证据；配套报告第九节 |
| v1.8 | 2026-10-30 | 新增 L27 回放端点音量残留 6.3%→"播放成功但物理无声"（pycaw 实测 vol=0.063，恢复 100% 后 daemon 采到强信号 0.0139）；新增 L28 密闭耳机与 USB 麦无物理声学耦合→T4 物理布置需操作者固定回放单元（唯一人工前置）；配套证据 `a3-output-endpoint-forensic.md` |
| v1.9 | 2026-10-30 | 新增 L29 KWS 真机命中需「唤醒词后静音确认窗」（长指令夹具 0.8s 静音拼接）+ speech 阶段 KWS 暂停互斥（批量回放按 90s 排队）；#136 验收 PASS，证据 `a4-kws-rootcause.md` |

## L34 Codex 派发 stdin 中文编码（2026-10-31 · 0008 十一次重派）

- **现象**：Codex 派发脚本经 .NET StandardInput 写中文载荷 → codex 报 `Failed to read prompt from stdin: input is not valid UTF-8 (invalid byte at offset 36)`，exit=1 启动即失败（PID 28420）。
- **根因**：载荷文件本身是合法 UTF-8（无 BOM、严格解码 OK），但 `StandardInput.Write(string)` 在 Windows PowerShell 下按默认编码（GBK/cp936）把字符串转成字节写 stdin，codex 按 UTF-8 解析错位报错；中文 UTF-8 三字节序列被 GBK 单字节化后产生非法字节。
- **修复**：改用字节直写 `$p.StandardInput.BaseStream.Write([Text.Encoding]::UTF8.GetBytes($promptText), 0, len)` + Flush + Close，绕过 .NET StreamWriter 的默认编码层；修复后重派 PID 29968 启动成功并完整收 round4 回执。
- **教训**：凡向任意子进程写 stdin 且内容含非 ASCII（中文/emoji/混合），必须显式 UTF-8 字节直写 BaseStream，绝不依赖 StreamWriter/Write(string) 的隐式编码；Windows 下这是高频静默坑（PowerShell 管道、.NET 编码层、控制台代码页三处都可能改写编码）。
- **遗留**：无；重派收尾已完成（十二次重派 exit=0，round4 重筛 150 段/8.03min，用户拍板 B 方案开训，十三次重派已启动）。
- **复发**：0（首登记）

## 变更日志
| v2.4 | 2026-10-31 | 新增 L34 Codex 派发 stdin 中文编码坑（UTF-8 字节直写 BaseStream 修复，0008 十一次重派 PID 28420 exit=1 → 十二次重派 PID 29968 exit=0） |
| v2.5 | 2026-11-01 | 新增 L35 agent_server 8756 "查新闻" 500 根因链（旧进程未加载 0016/0017 + Qwen3 thinking 空 content + you.com 不可达吞 fallback；修复=启动脚本注入 OPENJARVIS_WEB_SEARCH_ENGINE=duckduckgo + 重启，实测 200 grounded=true） |
| v2.6 | 2026-11-04 | 新增 L36 kws_listener.py 参数与权威基线漂移（score=1.0/num_trailing_blanks=0 vs 基线 2.0/8）+ 基线文档"产品主入口"声明与实测运行入口（daemon）不一致 |
| v2.7 | 2026-11-05 | 新增 L37 T4 全量回归两项环境既有失败（测试子进程 PATH 缺 Ollama 目录 + jarvis ask 14B 真实推理在 12GB 卡 cudaMalloc OOM）；处置=主脑豁免裁决收口 + 两项登记环境债（测试环境注入 PATH / 真推理测试改 8B 或加显存前置） |
| v2.8 | 2026-11-06 | 新增 L39-L42 抖音热榜视频提取四坑（纯 HTTP 返回空壳 / 详情页跳精选页但 SSR 数据可直读 / SSR 分片是 JSON 字符串字面量必先解码 / CDN 直链需 Referer 且签名有时效）；配套链路 `H:\UltimaAI\_shared\tools\scrapling-test\`（hot_fetch.py + hot_video.py + 播放页模板） |
| v2.9 | 2026-11-06 | 新增 L43 Windows 桌面自动化四处系统级限制（USER_CONTROL 控制权让路需重试 / SetForegroundWindow 前台锁定 / UI 树 500 元素上限 / 13 窗口 UIA 读不出 + README 门控参数在本机不存在）；配套配置文档 `docs/specs/windows-mcp-executor-channel.md`，能力清单「执行」组新增「操作桌面窗口和按钮」 |
| v3.0 | 2026-11-06 | 新增 L44 git 推送"代理连不上"假象（github.com 单独配 1083 失效端口，全局 1080 正常）；处置=单次 `-c` 覆盖到 7897 推分支与标签，`ls-remote` 带同覆盖回读确认 `6b433698` 已在远端 |

## L35 agent_server 8756 "查新闻" 500 根因链（2026-11-01 · 实测修复）

- **现象**：`POST /ask {"query":"查一下今天的新浪新闻"}` 返回 500；agent-server.log 尾部 `Requested engine '"'"'ollama'"'"' is unavailable; no substitute was selected`。
- **根因链（三层）**：
  1. **8756 进程跑旧代码**：PID 15504 为 10-31 13:56 启动，未加载 0016/0017（路由门/结构化回复）→ 旧链路异常。
  2. **Qwen3 thinking 空 content 坑**：Qwen3 系列默认开启 extended thinking，`num_predict` 配额被思考 token 全部消耗，`message.content` 返回空（done_reason=length）。openjarvis OllamaEngine 已默认 `think=False`（源码注释明确此坑），新代码链路不受影响；直接测 ollama chat 需显式 `think:false`。
  3. **ultima_web_search 30s 硬超时吞 fallback**：首选引擎 you.com API 本机不可达（`WinError 10060` 连接超时挂起），30s 工具执行上限在 fallback 到 DuckDuckGo 之前就掐掉请求。单测证明 you.com→DDG fallback 本身可用（返回真实来源 URL）。
- **修复**：`scripts/start-agent-server.ps1` Start-Process 前注入 `$env:OPENJARVIS_WEB_SEARCH_ENGINE = "duckduckgo"`（本机实测 200 可达），重启 agent_server 加载新代码。
- **验证**：`POST /ask "查一下今天的新浪新闻"` → 200；路由门 ALLOW（"查一下"命中）→ 8B 决策调用 ultima_web_search → DDG 返回 5 条真实新浪来源 → 0017 结构化回复 `grounded=true`、`confidence=0.9`、≤2 句无营销，`structured_degraded=false`。
- **教训**：① 进程重启前先核对启动时间，旧进程排障是浪费轮次；② 外部 API 首选引擎不可达时，检查工具级硬超时是否会吞掉内置 fallback；③ 改引擎走环境变量注入启动脚本（项目内可回退），不直接改 venv 库。
- **遗留**：无。
- **复发**：0（首登记）

## L36 kws_listener.py 参数与权威基线漂移 + 文档-运行入口不一致（2026-11-04 · 0023 T3 绑定证据实测）

- **现象**：0023（Jarvis P0）T3 绑定证据未闭合——执行端回执"产品入口仍 score=1.0/trailing=0 vs 权威回放 2.0/8"。
- **实测**：`src/brain/voice/kws_listener.py` L62/L64 = `keywords_score=1.0`、`num_trailing_blanks=0`；`docs/specs/kws-wakeup-params-baseline.md` 权威 = `score=2.0` / `trailing=8`（2026-10-30 #133 落地值）；`KWS_THRESHOLD=0.08` 已对齐。运行中语音进程= `data/logs/voice-listen-daemon.py`（PID 24812/24276，venv-asr，创建 11-03 17:38:54）——非 kws_listener。
- **根因**：10-30 基线更新（score 2.0/8）主要落在 daemon 实现；kws_listener.py 参数未同步更新，形成历史漂移；且基线文档声明"适用入口 kws_listener.py（产品主入口）"，与实测运行入口（daemon）不一致——文档声明 ≠ 运行时事实。
- **教训**：① 权威基线文档更新后，必须把每个实现入口（daemon / kws_listener）与基线逐项 diff，只改一处=漂移温床；② "产品主入口"类声明需与实际运行进程核对后再采信；③ 验收前把权威基线与全部实现入口逐项核对，不能只信文档汇总。
- **处置**：0023 主脑裁决授权有界修复——kws_listener.py 回正 `score=2.0/num_trailing_blanks=8`（消除漂移=回正冻结值，非新调参；不影响运行中 daemon）。
- **遗留**：北极星清单 kws 行、voice-profile 相关文档如需同步入口声明时另行核对。
- **复发**：1（首登记）

## L37 T4 全量回归两项环境既有失败（Ollama PATH + 14B 显存容量）（2026-11-04 · 0023 修复轮实测）

- **现象**：0023 修复轮（PID 21280，run 20261104T141335097160Z）T4 全树 `tools/venv-openjarvis/Scripts/python.exe -m pytest src -q` exit=1：`979 passed, 2 failed, 120 subtests passed`（junit `data/evidence/jarvis-p0/T4/full-green4-junit.xml`）。失败1 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains`：`FileNotFoundError: [WinError 2]`——测试子进程 PATH 不含 Ollama 安装目录；失败2 `TestC2Entry::test_jarvis_ask_real_inference`：`jarvis ask` exit 1，Ollama HTTP 500、llama-server `cudaMalloc failed: out of memory`（KV cache 申请 2,818,572,288 字节；qwen2.5:14b ~9GB + KV + 开销 > 启动时可用 10,453 MiB）。
- **首轮对照（定性关键）**：同两个测试在首轮 `T4/full-green3-junit.xml` 中均无 failure 标签（`test_ollama_has_brains` time=0.062、`test_jarvis_ask_real_inference` time=24.418，即 PASS）→ 修复轮代码仅改 kws_listener 参数回正 + P0-3 接线，与两项连通性测试零交叉 → 判为环境差异/波动，非本单回归。
- **根因**：① 测试依赖调用者 shell 的 PATH，未自带 Ollama 目录注入（执行端进程内 PATH 修正后 `ollama list` exit 0，但该修正未落到 pytest 子进程）；② `test_jarvis_ask_real_inference` 以 qwen2.5:14b 真实推理为断言对象，14B（9GB+2.8GB KV）超出 12GB 卡可用显存（当前实测 free 9,116 MiB，需求 ~11.8GB；用户 11-02 已裁定 14B 仅留库、不作运行候选，backend 默认 `memory_llm_model=qwen2.5:14b` 为历史遗留）。
- **处置**：主脑 2026-11-05 裁决 T4 按"环境既有失败豁免"收口，裁决另档 `data/evidence/jarvis-p0/T4/main-brain-exemption-ruling.json`；执行端 BLOCKED 守门记录保留不改（gate/回执原判留痕）。两项登记环境债：DEBT-ENV-01 测试环境 PATH 注入 Ollama 目录（或测试内自备）；DEBT-ENV-02 真推理测试改 8B 或按显存容量前置跳过（另立专项单，不占 0023 额度）。
- **教训**：① 全量回归红色用例必须与首轮同用例逐项对照定性，同测试首轮 PASS 是"环境波动非回归"的直接证据；② 12GB 卡上 14B 不得作为任何自动化测试的真实推理对象（模型策略=8B 唯一运行候选）；③ 测试依赖外部进程（Ollama/PATH）时须自带环境准备，禁止依赖调用者 shell 环境。
- **遗留**：DEBT-ENV-01/02 待专项单闭环；Owner 真实体验仍为延期验收项。
- **复发**：0（首登记）

## L38 派发前置检查漏判 Codex 桌面 App 会话内的执行端（2026-11-05 · 0024 派发后撤回）

- **现象**：2026-11-05 12:52 派发 0024（pid 34552）前，前置检查判定"无本项目在跑的 codex/python 派发进程"；但同项目 0021 的 R30 恢复轮当时正在真实推进（12:21 拉起 voice-next 监听、12:54 改 controller、12:56 写验证脚本、13:01 跑 package-tests），形成同项目 2 个执行端并行，违反"每项目执行中 ≤1"。
- **根因**：前置检查只按 `codex.exe` 进程名 + 命令行过滤；0021 的 R30 跑在 Codex 桌面 App 的 app-server 会话内（PID 23116），不产生独立 `codex.exe exec` 进程，因此进程名过滤天然看不见它；同时主表 0021 仍标 blocked，状态口径也未暴露"实况在跑"。
- **处置**：13:00 主脑主动 `taskkill /PID 34552 /T /F` 撤回 0024（日志已 931KB、M1–M5 实施计划草案保留在 run 目录，`dispatch.err.log` 无错误）；主表 0021 改 executing（写明 R30 授权恢复轮）、0024 改 blocked（待 0021 收口后重派）；北极星与 0024 卡同步，commit `cec8244b` 已推远端 main。
- **教训**：① 派发前置检查不能只看进程名，必须叠加"证据目录/工作树近 N 分钟写盘"信号（本例 0021 在写 `data/evidence/jarvis-work-capability/T2/e03-source12-20261105-r30-*`）；② 主表 blocked 不等于实况没跑，授权恢复轮期间应先把主表改 executing；③ 用户在 App 里手动发起的执行端与派发器拉起的是两套形态，WIP 计数要按"实际在写盘的工作"而不是按进程名。
- **遗留**：前置检查脚本（dispatch 前置探针）待补"活跃写盘"判定项；0024 待 0021 收口后按 WIP 重派。
- **复发**：0（首登记）

## L39 抖音热榜纯 HTTP 抓取返回 200 但正文是空壳（工具链/静默失败 · 2026-11-06）

- **现象**：`scrapling extract get https://www.douyin.com/hot` 返回 200，HTML 落地 72,911 字节，但 `<body>` 为空，只剩 `_$jsvmprt` 开头的 JS 挑战脚本，Markdown 产物 0 字节。抓取命令"成功"，数据一条没有。
- **根因**：抖音用 JS 挑战拦截无浏览器执行环境的请求，HTTP 层伪装 TLS 指纹过不去；状态码和文件大小都不能证明拿到了正文。
- **规避**：热榜必须走浏览器渲染模式（`extract fetch` + `--disable-resources` + `--wait-selector 'a[href^="/hot/"]'`），实测 5.1 秒拿到 97 万字节完整页面；抓完必须校验正文含榜单条目（`/hot/` 链接数 > 0），不能只看 exit code 和文件大小。
- **复发**：1（本会话首次实测即踩中）

## L40 热榜条目详情页在浏览器里跳精选页弹窗，改读 SSR 数据可绕过（工具链 · 2026-11-06）

- **现象**：未登录浏览器打开 `https://www.douyin.com/hot/2731877/BLG战胜DK晋级半决赛` 被重定向到 `https://www.douyin.com/jingxuan?modal_id=7671977518265650478`，三次分别拿到导航壳 / 漫威解说 / 钓鱼视频，全部与榜单条目无关；而同批次的 WTT 条目却正常。同一条目后来改用 SSR 直读，一次成功。
- **根因**：未登录态下详情页有跳精选页弹窗逻辑，跳转后的 `modal_id` 与榜单条目不保证对应（成因未完全验证）；但跳转发生在 UI 呈现层，页面 HTML 本身携带的 SSR 数据仍是该话题的。
- **规避**：不要"打开页面看"，直接抓 HTML 读 SSR 里的 `hotList` 与 `video` 对象；BLG 那条改走 SSR 后标题、画面（BLG vs DK 比赛画面 + "BLG3比0横扫DK"字幕）、文件大小三项全部对上。判据：只要 SSR 里 `hotTitle` 与榜单标题一致，就说明数据这条对了。
- **复发**：1（同一坑本会话撞过三次才定位到"UI 跳转不影响 SSR 数据"）

## L41 抖音详情页 SSR 是 JSON 字符串字面量，直接搜字段名必 0 命中（工具链 · 2026-11-06）

- **现象**：在详情页 HTML 里搜 `"playAddr":[` 返回 0 命中，据此误判"页面里没有视频地址"，转而去读 `<video>` 标签，`currentSrc` 又是空，白绕一圈。
- **根因**：页面用 Next.js 风格分片 `self.__pace_f.push([1,"..."])`，每段内容是被转义后的 JSON 字符串字面量，HTML 里实际形态是 `\"playAddr\":[`；不先解码就搜原始字段名必然搜不到。
- **规避**：先用正则 `self\.__pace_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)` 取出每段字符串，逐个 `json.loads` 解码后拼接成 payload，再在 payload 里搜字段。本会话此坑踩中两次。
- **复发**：2

## L42 抖音视频 CDN 直链需 Referer 且签名有时效（工具链/外部依赖 · 2026-11-06）

- **现象**：对 `v26-web.douyinvod.com` 的视频地址做 `Range: bytes=0-1023` 请求，不带 Referer 返回 403 Forbidden；带 `Referer: https://www.douyin.com/` + Chrome UA 返回 206、`Content-Type: video/mp4`、首 8 字节 `ftyp`。
- **根因**：CDN 做来源页防盗链校验。
- **规避**：下载必须带 Referer 与桌面 Chrome UA；地址含时间戳和签名（单条 557 字符），每次从当天详情页现取，禁止硬编码复用；验证取流成功要看状态码 206 + `ftyp` 头，不只看文件非空。
- **复发**：1

## L43 Windows 桌面自动化四处系统级限制：控制权让路 / 前台锁定 / 元素上限 / 窗口读不出（工具链 · 2026-11-06）

- **现象**（Windows-MCP 0.8.8 受限实例真机验证中）：
  1. `App(mode=launch_executable)` 与后续 `Click` 返回 `{"code":"USER_CONTROL","status":{"state":"user","generation":2,"wait_seconds":9.998}}`，人在动鼠标时输入类动作直接被拒不排队，约 10 秒空闲后才放行；被拒后的快照只剩 105 字符且无 Focused Window 段。
  2. `App(mode=switch, name="计算器")` 报 `Failed to bring 计算器 to the foreground within 1 second`，底层 `pywintypes.error: (5, 'SetForegroundWindow', '拒绝访问。')`，窗口已在列表中却切不过去。
  3. 快照报 `[Tree] Capture truncated at 500 elements (limit=500)`；`region=[0,0,900,1300]` 的区域快照 UI 树被 `Thomas` 窗口元素占满，计算器按钮读不出来。
  4. 13 个窗口报 `UIA_E_ELEMENTNOTAVAILABLE (-2147220991)`，日志 `[Tree] 13 window(s) failed to capture`；重试日志还出现 `attempt 4/3` 越界计数。
  另：README 宣称的 `--no-control` / `--control-policy` / 三档 `relaxed/balanced/strict` 在本机 0.8.8 全部不存在（`serve --help` 实测）。
- **根因**：① 控制权门控是设计内的「人在用时 AI 让路」，空闲即还权，不是失败也不是排队；② Windows 前台锁定策略禁止非前台进程抢焦点；③ UI 树默认上限 500 元素（`WINDOWS_MCP_MAX_TREE_ELEMENTS`），聊天类大窗口吃光预算；④ 部分应用（Electron 类）不吐 UIA 元素；⑤ 文档版本与本机包版本脱节（服务自报 4.1.6 vs 包 0.8.8）。
- **规避**：① 调用层必须写「被拒 → 等 2 秒 → 最多重试 10 次」，全失败才判失败并上报，不能一次被拒就当任务失败；② 不依赖 `switch`，改点击目标窗口可见区域激活，或对未被遮挡的窗口直接按坐标点击；③ 调高 `WINDOWS_MCP_MAX_TREE_ELEMENTS`、配 `WINDOWS_MCP_EXCLUDE_PROCESSES` 排除干扰进程，紧急时用 `region` + `Screenshot` 按坐标点击（注意图片会缩放，坐标按 900/747 ≈ 1.204 反算）；④ UIA 超时用 `WINDOWS_MCP_UIA_CONNECTION_TIMEOUT_MS`（默认 2000）/ `WINDOWS_MCP_UIA_TRANSACTION_TIMEOUT_MS`（默认 5000），读不出的窗口一律走截图；⑤ 门控参数以本机 `serve --help` 为准，不信 README。
- **复发**：1（同会话内 ① 复现 3 次（两次点击 + 一次启动）、② 复现 1 次、④ 每轮快照都在报）

## L44 git 推送报"代理连不上"实为 github.com 单独配了失效端口（工具链 · 2026-11-06）

- **现象**：`git push origin codex/voice-fsmn-new-path` 连续两次报 `fatal: unable to access 'https://github.com/Ultima-AI-Studio/Ultima-Agent.git/': Failed to connect to github.com:443 over proxy 127.0.0.1 after 2067 ms / 2063 ms`，看起来像本机代理整体挂了。但同一时刻 `curl -x http://127.0.0.1:1080 -I https://github.com` 返回 200、`Test-NetConnection 127.0.0.1 -Port 1080` 为 True。
- **根因**：`C:/Users/Administrator/.gitconfig` 里除全局 `http.proxy=http://127.0.0.1:1080`、`https.proxy=http://127.0.0.1:1080` 之外，还有一条 `http.https://github.com.proxy=http://127.0.0.1:1083`。git 按 URL 精确匹配的代理优先级高于全局代理，于是所有 github.com 请求都走已失效的 1083 端口（同一端口用 curl 测也是 `curl: (7) Failed to connect ... after 2033 ms`）。全局代理是好的，报错文案却统一指向 `127.0.0.1`，容易误判。
- **规避**：① 遇到"代理连不上"先 `git config --list --show-origin | Select-String -Pattern 'proxy'`，分清全局代理与按 URL 的专属代理，别只看 `http.proxy`；② 用单次覆盖跑通，不改全局配置：`git -c 'http.https://github.com.proxy=http://127.0.0.1:7897' push origin <ref>`；③ 推送后用 `git ls-remote` 回读核对，且回读命令必须带同样的 `-c` 覆盖，否则 `ls-remote` 会因同一个 1083 再报一次错，被误当成"推送没成"；④ 本机实测可用端口为 1080 与 7897，1083 与 7890/7891 均不通。
- **复发**：2（分支与标签各失败一次，图案相同）

## L45 无头截图验单页动效的两个假象：虚拟时间不走 CSS 过渡 / 无头窗口有最小宽度（工具链 · 2026-11-06）

- **现象**：① 用 `msedge --headless=new --virtual-time-budget=12000 --screenshot` 截单页 HTML，元素靠 CSS `transition` 做位移时只走到半程（环停在中央偏右一点、步骤文字近乎透明），看起来像"定位规则失效 / 元素丢失"；② 加 `--run-all-compositor-stages-before-draw --disable-new-content-rendering-timeout` 后现象不变；③ 用 `--window-size=390,844` 截窄屏，图确实是 390 宽，但右侧输入栏控件被切，疑似布局溢出。
- **根因**：① `--virtual-time-budget` 只快进 `setTimeout`/定时器，CSS transition 走的是真实时钟，页面加载到截图真实只过了不到 1 秒，过渡自然停在起始段；DOM 里 `class="orb-wrap focus"` 已正确挂载，规则本身没问题；② Edge 无头窗口受系统最小窗口宽度限制，`--window-size=390` 时 `innerWidth` 实测 470，布局按 470 排，截图仍按 390 输出，于是"看起来溢出"。同一次量测：`vw:470`、`composer.right:447`、`send.right:437`，控件实际都在容器内。
- **规避**：① 验动效终止态必须走真实时钟：`--remote-debugging-port` 起无头实例，`/json` 取 page target，`ClientWebSocket` 发 `Page.captureScreenshot`，等够秒数再抓；不要用虚拟时间判断过渡结果；② 判定"是否真溢出"用 `Runtime.evaluate` 读 `innerWidth` + `getBoundingClientRect`，不靠目测截图；③ 验窄屏必须发 `Emulation.setDeviceMetricsOverride`（width/height/deviceScaleFactor/mobile）设视口，不能只靠 `--window-size`；④ 抓 page target 要按 `url -like 'file:*'` 过滤，否则可能截到 Edge 自身的同步提示页；⑤ PowerShell 里 `ClientWebSocket.SendAsync`/`ReceiveAsync` 传裸 `byte[]` 会报 "Multiple ambiguous overloads"，必须包 `[ArraySegment[byte]]`。
- **复发**：3（虚拟时间误判 2 次、窄屏误判 1 次）

## L46 Canvas 重设尺寸会清空画面，绘制循环必须与尺寸回调解耦（前端 · 2026-11-06）

- **现象**：粒子环元素用 CSS transition 从 340px 缩到 186px 并位移后，整块 canvas 一片空白；同一时刻 rAF 循环并未报错。
- **根因**：给 `canvas.width/height` 赋值会立即清空画布内容；重设发生在过渡中间，若其后没有马上补画一帧（或 rAF 恰被挂起），画面就留白。原实现把绘制与调度写在一个 `draw()` 里，递归 rAF 依赖上一帧是否执行，尺寸变化时容易断链。
- **规避**：① 拆成 `paint(ts)` 纯绘制 + `loop(ts)` 负责 `requestAnimationFrame`；② `ResizeObserver` 回调里设完 `canvas.width/height` 后立刻调一次 `paint(performance.now())` 补帧；③ `prefers-reduced-motion: reduce` 分支末尾同样补一帧，因为该分支不跑循环；④ 验收判据是"缩小后画面仍在"，不是"代码里有 resize 处理"。
- **复发**：1
## L47 卡片"从 0 展开"用 grid 行高过渡，别用 max-height；占位列表会让展开先撑满空框（前端 · 2026-11-06）

- **现象**：给右栏步骤区补"卡片淡入 + 展开"时，第一版用 `max-height:0 → 220px` 过渡，展开过程前 60% 几乎没有高度变化（先快后停），且不同内容高度要反复调数值。第二版改用 `grid-template-rows:0fr → 1fr`，展开顺滑，但卡片一展开就是最终高度（内容区一片空白），文字随后才逐条淡入，看起来像"空框先撑满"。
- **根因**：① `max-height` 过渡是线性作用于一个远大于真实高度的上限，缓动曲线被拉平；grid 的 `0fr → 1fr` 直接对真实内容高度做插值，曲线正确；② 步骤行用 `opacity:0` 隐藏但仍在文档流里占位，容器高度在展开开始时就等于"全部步骤"的高度，于是空框先到顶。这是"透明 ≠ 折叠"的必然结果。
- **规避**：① 通用展开用 `display:grid;grid-template-rows:0fr` + 内层 `min-height:0;overflow:hidden`，`open` 时 `1fr`；② 若希望容器随内容增长，占位行也必须收到 0（`max-height:0` 或折叠），不能只做透明；③ 若接受"先有框再有字"（原片就是这个节奏：卡片先张开、内容再填入），保持占位即可，但必须让第一条内容在展开完成前出现，否则空框会被看成加载失败；④ 验收要抓三个点：展开中、内容满、收起后，只看终态会漏掉中间态异常。
- **复发**：1

## L48 接口候选池的三条建模铁律：声明即契约、一池一标的、快不等于对（数据源 · 2026-11-06）

- **现象**：给常见问答做"配置表 + 自动巡检"时连续翻车三次。① `weather.today` 首选被换成 26ms 的实况接口 `sk_2d`，它没有今日最高/最低，模板填不出高低温；② 把 `dingzhi` 的 `provides` 写成了 `temperature/condition/wind/temp_range`，它靠 33ms 直接上位，实际只覆盖今天和今夜；③ 把恒生与道指放进同一个意图、把伦敦金与 COMEX 放进同一个意图，自动升权会把道指当恒生报、把期货价当现货价报。
- **根因**：覆盖度门禁只比对"候选声明的 `provides`"与"意图要求的 `requires_coverage`"，**声明是人工写的，门禁无法验证字段真假**——写宽了等于开后门。另外排序只按延迟，而"延迟最低"与"答得全"是两件事；不同标的放同一池，等于允许系统用一个品种的价答另一个品种的问题。
- **规避**：① `provides` 按实测字段写，不确定就不写；宁可少声明、让它降级，也不要把模板要用的字段写宽；② 一个意图只对应一个标的，候选只能是**同标的不同源**，不同标的必须拆成独立意图（伦敦金/COMEX、恒生/道指/纳指各一条）；③ 覆盖度不足一票否决，不论多快；④ 换首选加"快 20% 以上"门槛，避免每天抖动；⑤ 备选掉线只记录不报警，只有"某意图无可用首选"才判失败，否则巡检天天红等于没红。
- **验收判据**：看"首选能不能填满模板"和"每个意图的候选是不是同一标的"，而不是看"首选是不是最快"。
- **复发**：1

## L49 降级备用要"先比覆盖字段、再比延迟"，否则最快那条恰好答不了关键问题（数据源 · 2026-11-06）

- **现象**：建路器给 `weather.today` 建备用，排在第二位的备选是 `sk_2d`（28ms，全场最快），而不是 `dingzhi`（164ms）。但 `sk_2d` 只有温湿度，说不了晴/雨；`dingzhi` 能给温度和天气现象。"今天天气怎么样"最缺的恰恰是晴雨。
- **根因**：完整源（字段全覆盖）按延迟排序没问题；降级源（字段不全）也照抄了按延迟排序。延迟低只说明它快，不说明它还能答出多少。
- **规避**：① 降级源排序改为"覆盖必需字段的比例降序、比例相同再比延迟"；② 把 `coverage_ratio` 与 `missing_fields` 写进候选，回复时能直接说缺什么；③ 建路与巡检两处必须用同一套排序，否则建的时候对、巡检一跑又换回去。
- **验收判据**：看备用位上的源"能答出几条必需字段"，不是看它多快。
- **复发**：1

## L50 巡检判"坏"要连续失败，单轮 3 次采样挂 1 次不算（数据源 · 2026-11-06）

- **现象**：巡检第二轮，`open-meteo` 这一轮 3 次采样里挂了 1 次（`http:URLError`），当场被降出备选位，`changelog` 里多了一条角色变化；下一轮它又正常了。照这么跑，每天都会因为一次超时来回换角色。
- **根因**：升降级只看本轮 `ok_rate >= 0.9`，等于"一次超时即判坏"。配置里本来就有 `demotion.fail_streak = 3`（连续失败才让位），但代码没读它。
- **规避**：① 健康判定改为"本轮成功率过半 且 连续失败轮数未到 3"，`fail_streak` 由 `apply_health` 维护；② 换首选仍保留"快 20% 以上"门槛，两道门一起防抖；③ 验收要看"连续跑三轮角色有没有变化"，只看一轮看不出来。
- **验收判据**：连续三轮巡检，除耗时数字外，角色与 `changelog` 不新增变化。
- **复发**：1

## L51 「问到才建路」接进对话主链时，最容易静默答错的三处（数据源 · 2026-11-06）

- **现象**：接线冒烟 8 条问句，第一轮 2 条 MISS（"沈阳天气怎么样"、"白银多少钱"）、1 条答错（恒生报成 24404.62，那是今开，不是现价 24502.44）。三处修完才 8/8 全绿。
- **根因**：① 五个解析器里只有新浪带 `asset` 参数，其余按单参调用，`TypeError` 被上层的 `except Exception: return None` 吞掉，表现成"没命中"，看着像意图识别问题；② 港股字段 `[2]` 是今开、`[6]` 才是现价，凭印象取 `[2]` 就把开盘价报成现价，数字看着合理不会报警；③ 种子册 `catalog` 条目没带 `asset`，新建分支拿不到标的，建路器直接判"缺 asset"退出；④ `汇率`、`指数多少点` 这类宽触发词会把别的品种吞进来（"欧元汇率"答成美元兑人民币、"深成指"答成上证）。
- **规避**：① 解析器统一签名 `(text, asset)`，调用方不按类型分支；② 字段下标一律以实测样本为准，改完必须用一条已知值反算核对（恒生 24502.44 − 24796.98 = −1.19%，对得上才收工）；③ `catalog` 条目必须自带 `asset`，由脚本从配置回填而不是手写；④ 触发词只写明确品种名，宽泛品类词（汇率/指数/金价）留给专用意图或兜底；⑤ 冒烟用例必须含"没配过的类型"，否则建路分支根本没被测到。
- **验收判据**：8 条问句全绿；同一条问句第一次 `built=True`、第二次 `built=False`；数值与实抓样本对得上（不是"有回复"就算过）；写回的配置里能看到 `build_state` 和候选角色。
- **复发**：1

## L52 验收读端的逐字节断言和生产端的 JSON 键序对不上时，测试会全绿却判不过（T2/E02 · 2026-11-06）

- **现象**：E02 source13 冷导入第六轮之前，审计层已经零拒绝、例外收据 `clean=true`，产品侧 `research.md` 711B 六轮不变；但正式运行仍以 `"Exact producer JSON-string bytes/order"` 失败。把消息补成带偏移的诊断后，首差在偏移 582：存储串是 `"agent": "58e6ddf…`，期望串是 `"success": true`。
- **根因**：读端有两份"期望重建"（`rebuild_expectations` 与 `validate_collection`）把 TOOL_CALL_END 的 data 按 `tool, agent, success, latency, result, metadata` 构造，而真实生产端 `openjarvis\tools\_stubs.py` 发布顺序是 `tool, success, latency, result, metadata, agent`。`_safe_equal` 只比数值、忽略键序，所以值级校验全过；`json.dumps` 整串比逐字节，键序不同即失败。测试夹具 `quarantine_fixture` 复刻了同一个错误顺序，于是 566 条测试全绿也抓不到。
- **规避**：① 凡是要做"逐字节相等"的期望重建，键序必须从真实 producer 的字面构造取证，不能按语义字段顺序凭印象写；② 值比较和串比较不能混用同一套期望——要串比就全链路保序；③ 夹具必须携带生产端真实序列化顺序，否则测试只验证了"自己跟自己一致"；④ 断言消息里带首个差异偏移与前后窗口，否则只能看到一句"bytes/order"。
- **验收判据**：定向 59 条与全量 566 条全绿只是前置；真正的判据是正式运行 reader 退出码 0、`candidate_mechanical_verified`、四条 trusted 成员放行（`c794f6fd` 已达到）。
- **复发**：1

## L53 机械通过不等于验收通过：自签授权链把“跑完了”和“判过了”分成两件事（T2/E02 · 2026-11-06）

- **现象**：修复读端键序后，正式运行 `c794f6fd` 的 reader 退出码 0、`candidate_mechanical_verified`、`mechanical=PASS`、cleanup PASS，但终态仍是 `PENDING_RESULT_REVIEW`，`e02=NOT_PASSED`、`acceptance_credit=false`、`outer_root_gate=NOT_ISSUED`。看上去“都绿了”，实际一分未得。
- **根因**：`entry.py` L155–156 把 `e02='NOT_PASSED'`、`acceptance_credit=False` 写死，L142 成功后只进 `PENDING_RESULT_REVIEW`；验收分只由外层独立结果复核签发，准备门本身是 `PASS_PREPARATION_ONLY`、`actual_authority=false`。同一会话自签的准备评审只能作诊断证据，文件必须带 `independence_note`。
- **规避**：① 汇报时必须把“机械链路通过 / 验收结论产出”分成两行写，不能用一个 PASS 概括；② 判定 E02 这类复合任务，先把终态字段（`terminal.status`、`e02`、`acceptance_credit`、`outer_root_gate`）逐项读出，再决定下一步是重跑还是复核；③ 配额为 0 时不要用重跑代替复核——重跑只会消耗新的执行配额，仍拿不到验收分；④ 看板的“done”只能表示定性任务完成，必须在描述里同步写“E02 尚未验收”。
- **验收判据**：终态出现 `outer_root_gate` 已签发、`acceptance_credit=true`、`e02=PASSED` 三项同时成立，才算 E02 过；只出现 `candidate_mechanical_verified` 不算。
- **复发**：1


## L54 只读复核先怀疑自己的映射，再怀疑产物（T2/E02 · 2026-11-06）

- **现象**：对已完成 run 做逐字节复核时，27 项里有 2 项报红：`first_result_sha256` 对不上 cleanup-observation，保护快照三份文件哈希不一致。第一反应容易写成“产物有问题”。
- **实情**：`first_result_sha256` 对应的是 `profile-first-result.json`，不是 cleanup-observation；保护快照的 `identities` 是 7 条，但文件顶层还有 `observed_at_ns`，按顶层键数会数成 3。两处都是复核脚本的映射错误，产物本身没问题。
- **规避**：① 摘要字段先找“它到底是谁的摘要”，用文件逐个试算比对，不按名字猜；② 结构计数要数到目标数组（`identities[]`），不数外层键；③ 复核报告里保留“复核人自纠”记录，第一版误报不能悄悄改绿；④ 复核脚本自身也要有失败路径，宁可报红后查明，不可为了让结果好看放宽断言。
- **验收判据**：27 项全绿且每一项都有“字段→文件→重算值”的对应关系；只有“全绿”没有对应关系不算复核。
- **复发**：1

## L55 项目队列写 executing 不等于全局主表已登记，Codex 会 fail-closed 停在 T0 前（UltimaAgent · 2026-11-08）

- **现象**：工单 0013 在项目队列 `tasks/queue/index.md` 里是 `executing`，但首派回执是 `BLOCKED_BEFORE_T0`，T0–T3 全部未开始、源码零改动、tag 未产生。用 `rg` 精确搜工单号，全局主表 `_shared/queue/global-queue-index.md` 零命中。
- **根因**：G-DISPATCH-001 的准入以全局主表为准，项目队列的 `executing` 只是项目级视图，不能替代全局登记。Codex 的写域不含"项目外权威文件"，按 fail-closed 拒绝越域自行补登记，停在准入门。
- **规避**：① 派发前先在全局主表 `rg` 工单号做回读命中，命中后才算准入；② 主表结构是 `<!-- queue-items:start -->` 到文件末尾，明细行格式 `| 项目 | 工单号 | 状态 | 说明 |`，补登记只写明细行，不手改上方统计表（看门狗重算）；③ 补登记必须留备份与回读证据，并在载荷里写明"已在主表登记、上一轮 fail-closed 未改源码、本轮从 T0 全新开始"。
- **验收判据**：主表 `rg` 命中且状态正确 + 派发载荷含准入说明 + 回执不再是 `BLOCKED_BEFORE_T0`。
- **复发**：1

## L56 Codex 进程被终止不会写 final 回执；policy 拦截与模型刷新超时是噪声，不等于任务失败（UltimaAgent · 2026-11-08）

- **现象**：0027 在 T2 全量门约 35% 时进程消失，run 目录没有 `final.json`，主表登记仍停在 `executing`。0013 执行中反复出现 `failed to refresh available models: request timed out`、`exec_command ... rejected: blocked by policy`、`Reconnecting... waiting for network`，但最终 T0–T4 全 PASS 并正常生成回执。
- **根因**：`codex exec --output-last-message` 只在会话自然结束时写回执文件，被终止/崩溃时不写；`blocked by policy` 是 Codex 自身命令策略拒绝（涉及 `Remove-Item -Recurse -Force`、敏感临时目录等），它会换等价命令重试；模型刷新与网络重连是后台噪声，不影响已完成的工具调用。
- **规避**：① 判断任务结束看"进程是否存活 + final 文件是否生成"两件事，只有进程消失没回执要判为中断并人工纠正主表状态；② 见到 policy 拦截先看后续是否有等价命令成功，不据此判死；③ 见到重连/刷新超时看 out 日志字节是否仍在增长，增长即仍在推进（0027 与 0013 的差别就在这一点）；④ 主脑独立复核时，真实推理类用例在全量并发下会冷启动超时，失败时应单跑复验再定性。
- **验收判据**：只有 final 回执 + tag 远端 SHA 回读一致 + 主脑独立定向复核通过，才可把工单判为完成。
- **复发**：1
## L57 「最小改动边界」与「加一页还在预算内」都必须先用证据核验，不能由提案口气决定（UltimaAgent · 2026-11-08）

- **现象**：工单 0028 只读评审 E02 写入资格提案，推翻了两条被当作前提的说法。①边界：冻结候选工作树 `src/brain/work_research.py:810-823` 独立重算 `eligible=len({source_id for visible if cards})>=3` 并 `allowed.append(action('..._write'))`，即独立重放侧自己也持有一份写入资格判定，只改 `work_navigation.py` + `agent_server.py` 不会自动传到重放；②容量：用保存的 `trusted-runtime.raw`/`trusted-replay.raw` 按 canonical JSON 只读重建，当前第 6 代 `messages+schema` = 29,998（余量 2,770），新增任一可渲染 S4 页后为 33,837–39,147，284 个起点无一落在 32,768 硬门内；③revision：提案依据 commit `43da3f0`，而当前分支 `codex/voice-fsmn-new-path` 根本没有 `src/brain/work_navigation.py`，`agent_server.py` 与之相差 650 增 18 删。
- **根因**：写方案时把"设计上应该只有两处""再加一页应该够"当成结论，没有在目标 commit 上做模块归属核查与数值重建；评审侧一旦照抄，就会拿着错误 revision 的补丁去"最小修复"。
- **规避**：① 任何"最小改动边界"结论前，先在目标 revision 上 grep 同一个判定表达式（如 `eligible`、`>=3`、`allowed`、write permit）列出全部持有处，逐处编号；② 任何"再加一页/一条仍在预算内"的主张前，用保存 wire 只读重建出各门的实际数值，不用估算；③ 提案必须写明依据 commit，并与当前工作树比对，不一致就先锁 revision 再谈改法。
- **验收判据**：边界结论附"文件:行号"逐处清单；容量结论附下界数值与重建方法；revision 一致，或明确锁定待改对象。
- **复发**：1
## L58 「元工具看板」与「产品看板」是两种写权，不能互相塞工单（UltimaAgent · 2026-11-08）

- **现象**：北极星 HTML 焦点框「运行中 55 分钟」刷新多次不变，复核查出 `final-message.json` 已于 17:00:23 落盘，进程 PID 39672 早已退出——看板把一个结束半小时的工单显示成在跑。修第一版时仅用 PID 存在性判存活，被系统复用给别的进程骗过，误报「运行中 1 小时 33 分钟」。同时数出看板 56 条任务条目里 34 条带人工填写百分比。为避免继续失真，一度打算把采集需求写进模块4 工单 0030。
- **根因**：把「豆包自己的仪表盘（元工具）」与「Agent 产品内执行看板（产品能力）」当成一件事。前者属于主脑写权、应当直接维护；后者才是 Codex 写域。混在一起的后果是：既给 Codex 塞了不属于它的活，又让产品工单范围失去闭合性。
- **规避**：① 北极星 HTML、工单卡、全局主表状态行 = 主脑写权，直接改、不派单；② ledger、活动级阶段解析器、A2UI 执行看板页 = Codex 写域，0030 已写明「本阶段不改 `docs\tracker\北极星上线任务清单.html` 的数据源」；③ 判任务是否在跑必须「进程存在 + 启动时间与派发时间吻合（±180s）」，单看 PID 会被复用骗过；④ 看板只要还有手填百分比，页面就必须显式标注「人工校准口径」，不得默认为实时。
- **验收判据**：看板上每一处「事实」字段，都能说出它的采集来源与采集时刻；说不出来的，必须在页面上标为人工校准。派发前核对：工单写域是否包含主脑元工具路径，包含则退回改写。
- **复发**：1
## L59 计划任务调本地脚本：任务结束会杀掉整个进程树，SYSTEM 还看不见用户盘符（UltimaAgent · 2026-11-08）

- **现象**：把看板采集挂成每 5 分钟无窗计划任务，连挂三次都「成功」却零产出。①`-RepetitionDuration ([TimeSpan]::MaxValue)` 报 `任务 XML 包含格式不正确或超出范围的值 (10,42):Duration:P99999999DT23H59M59S`，任务根本没建成；②改 SYSTEM 身份后 `LastTaskResult=0`，但 `live-data.js` 的 `updatedAt` 纹丝不动、日志也没生成——SYSTEM 会话看不到 H: 盘符，python 从未真正执行；③再换回当前用户仍不刷新，根因是 vbs 里 `ws.Run "cmd /c ...", 0, False` 传了异步，wscript 立即退出，Task Scheduler 判定任务完成即回收整个进程树，python 被连带杀掉。
- **根因**：计划任务的进程管理与普通 shell 不同——任务实例结束就关闭 Job Object，子孙进程一起终止；且服务账户（SYSTEM）与交互用户会话的盘符映射视图不共享，`H:` 这类用户会话内可见的盘符在 SYSTEM 下可能不存在。`LastTaskResult=0` 只证明「被启动的那个 exe 正常退出」，不证明业务动作完成。
- **规避**：①`-RepetitionDuration` 不用 `[TimeSpan]::MaxValue`，改固定时长（实测 `New-TimeSpan -Days 3650` 可用）；②运行主体优先用当前登录用户 `-LogonType Interactive`，目标文件在用户会话可见盘符上时更稳；③非要用 vbs 包装，`ws.Run` 第三参必须 `True`（保活到子进程结束）；④最省事也最无窗的做法是放弃 vbs+cmd，让任务动作直接是 `pythonw.exe`（无控制台，天然无窗、无中间层）；⑤判成败看产物时间戳是否前进，不看 `LastTaskResult`。
- **验收判据**：连续两次周期触发后产物 `updatedAt` 都前进；`NextRunTime` 已推进；可见窗口进程表为空（`MainWindowHandle -ne 0` 无命中）。
- **复发**：1

## L60 审计「100% 已完成」不能看标注，要先取运行时实证；且「人工可用」不等于「自动可用」（UltimaAgent · 2026-11-08）

- **现象**：对北极星看板模块1/2 做独立审计，逐条取证后推翻两条标注。①模块1「UltimaManager 全局工单登记接口：100% ✅」——`Test-NetConnection 127.0.0.1:18766` 返回 False、无 UltimaManager 进程，实际登记是 `GlobalQueueRegistrar` 直接写 `global-queue-index.md` 纯文本，该接口属「代码在、服务未部署」；②模块1「Git 自动打 Tag：100% ✅」——`git tag` 确有 248 个，但没有任何脚本会在任务完成时自动打 tag，全部手工；`freeze-approved-v01/v03.py` 只是针对特定版本基线的专用冻结脚本，不是通用门。模块1 真实 5/6，而非 6/6。
- **根因**：看板进度用机械规则累计（条目文本是否含「100% ✅」），标注全靠人工维护，且维护者容易把「规范写了」「代码在仓库里」「我手工跑通过」都记成 100%。更深一层：模块1/2 的完成度本质是「人推着系统走」的流程完备，而北极星要的是「系统自己跑」的自动化能力，两者被同一套百分比混算了。
- **规避**：① 任何标 100% 的条目，审计必须给出可复现取证命令与实测输出（端口 `Test-NetConnection`、进程 `Get-Process`、文件体积/条数、代码 grep 命中行）；② 端口类能力未监听一律判未完成，不能因「项目目录存在」而放行；③ 涉及「自动」二字的条目，必须指出具体自动化的触发点与脚本路径，指不出来的按人工处理降级；④ 区分「人工可用」与「系统自动可用」两档分别计分，自动化档位另立条目，不与流程档位混在一个百分比里。
- **验收判据**：每条 100% 都附「取证命令 + 实测输出」；说不清采集来源的事实字段，页面必须标注「人工校准口径」。
- **复发**：1

## L61 队列引擎「三件套齐全」不等于「接通了」：状态机/依赖DAG/插队都在，但没有一条真实链路调用它（UltimaAgent · 2026-11-08）

- **现象**：用户按目标架构追问「任务应在队列与交付之间形成闭环：合格打 tag、不合格标记问题后重审依赖再插回队列」，核对代码发现 `tasks\queue_engine\` 里能力其实齐备——`state_machine.py` 8 态迁移表含 `AUDIT→COMPLETED` 强制 `audit_passed`、`FAILED→QUEUED` 限 2 次重试后转 `BLOCKED`、`block_failed_dependents` 依赖失败自动冻结下游；`priority_deps.py` 有 `requeue_before` 插队、`validate_acyclic` 环检测、`dependency_gate` 依赖门。但真实派发从未经过它：引擎数据源是 `tasks.json`（46 条，`voice-01`/`s2-tool-extend` 等老卡 ID，其中 5 条状态值为 `TERMINATED`，根本不在 8 态枚举内），而实际派发走 `tasks\queue\wo-*.md` 卡 + 手改 `global-queue-index.md` + 手工起 codex 进程。引擎实例化点只在 `cli.py`/`audit.py`/`dispatcher.py` 内部及一个自测脚本，没有一个被真实派发脚本调用。
- **根因**：能力建设与链路接线是两件事，被当成了一件。代码写完后从未有一次真实工单走过 `QUEUED→EXECUTING→SELF-CHECK→AUDIT→COMPLETED`，于是没人发现数据源格式（Markdown 卡 vs tasks.json）、状态命名（8 态 vs TERMINATED 等历史值）、派发入口（cli vs 手写 dispatch 脚本）三处全部对不上。叠加结果：看板上的「有序」由主脑人工模拟，闭环的最后一环比初判完整：`audit.py:243 RecoveryManager.create_correction` 已实现「FAILED/BLOCKED → 派生 `{root}~r{N}` 修正子卡 → 挂进原卡 dependsOn → 原卡等子卡审计通过才重验」，并清空历史 ACCEPT、不覆盖旧卡、retryCount≥2 拒建（比原地重放严谨得多）。但它同样只认 `tasks\cards\` 老卡格式（要求卡内含 `**task_id**：` 与 `## dependsOn[]` 章节），未接 `wo-*.md`；且它只修单卡，不重排其他工单的依赖——「重审依赖关系」这一步依旧空白。另：`fileDomain` 字段与 `_all_paths_in_domain` 守界审计已在，但缺「两个并行任务 fileDomain 重叠」的前置判定。
- **规避**：① 判断某能力「已实现」必须同时验证三层：代码存在、**实例化点被真实入口调用**、**数据源格式与状态取值能对上**，任一断裂即判「未接线」，不得计入完成度；② 引擎与 `wo-*.md` 之间必须先有适配层（0031 的 schema + validator 正是前置），接通前不得对外宣称「队列自动化」；③ 审计失败的闭环要单独立项设计「返修工单生成 + 依赖重排 + 插队」，不能拿 `retryCount` 原地重放冒充；④ 索引里出现枚举外状态值即视为跨体系污染，先做状态映射再谈迁移。
- **验收判据**：`tasks.json` 中 `wo-` 前缀占比、全部状态值落在 8 态枚举内、派发脚本里能 grep 到 `QueueStorage`/`QueuePlanner` 调用行、且至少一张真实工单留下完整 `events/<task_id>.jsonl` 迁移链。
- **复发**：1

### L62 · 看板对「已冻结但无 final-message」的工单永久误报中断（2026-11-08）

- **现象**：0031 打上冻结 tag、主表改 frozen 之后，看板焦点框仍显示「中断 · 无 final-message」，elapsed 从派发时刻持续增长（57 分钟 → 1 小时 2 分钟），越看越像还在跑。
- **根因**：`scripts/tracker-live.py` 的 `decide()` 只有三档判定（存活=运行中 / 不存活有 final=已结束 / 不存活无 final=中断），没有把主表状态纳入。工单靠「打 tag + 改主表」收口、日志里没有 final-message 时，必然落进中断档；elapsed 用 `now - dispatch_ts` 计算，没有封顶。
- **规避**：`decide()` 增加主表状态查询 `queue_state()`，`frozen/completed/done` 判「已完成 · 已冻结」，elapsed 改用最后一条日志的 mtime 当结束时刻。
- **复发标记**：1 次。同类风险：任何「结束状态写在别处、日志里没有收尾记录」的工单都会撞这条。

## L63 公共账本 fail-closed 是「正确的错误」：主表一个自造状态词就能打断全项目派发（UltimaAgent · 2026-11-08）

- **现象**：5 次派发中 2 次在启动 40 秒内被打断，run 目录只落 `before.json`/`prompt.txt`/`registry-*`、无 codex 进程，而主表该单已被写成 `executing`（假执行中）。3 小时内同一位置出现 3 个不同自造状态词：`proposal-pending-gate`、`arch-review-approved`，连工单号都被改成 `wo-ultimasentinel-*`。写者实为 `H:\UltimaAI\UltimaSentinel` 项目的 codex exec（PID 28720）在跑自己的 pipeline 测试时写入。
- **根因**：`queue-status-gen.py` 把 `STATES` 锁死为 6 态，遇其他任何词 `raise ValueError` 退出 1；而它是 `dispatch-work-order.py` 的硬前置且不捕获 → 任何一个项目往公共主表写自己的状态词，全项目派发全部失效。这是**公共池子 + 单一权威判据**的结构性错配：账本没有写入门，读出端却按最严标准 fail-closed。
- **规避**：① 判「主表打断」不要只看 status-gen 报错文案（它把「重复」和「非法」合并成一句），必须独立扫描区分：重复 `(project,wid)` 才是真损坏，未知状态词只是语义外溢；② 派发前先跑一次 `queue-status-gen.py` + 独立扫描双确认，不能只信 dry-run `ready:true`（dry-run 会过，execute 才调 status-gen）；③ 抢修数据用 `read_bytes().decode()` 分行，`Path.read_text()` 的 universal newlines 会把 CRLF 吞成 LF 让整文件变一行，导致修复脚本静默「无可修复项」；④ 机制修法二选一（宽进严出加 unknown 分组 / 约束写入方只写 6 态）属标准变更，需 Owner 拍板，抢修只做数据归一。
- **验收判据**：主表 150 条 / 唯一 150 / 0 重复 / 0 非法；`queue-status-gen.py` 退出 0；派发后 run 目录内出现 `out.jsonl` 增长 + codex 进程存活。
- **复发**：3

## L64 回执判读的三个静默洞：短路掩盖 TypeError、裸子串串单、全角冒号吃掉「待审计」（UltimaAgent · 2026-11-08）

- **现象**：`done.json` 连续写 `receipt_valid:false, state:blocked`，而 Codex 回执明确是 `READY_FOR_DEEPSEEK_AUDIT`。逐层复现出三个洞：① `status in {…}` 在 status 为 list 时抛 `unhashable type: 'list'`，但被 `valid_payload` 短路掩盖，只在 evidence 有效时暴露，而派发器调用处**无 try/except**，真触发会打崩派发器；② `if work_order not in text` 裸子串，`wo-orb-w7` 命中 `wo-orb-w7x`；③ 自检判据写 `自检\s*PASS`，而回执实际是 `- 自检：PASS`（全角冒号），正则不认 → 整个回执判 invalid → 待审计落 blocked。
- **根因**：回执契约用「弱信号叠加」（工单号出现 + READY 词 + 自检 PASS）代替「结构化字段判定」，且正则按半角标点写死。中文回执的全角标点是常态，任何 `\s*` 连接都会被冒号打断。
- **规避**：① 类型不可信字段先 `isinstance` 收口再进集合判断，不能靠短路侥幸；② 工单号匹配一律加 `(?<![\w-])…(?![\w-])` 边界；③ 中文语境的固定词判据必须容忍 `[：:]`，`自检\s*[：:]?\s*(?:PASS|通过)`；④ 验证回执契约必须用**真实历史回执**做正反样本（待审计/BLOCKED 各一份），合成样本会漏掉真实排版差异。
- **验收判据**：三份真实 final.json 判读正确（w6 待审计→audit、w6 BLOCKED→blocked、w7 READY→audit）；`status=[]`/`{}` 落 `blocked,valid=False` 且不抛异常；`wo-orb-w7x` 不得判成功。
- **复发**：1

## L65 「全量」在这个仓库没有定义：根递归收进外部源码与证据快照，14028 errors（UltimaAgent · 2026-11-08）

- **现象**：Codex 首轮按工单跑根目录全量，`collection errors=14028`、耗时 1997.14s 后失败，`passed=0`。而按白名单口径 `tests src scripts tasks execution` 只有 **1143 tests collected in 8.51s**。
- **根因**：仓库顶层是混合体——`libs`（外部库）、`legacy-topo`（历史工程）、`data`（证据快照，同名测试触发 `import file mismatch`）、`docs/research/sources`（研究源码）、`tools/*/source`（上游源码）与自有代码同级。没有 `pytest.ini` 时 pytest 一律根递归，把别人的测试当成自己的。
- **规避**：① 「全量」必须写成显式目录白名单 `testpaths`，不能默认根递归；② 定口径前先数 `test_*.py` 分布（`src` 93 / `tasks` 9 / `scripts` 3 / `tests` 5 / `execution` 1），再决定白名单，不要凭「tests/ 只有几个文件」推断覆盖范围；③ 收窄作用域前先判断是否只剩自测——本仓库 `tests/` 只有 5 个文件全是近期新写，若 `testpaths=tests` 就等于自测门零回归，必须带上 `src`；④ 排除历史备份用引号包 `"Topo Backup"`。
- **验收判据**：根目录无位置参数执行，`collection errors=0`，收集量约 1143，耗时 10 秒级。
- **复发**：1

## L66 · 主表写入方不守契约，生成器又把行尾翻掉（2026-11-08）

- **现象 A**：`queue-status-gen.py` 解析主表时报 `ValueError: too many values to unpack`。定位到 UltimaSentinel 侧新写一条 `closed` 状态，且 reason 字段里夹了 5 个 `|`，把一行撕成 9 列。
- **现象 B**：生成器用 `read_text` + `write_text(encoding='utf-8')` 写回。`read_text` 的 universal newlines 把 CRLF 吞成 LF，一旦摘要表内容变化触发写回，整张 2.8 万行主表就被翻成 LF——下一次按 CRLF 切行的修复脚本会静默 no-op。
- **修法**：①`read_items` 改为「字段数 >=3 才解析，第 4 段之后全部并回 reason」，畸形行登记 `MALFORMED` 继续生成；②未知状态归一 `unregistered`，继续生成并在 stdout 点名清单，只有重复 `(project,wid)` 仍 fail-closed；③读写改 `read_bytes`/`write_bytes`，行尾由原文 `NL` 决定（摘要表拼接也用 `NL`）。
- **口径**：公共账本无法约束所有写入方，读出端必须「宽进严出」——容忍未知状态和畸形行并点名，只对真正的数据损坏（重复工单）硬停。写入门（6 态白名单 + 4 列格式校验）须落在各项目自己的登记脚本里，不能只靠读出端兜底。
- **复发记录**：两小时内 UltimaSentinel 侧共写入 5 次非 6 态值（`proposal-pending-gate`、`arch-review-approved`×2、`closed`×2），全部来自 `H:\UltimaAI\UltimaSentinel` 的 codex 进程。

## L67 · 串行名额没有出口，队列会被一个被遗忘的工单永久堵死（2026-11-09）

- **现象**：`wo-orb-w9` 回执已判定有效（`receipt_valid: true`），却仍落 `state: blocked`、`audit_slot_busy: true`。查主表发现 5 个工单同时停在 `audit`。
- **根因**：审计名额的判定是「主表里只要还有**别的**工单处于 audit，就降级 blocked」。规则方向没错（审计必须串行），但只写了入场条件，没写**离场条件**——一个被遗忘或长期待 Owner 验收的工单会永久占着唯一名额，后面所有工单只能无限排队。限流机制如果只有「进」没有「出」，等价于全队列停摆。
- **修法**（`scripts/dispatch-work-order.py::audit_slot_holders`）：①等待超过 `AUDIT_SLOT_MAX_AGE_DAYS`（默认 7，环境变量 `ULTIMA_AUDIT_SLOT_MAX_AGE_DAYS` 可覆盖）不再占位；②状态理由已写明「范围外冻结/已冻结」的直接不占位，与天数无关——这类单已不在流程内；③**取不到任何时间戳仍算占位**（fail-closed），信息缺失不是驱赶在途单的许可；④取证顺序为该单最新 run 的 `done.json.finished_at` → 主表理由里的显式日期 → 放弃，**最新证据优先**，避免旧文案里的历史日期把一个刚重派的单赶走。
- **实测**：真实主表 5 个 audit → 3 个超 7 天放过、1 个标冻结放过，只剩 1 个在途（0.1 天）正常占位。回归 58 passed。
- **口径**：凡「限 N 个在途」的准入控制，必须同时定义超时/失效出口，并在放行时点名**放过了谁、为什么**（落 `audit-slot.json` 与状态理由），否则限流会退化成死锁且事后无从追查。
- **边界**：机制只决定「是否占位」，不替这些工单改状态。是否把滞留单正式转 blocked，属于人的裁决，不自动化。
- **复发**：1

## L68 · 执行器升级换了安装位置，派发器 "找不到" 就全线停摆（2026-11-09）

- **现象**：`wo-orb-w9` 派发返回 `{"blocked": true, "reason": "Codex 执行器不存在"}`。同机同工单，几分钟前还能正常派发。
- **根因**：派发器只用 `shutil.which('codex.exe')` 一条路找执行器。Codex 更新到 `26.1103.4239.0` 后主程序被放进版本化包目录 `C:\Program Files\WindowsApps\OpenAI.Codex_<版本>_x64__<publisher>\app\resources\codex.exe`，而 `WindowsApps` alias 目录只保留两个辅助 exe，**主程序不再有 alias**。PATH 查不到 → 判定"没装"。
- **误导性**：报错文案字面是"执行器不存在"，看起来像未安装，实际是"装了但搬家了"。且断裂发生在升级瞬间，前一次派发仍正常，"昨天能跑"无法作为排除依据。
- **修法**：`resolve_codex_exe()` 多路解析 —— ①环境变量 `ULTIMA_CODEX_EXE` 最高优先（路径不存在则忽略、不硬失败）；②`shutil.which('codex.exe'|'codex')`；③四组 glob 兜底（Store 版本化包、WindowsApps、npm 全局、`Programs\*`）。多版本共存按 mtime 取最新，防止捡到旧版。
- **实测**：解析到 `OpenAI.Codex_26.1103.4239.0_x64__2p2nqsd0c76g0\app\resources\codex.exe`，真派发走完全链路 `exit_code: 0`，`audit-slot.json` 与 `done.json` 新字段落盘实证。回归 62 passed。
- **口径**：任何"外部可执行体路径"都不得只靠 PATH 判定存在性，尤其是会自更新的桌面客户端——升级会改安装位置且可能不留 alias。找不到时的报错必须区分"未安装"与"安装了但位置变了"，否则运维会朝错误方向排查。
- **附带**：`%LOCALAPPDATA%\CrashDumps` 里 codex 崩溃转储已累积 5 个（11-01/11-02/11-04/11-08），属持续数日的间歇性崩溃，与卡点 D 同源，待单独跟进。
- **复发**：1

## L69 · 验收卡的 goal 承诺了 ACC 没验的条件，判据自相矛盾必然 FAIL（2026-11-09）

- **现象**：`orb-w9` 复验卡两轮独立审计都判 FAIL。实际结果 `receipt_valid: true`（回执有效）但 `state: blocked`（没拿到审计名额）。审计指出「与 goal 写的『而不是落到阻塞』矛盾」——判得对。
- **根因**：同一张卡的两句话在说两件事，却被当成一件事。goal 写「使回执被判为有效（`receipt_valid: true`、`state: audit`），而不是落到阻塞」——把"回执有效性"和"最终状态落位"绑在一起；而 ACC-5 只验 `receipt_valid` 为 true。`state` 实际由**审计名额是否空闲**这类外部条件决定，根本不是本卡能控制的。于是无论跑几次，只要名额被占，goal 就为假、ACC-5 就为真，永远收敛不了。
- **修法**：把两件事显式拆开。goal 只承诺「判读器判为有效」，并写明「`state` 落哪一态由外部条件决定，不在本卡可控范围、不作判据」；ACC-5 补一句「`state` 字段不参与本卡判定」。
- **口径（通用）**：①验收卡的 goal 与 ACC 必须验**同一件事**，goal 里出现的每个结果词都要有对应 ACC，否则就是承诺了不验的东西；②凡结果依赖**本卡不可控的外部条件**（名额、配额、队列状态、他人改动），一律写进边界说明并排除出判据，不能混入 goal；③自相矛盾的判据不会"有时通过"，只会稳定失败，且审计每次都能正确抓到——问题不在审计，在卡。
- **附加**：本卡后来整体失效（目标文件已被 `30b36e7b` 提交进 HEAD，「新增唯一文件」前提消失）。验收卡依赖"文件尚未存在"，一旦上游把该文件提交，卡就作废，这类卡应标注失效而不是反复重派。
- **复发**：1

## L70 · 为验证开源项目能否运行，把它的宿主运行时框架装进了本机（2026-11-09）

- **现象**：判断 `cft0808/edict` 能否跑时，看到 `install.ps1:30-34` 缺 `openclaw` CLI 就 `exit 1`，于是 `npm install -g openclaw` 装上 2026.11.2，准备据此"验证 edict"。
- **定性**：方向错误。edict 的代码（`scripts/kanban_update.py` 等）是纯标准库 Python，与 OpenClaw 无调用关系；`openclaw` 只是它声明的**宿主运行环境**。装宿主 = 引入第二个第三方产品，与"把人家源码搬进我方仓库"正相反。用户当场两次否决。
- **误导来源**：先做的依赖核查其实已给出"不需要宿主"的证据（`requirements.txt` 明写"均为 Python 标准库"、`kanban_update.py` 只 import 标准库 + 同目录两个模块），但被"install.ps1 要求 openclaw"这一条盖过 —— 把**安装器的前置检查**误当成**代码的运行前提**。
- **处置**：`npm uninstall -g openclaw` → `removed 508 packages`，`openclaw.cmd` 已不存在，`~/.openclaw` 从未创建，无进程残留。
- **替代做法（已验证可行）**：只搬 `file_lock.py` / `utils.py` / `kanban_update.py` 三个文件，改 8 处硬编码（数据根目录、刷新钩子、身份环境变量），`tests/test_gorch_kanban.py` 8 passed，8 进程并发写零丢失。全程零第三方依赖。
- **口径（通用）**：开源项目的 `install.*` 脚本要装什么，只说明**作者预设的部署形态**，不说明**代码本身依赖什么**。判断能否只搬代码，看 import 图，不看安装器；安装器要求的宿主一律先当作"可丢弃的部署外壳"。
- **复发**：1

## L71 · 薄编排 gate 把"读不到结果"静默当成"可开工"，fail-open 被 fail-closed 收口（2026-11-09）

- **现象**：`test_full_batch_ready_blocked_summary` 单独跑稳定通过，与其他测试文件合并跑时低频失败（一次系统高负载，耗时 62s vs 正常 26s），`assert ready == []` 报 ready 多出 3 项、首项 '1'——即 1 已 in-progress、本应整批 blocked，却把 1/2/3 错判成"可开工"。
- **根因**：`gate_check` 是 **fail-open** 设计。它对每次 bash 调用预设 `status=''`、`unmet=[]`、`conflicts=[]`，再用 `startswith` 挑能匹配的行；当子进程输出丢失、或文件被实时杀毒短暂锁定导致 ccpm 的 `grep` 静默返回空时，标记行缺失/值为空，全部默认值恰好落在"可开工"分支。空结果被当成了"通过"。
- **修复（已提交 59cfd538）**：改为确定性 **fail-closed**——① STATUS/UNMET/CONFLICTS 三个标记必须齐全，缺任一即报错；② status 必须属于已知合法状态集合，空值或未知值报错；③ stderr 非空即报错；④ 子进程加超时。任何读取不可靠都停止派发，不猜。
- **教训（通用）**：接线层/解析层的默认值必须朝"拒绝"方向设计——空输出、缺字段、超时都应触发报错，绝不能让默认值恰好等于"放行/通过"。对子进程输出要校验"应有的标记是否齐全"，而不是只解析能匹配上的行、其余静默忽略。
- **复发**：0
## L72 · wt merge 超时被当成"没动手"，实际分支已被删除、提交变成孤儿（2026-11-09）

- **现象**：S7 真跑一单时调 `wt merge gorch/WO-README`，180s 超时被拦，报"fail-closed"。随后核查现场发现：worktree 目录没了、`gorch/WO-README` 分支没了、工作分支 `codex/voice-fsmn-new-path` 上没出现 `config/gorch/README.md`，执行端提交 `def92006` 不在任何分支上。
- **根因**：两层叠加。① `MERGE_TIMEOUT` 沿用了 `wt switch` 的 180s，而本仓库有 32 万+ 未跟踪文件，单次 `git status` 就要 90s+，`wt merge` 的 commit→squash→rebase 串下来必然超过 180s；② 超时处理把"进程被 terminate"一律当成"未变更"，但 `wt` 的第 7 步 cleanup 会删分支与 worktree，超时点落在 cleanup 之后时，分支已经消失而合并并未完成。
- **补正（2026-11-09 收口复核，推翻原结论）**：上面"没合入"的判断**是错的**。收口时回读 `main` 发现 `d1e51eb3 Squash commits from gorch/WO-README` —— 那次合并**实际合进了 `main`**（`wt merge` 的 TARGET 缺省是 default branch，不是当前检出分支），只是没合进工作分支 `codex/voice-fsmn-new-path`。所以真实失效是"**合错了分支**"，而不是"没合"。后续把 `def92006` cherry-pick 成 `ea6f08ec` 补到工作分支，等于同一份改动现在在两条链上各有一份。详见 L74。
- **处置**：`def92006` 对象仍在（git 未 gc），用 `git cherry-pick def92006` 恢复，产出 `ea6f08ec`、README.md 4209B 与执行端产物逐字节一致。同时改代码：`MERGE_TIMEOUT=600` 独立于 `WT_TIMEOUT`；超时后先调 `_branch_exists()` 探现场，分支已不存在就明说"可能已删分支但未完成合入，不要假定无改动"，分支仍在才敢说"主线应未变更"。新增 4 条测试锁住两种表述。**收口实测**：修好 target 后再跑真实合并，耗时 **227.4s**、`rc=0`、`rebased:true`、主线前进 `50af6549→3d0fc8dd`、报告 4020B 落地——600s 预算已被真实合并验证（227.4s 恰好落在"旧的 180s 会超时、新的 600s 有余量"之间）。
- **补充（2026-11-09 晚，remove 侧仍未收口）**：`MERGE_TIMEOUT` 已改 600s，但 `wt remove` 走的是另一个
  `WT_TIMEOUT=180s`，没跟着改。当晚清理三卡/双卡批次时 **TC-B、TC-C、MM-B 三次全部报"wt remove 超时（180s），
  fail-closed"，而三次目录都已删除、分支都已按 `--delete-branch` 消掉**——现象与本节完全同源：超时点落在
  wt 内部 cleanup 之后。三次全中说明这不是偶发，是 Windows 上 `wt remove` 的稳定耗时。处置建议（未实施，待 Owner 裁）：
  超时后回读"worktree 目录是否还在 + 分支是否还在"，两者都已消失就报"已清理（超时）"而不是 fail-closed。
- **复发**：3
- **教训（通用）**：① **超时 ≠ 无副作用**。对会做清理动作（删分支/删目录/删文件）的外部工具，超时后必须回读现场状态再下结论，不能把"进程没返回 0"等同于"什么都没发生"；② 一条工具的多个子命令，超时预算要按各自最坏耗时分别设定，不能共用；③ 判断"合并成功"只看最终产物是否在目标分支上，不看工具自己的 JSON 回执——本次回执根本没来得及产出；④ **"没合入"要限定到具体分支**。回读范围只覆盖工作分支时，"主线没出现产物"和"合到了别处"长得一模一样，必须把 default branch 也列进检查面。
- **复发**：1

## L73 · 把工单里合法的命令示例判定成"模型试图调用工具"（2026-11-09）

- **现象**：S7 冒烟单两次真跑，`work_order` 阶段都被判成 `stage work_order returned a tool-call attempt instead of an analysis result`。落盘原文显示 `matched_markers` 只有 `["```bash"]`，命中的是工单正文里合法的命令示例（`cp slots.example.json slots.json`），不是任何工具调用。
- **根因**：`_TOOL_CALL_MARKERS` 把 ```bash / ```shell / ```powershell 当成了工具调用标记。但 `work_order` 阶段的产出**本来就要**给执行端照做的命令（工单模板明确要求贴命令与输出），用代码块标记判定等于把合法工单整张误杀。又一次"拿字符串标记当类型系统"。
- **处置**：判定改走**协议级信号**——供应商在 `message` 里给出原生 `tool_calls` 字段才算工具调用，文本标记只留控制 token 泄漏（`<｜｜`/`｜｜>`/`DSML`）与带引号的 `"tool_calls"` 键。同时在 `run_stage` 失败落盘加 `response_excerpt` 与 `matched_markers`，否则"为什么被判成工具调用"无从复盘，只能重跑烧额度。新增 6 条测试（命令块不算、原生 tool_calls 必须拦）。
- **教训（通用）**：① 能用协议字段判断的，绝不用文本扫描；文本扫描只作为协议字段缺失时的兜底，且标记集合必须限定在"正常产出绝不会出现"的字符串上；② 判定规则要先问"目标阶段的合法产出里会不会自然出现这个模式"，会出现的就不能当违规信号；③ 失败必须留原文摘录，否则同类问题每次都要靠重跑复现。
- **复发**：0

## L74 · `wt merge` 的 TARGET 缺省是 default branch，编排把施工全铺到了 main（2026-11-09）

- **现象**：收口阶段再跑一次真实合并，`wt merge gorch/S7-smoke-report` 20.8s 就 `rc=1`，报 `CONFLICT (add/add): scripts/gorch/batch_orchestrator.py`、`CONFLICT (add/add): src/brain/orchestrator.py`、`CONFLICT (content): docs/tracker/北极星上线任务清单.html`。而从当前 HEAD 建的新分支不可能与同一 HEAD 的 target 产生 add/add 冲突。
- **根因**：`wt merge [OPTIONS] [TARGET]` 的第一个位置参数是**目标分支**，源分支才走 `--branch`；**TARGET 缺省就是 default branch（本仓库为 `main`）**。编排层 `merge()` 调 `wt_merge(branch)` 时没传 target，于是每次合并都把 `gorch/*` 分支 rebase 到 `main` 再 ff `main`——施工分支 `codex/voice-fsmn-new-path` 反而永远落后。上一单的 `d1e51eb3 Squash commits from gorch/WO-README` 正是这样合进 `main` 的，随后第二个分支再合过来时 `main` 已有同名文件，直接 add/add。
- **处置**：`scripts/gorch/batch_orchestrator.py` 新增 `_current_branch()`（`git rev-parse --abbrev-ref HEAD`）；`merge()` 加 `target` 参数，默认取当前检出分支，detached HEAD 时 `SystemExit` 明确要求显式传；CLI `merge` 加 `--target` 并在 JSON 输出 `target`。新增 5 条测试（当前分支读取、默认显式传 target、显式覆盖、detached 拒绝、`TARGET` 必须排在 `--branch` 之前）。修好后真实合并：**227.4s、rc=0、rebased:true、removed:true、主线 `50af6549→3d0fc8dd`、报告 4020B 落地**。
- **教训（通用）**：① **位置参数的含义必须按 `--help` 核实，不能按"直觉顺序"填**——`wt merge [TARGET] --branch <源>` 与直觉的 `<源> [TARGET]` 正好相反，写反了不报错、只合错地方；② 任何"合回主线"的自动化都必须显式写目标分支，交给工具的 default 缺省等于把决定权交给了仓库配置；③ 同一个仓库里存在默认分支与工作分支两条链时，先想清楚"施工落在哪条链、发布走哪条链"，否则会长期双写；④ 出现 add/add 冲突先怀疑"两边各自新增了同名文件"，而不是"内容改坏了"。
- **复发**：0

## L75 · "零自研"的口径只写了件级、漏了层级：约 170KB 自建校验层从未进入照搬映射表（2026-11-09）

- **现象**：`docs/plans/gorch-assembly-mapping-20261109.md` §2.2 与结论段写"全部照搬，零自研算法""唯一新增的代码是薄编排层"。治理体检逐项核对后，自建部分远不止"薄编排"——判定交付物能否冻结的整个解析/校验层都是自写，而它从未出现在映射表里。
- **根因**：映射表按**件**登记（wt / ccpm / codex），没有按**层**登记（解析层 / 校验层 / 编排层 / 适配层）。自建的解析器与校验器因为没有第三方来源，天然不在"照搬映射表"的视野里——于是既没被当成"自研需附开源替代排查"的对象（与"任何自写模块开工前必须附开源替代排查结论"的口径冲突），也没被当成"控制主体需机检兜底"的对象。
- **实测差异**：ccpm 原版 16 个脚本，只接了 `lib.sh` 的 `unmet_deps` / `active_conflicts` 两个函数；`validate.sh`（原版校验器）未接；`next.sh`（决定下一单）未接——所以"下一单不会自己起来"这个缺口，是原版本来有、我们没搬。任务发现机制也从原版 `.claude/epics/<数字>.md` 换成批次目录 `<id>.md`，状态词因此三套并存（ccpm `closed/completed/done`、`codex-channel.json` `done/blocked`、`kanban_update.py` `completed/in-progress/not-started`）。
- **自建清单（本次实测，随审计工单 02 一并登记）**：`scripts/gorch_contract.py` 5.2KB（解析器，L1-04 缺陷位）、`scripts/verify-order.py` 46.4KB（校验器，L1-02 缺陷位）、`scripts/audit-work-order.py` 17.7KB、`scripts/freeze-work-order.py` 28.1KB、`scripts/gorch/kanban_update.py` 42.0KB、`scripts/gorch/batch_orchestrator.py` 30.8KB（编排壳）、`scripts/gorch/codex_channel.py` 10.3KB、`src/brain/slot_adapter.py`（三插槽适配）——合计 170KB+，全部 Ultima 自建。
- **教训（通用）**：① 判断"是否自研"要看**层的来源**，不能看"被调用的件有没有上游"——件是开源的，调用它的壳、喂它数据的解析器、判它结果的校验器都可以是自研；② 自建清单必须与照搬清单**并列登记在同一张表**，否则自建层在评审视野里是隐身的，出问题前没人问、出问题后找不到责任人；③ 控制主体（判定交付物能不能冻结的那一层）即使是"薄"的也要有机检兜底，因为它的失效等于门失效；④ "零自研算法"字面成立不等于风险成立——没有算法，不等于没有判断。
- **复发**：0
## L76 · "畸形行"要分两类：没进扫描范围（补范围）和解析不出（必须拒）（2026-11-09）

- **现象**：按 L1-04 收紧 `gorch_contract.py` 时，原判据说"4 类畸形行 4/4 REFUSE"。实际第①类（缩进卡行 `  | T1 s1-... |`）的正确做法是**把它读出来**，不是拒绝——缩进是 Markdown 嵌套表格（标题/列表下的表），拒绝会把合法结构判成非法。真正的畸形只有三类：任务号与卡号无分隔（`T2s1-...`）、门 ID 前缀冒充（`ACC-1x`）、门 ID 无编号（`ACC-X`）。
- **根因**：把"没被扫到"和"扫到但读不出"合成一个词。前者是**范围问题**（块收集条件太窄），后者是**解析问题**（正则太松或太严）。两类修法相反：一类要放宽收集，一类要收紧匹配；混为一谈就会用错方向。
- **连带查出**：14 份真实文档里 **0 份含 `ACC` 字样**——`freeze-work-order.py:388` 的 `if gate_ids and (...)` 意味着"卡没有判据表时直接跳过每门必审"。也就是说判据门的**判据表存在性**从来没被门管过，解析器修好了也管不到这一层。
- **教训（通用）**：① 修解析器前先问"这一行是被漏掉还是被读错"，两者的修法相反；② 判据表"能解析"与"存在"是两个判据，必须各配一条机检；③ 验证收紧是否误伤，最省成本的办法是 `git show HEAD:<file>` 取旧源码在同一批真实样本上并排跑，而不是只跑合成用例；④ 第三方脚本在本地跑不起来时（`next.sh` 的 `list_task_files()` 只认 `.claude/epics/<纯数字>.md`），"接它"的正确含义是接它的**判定语义**（调它依赖的原函数），不是抄它的脚本文本。
- **复发**：0
## L77 · cygwin 的 fork 噪声被当成"判定失败"，一条 warning 能拦下整批派发（2026-11-09）

- **现象**：G-ORCH 双卡并发批次跑通后跑全量，`tests/test_gorch_batch_orchestrator.py` 1 failed、`tests/test_verify_order.py` 7 errors。报错串不是断言失败，而是 `lib.sh: fork: retry: Resource temporarily unavailable`、`child_copy: cygheap read copy failed`、`bash dofork: child -1: forked process ... died unexpectedly`。同样这 8 条**逐条单跑全部 PASS**（冲突用例 6.18s 过、untracked 写入域用例 4.62s 过）。
- **根因**：`scripts/gorch/batch_orchestrator.py` 的 `gate_check` 里写着 `if r.stderr.strip(): raise SystemExit('ccpm 判定出现错误输出 ...')`——把"bash 往 stderr 输出了任何东西"当成"判定逻辑失败"。而 cygwin 在连续 fork 抖动时就会往 stderr 写这种噪声，真正的判定结果（STATUS / UNMET / CONFLICTS 三个 printf）其实完好无损。于是判据是假的坏、派发被真的停。
- **处置**：本轮登记为缺口（报告 §七 第 9 条），未修。建议改成——以 `returncode` 为唯一契约；`stderr` 只在 `returncode != 0` 时作为附加诊断信息；对 `fork: retry` / `cygheap` / `dofork` 这类已知 cygwin 噪声置白名单。
- **收口与二次踩坑（2026-11-09 同日）**：第一版按上述建议只删了 stderr 判定、留 `stderr_diag` 纯诊断，**被 Codex 第二轮审计判定为新开的漏口**。原因是执行串是 `printf 'STATUS:%s' "$(frontmatter_field …)"` 这种命令替换——函数内部的失败（`grep: Permission denied` / `No such file`）**不会变成外层退出码**，于是 `CONFLICTS:` 空成"无冲突"、rc 仍是 0、三标记仍齐，有冲突的卡被判可开工。审计当轮实测复现了 `outer_rc=0` + `grep: other.md: Permission denied` 的组合。最终收口为双向判定：bash 串加 `set -o pipefail` 且三函数先各自赋值、失败即 `exit 71/72/73`；stderr 走白名单——只放行 cygwin 噪声（`fork: retry`/`cygheap`/`dofork`/`child_copy`/`Resource temporarily unavailable`/`^\s*\d+\s*[main]`），其余任何一行仍 `SystemExit`。
- **教训（通用）**：① **"stderr 非空"不等于"失败"**。exit code 才是契约，stderr 是诊断通道；把诊断通道当契约会造出假阴性，而假阴性在 fail-closed 系统里表现为"整批不动"——系统看起来是"正常地什么都没做"，比假阳性难发现得多。② Windows 上依赖 bash fork 的测试套，全量连跑数百次必撞 cygwin fork 受限；判"逻辑坏没坏"必须用**单条重跑**，不能拿全量结果直接定性。③ 全量结果必须分类报出（稳定红 / 环境性失败 / 通过），合成一个数字会让人以为代码坏了。
- **补充教训（通用）**：① **放宽一条 fail-closed 判据前，必须先证明"被放宽的那类输出不会携带真实失败"**。这里的反例就是命令替换：`printf "$(cmd)"` 的退出码只反映 printf，`cmd` 内部报错全被吞。凡是用 `$( … )` 拼判定的地方，都要先补 `pipefail` + 显式传递失败码，再谈放宽。② "噪声"必须**白名单枚举**，不能"删掉整个 stderr 判定"——白名单让未知情况继续 fail-closed，黑名单/全删会让未知情况 fail-open。③ 审计提的"降低证据强度"与"测试没钉住挂载点"是两类不同缺陷：前者是话说过头，后者是删掉被测代码测试仍绿；只测 helper 不测主流程等于没测。
- **复发**：0
## L78 · 每 5 分钟连闪 6 个黑窗：为了读一个 pid 的启动时间，起了 6 个 PowerShell 进程（2026-11-09）

- **现象**：屏幕上每隔几分钟就连续闪出 6 个控制台窗口，反复不断。看起来像有任务在周期性派发。
- **误判过程（值得记）**：① 先猜"我的 G-ORCH 批次还在跑"——普查显示当前无 `bash`/`codex`/`wt` 存活，批次早已结束；② 再查 6 个常驻 `conhost.exe`，逐个反查父进程，结果是 ArmouryCrate / ollama / verge-mihomo / Codex 扩展的 cmd / agent_server / 我自己的 shell——全是长驻宿主，不是"新弹出"；③ 90 秒采样一无所获（周期比采样窗口长，直接漏掉）。**只有把采样拉到 330 秒覆盖完整 5 分钟周期，才在 19:36:04 抓到真凶。**
- **根因**：`scripts/tracker-live.py` 的 `process_start()` 为了取一个 pid 的启动时间，起一个完整 PowerShell：

  ```python
  subprocess.check_output(["powershell", "-NoProfile", "-Command", f"$p=Get-Process -Id {pid} ..."])
  ```

  而刷新逻辑是 `for it in items[:6]: it["alive"] = alive(it["pid"], ...)`——**固定最近 6 条，每条一次调用**。脚本由计划任务 `UltimaAgentTrackerLive` 每 5 分钟拉起（repeat `PT5M`），三个条件叠起来就是"每隔几分钟连续 6 个窗口"。这些 `powershell.exe` 都没有 `-WindowStyle Hidden`、也没有 `CREATE_NO_WINDOW`，于是每次调用都建一个 conhost。
- **处置**：`process_start()` 改为直接调 kernel32（`OpenProcess` + `GetProcessTimes` 读 FILETIME），零子进程、零窗口，顺带把每轮 6 次 × 几百毫秒的进程启动开销也去掉了；算式 `ticks/1e7 - 11644473600` 得 UTC 再转 CST，与原口径一致。同一类缺陷一起收：`batch_orchestrator.py` 7 处 `subprocess.run/Popen`（bash / wt / git）加 `creationflags=_NO_WINDOW`，`kanban_update.py:135` 的看板刷新 `Popen` 加 `CREATE_NO_WINDOW`。验证：三文件 `py_compile` 通过、`test_conflict_blocked_when_other_in_progress` 单条 1.75s 通过、`tracker-live.py` 真跑一次 rc=0 且 `live-data.js` 正常更新（判定结果正确：已退出的 pid 判 `running:false`）。
- **教训（通用）**：① **为了读一个字段而启动一个完整 shell 进程，代价是几百毫秒加一个窗口**——本机能用 API 直接读的信息（进程创建时间、文件属性、服务状态），不要绕道 shell；② 排查"是不是我造成的"必须做到**子进程 + 父进程链 + 时间戳**三要素，只看进程名会漏掉"父进程已经退出、只剩宿主"的情况；③ 周期性的问题，**采样窗口必须 ≥ 一个完整周期**，否则连续采样也永远看不到，反而得出"没有周期性进程"的错误结论；④ 在自己 shell 里执行 `Get-Command powershell` 找不到，不等于计划任务里也找不到——计划任务由 svchost 拉起，PATH 是系统 PATH，环境不同；判断"这个调用会不会弹窗"要去目标环境实测。
- **复发**：1
## L79 · 收紧三处判据时踩到的两类坑：Edit 吃换行、mtime 假“最新”（2026-11-09）

- **背景**：第三轮按审计清单收紧三处判据——gate 三标记“各出现且仅一次 + 禁多余行”、`find_done_tasks` 只认每任务最新一条真实记录、执行段用 `git status --porcelain` 基线快照只认“相对基线的新增改动”。
- **坑 1（工具层）：Edit 吃掉换行 → SyntaxError，53 个用例 collect 就 ERROR。** 在 argparse 段替换时 old_string 未带行尾换行、new_string 又接了新内容，结果两行被拼成一行（`...（只搬不解析）')    b.add_argument(...)`）。pytest 报 `17 passed, 53 errors`，看着像大面积破坏，实际只是一处语法错误。处置：`python -m py_compile` 直接指到 791 行，补回换行即恢复。
  **教训**：批量 Edit 之后、跑测试之前先对每个被改文件做 `py_compile`；“大量 ERROR”优先怀疑语法，不要先怀疑逻辑。
- **坑 2（测试层）：mtime 假“最新”。** 新用例本意是“任务 2 先 done、再 blocked（较新）”，给两条记录设了 mtime `1_700_000_000` / `1_700_000_100`（2023 年）。但任务 2 的 done 记录是 `write_run` 刚建的、mtime 是真实的 2026 年，比人工设的值大得多 → “最新”实际是 done，用例假红。处置：三条记录统一显式 `os.utime`。
  **教训**：用 mtime 造“新旧关系”时，必须把参与比较的**每一条**都显式赋值；只要有一条是新建文件，它天然就是“最新”。
- **本轮收紧的取舍（留档，供审计对照）**：
  ① `find_done_tasks` 从“跳过 blocked 找 done”改为“只认最新一条真实记录”——旧语义会把一次失败的执行当成果合并，属“造错误结果”级缺陷，“失败后沿用上次成功”的运营习惯不值得保留。
  ② `clean` 保持默认严格，只开一道有名字的门 `--no-change-allowed`（批次路径从卡 frontmatter 逐卡透传）——纯验证卡确实不改仓库，但“整批放行”会连带放过真该产出的卡。
  ③ 基线快照的已知弱点如实留档：porcelain **行集合**相减，同一文件执行前后都是 ` M` 且内容继续变化时相减为空、会误杀。真正区分需内容哈希，本版没做——这是“宁可误杀不可放过”的有意选择，不是遗漏。
- **全链一条命令首次真跑（`batch_orchestrator.py run`）**：两卡并发 → 两 commit 合入 → `stopped_at=done`。一个易被误读的点：`cleanup` 两卡都报“worktree 已不存在”，看似清理失败，实际是 `wt merge` 在合并时已自行回收 worktree/分支，`cleanup` 只是走了“已不存在即跳过”的既定分支。**不要把这条 skipped 读成缺陷**——判断清理是否真发生，看 `git branch --list` 与主线 commit，不要看 `removed` 是否为空。
- **未覆盖**：冲突形态的全链（`run` 遇 CONFLICT 停 + 保现场）只有单测，没真跑；`wt remove` 超时回读在本轮真跑里没被触发（`wt merge` 先回收了）。
- **复发**：0
## L80 · 第四轮闭环：批量文本替换打偏、Edit 吃换行复发、判据自身被自己的测试揭穿（2026-11-09）

- **背景**：按第三轮 Codex 审计的 10 条 fail-open 逐条修（提交 `2a446b9a`），执行段改内容级指纹 + 基线阻断，编排段 `run_all` 整段重写为七终态 + invocation 绑定。收尾时踩到三个坑，都属于"改法本身有问题"而不是代码逻辑。
- **坑 1（工具层）：用 `str.replace` 按一行字面值给测试补断言，打偏到另一条用例。** 同一行 `assert 'Permission denied' in str(ei.value)` 在两个用例里都存在（旧用例 `test_real_stderr_error_with_intact_markers_fails_closed` 与本轮新用例 `test_gate_check_rejects_error_after_200_chars`），`replace` 命中第一条，于是"共 2 行真错误"这条断言被塞进只造 1 行 stderr 的旧用例 → 旧用例假红。
  **教训**：改测试断言不能用"某一行文本"当锚点，锚点必须是**用例名 + 该用例独有的一行**；批量替换后必须看一眼 `git diff` 落在哪个函数里，再看测试结果。
- **坑 2（工具层）：Edit 在替换 `def` 行时把 docstring 首行吃掉。** old_string 取了「`def merge(...)` + docstring 首行」，new_string 只回写了 `def merge(...)`——docstring 起始的 `"""` 丢失，函数体变成裸字符串，`py_compile` 立刻报错。这是 L79 坑 1 的复发（同一类：old/new 结构不对称）。
  **教训**：Edit 的 old/new **必须行数与结构对称**；要在某个 `def` 前插新函数，就用「`def` 行」当锚点、把新函数完整写在 old_string 里再回写，或直接分成两次 Edit（先插函数、后改函数体）。批量 Edit 之后 `py_compile` 是硬性动作，不是可选动作。
- **坑 3（实现层）：判据自己暴露了判据不够。** 我按审计 #2 把 stderr 改成"全量逐行分类、只展示首条"，新用例 `test_gate_check_rejects_error_after_200_chars` 用了「噪声行 + 250 个 x 的垃圾行 + `fatal: Permission denied`」，断言 `Permission denied` 必须可见——结果失败：首条真错误是那行 x。这条用例证明"只贴首条"仍会遮住真错误，于是实现改为**前 3 行拼接 + 共 N 行真错误计数**，用例才通过。
  **教训**：写"错误必须可见"的用例，输入里要**故意放垃圾行在真错误之前**；只造一行 stderr 的用例永远证明不了"截断不会遮住真错误"。
- **自查另补的一处（未进审计清单）**：`wt merge` 的 JSON 里 branch/target 可能写成 `refs/heads/x`，而本轮新加的一致性校验用裸字符串比对 → 会把"合成功、只是写法不同"判成目标不符并整批 `SystemExit`。已加 `_norm_ref` 归一化再比。这类"新加的严格校验自己造成误杀"必须在同一轮内自查掉，否则就是把 fail-open 修成 fail-closed 误杀。
- **验证**：`py_compile` 两模块通过；两 gorch 测试文件 `90 passed in 37.57s`（补 `_norm_ref` 后 batch 68 passed 单独复验）；提交 `2a446b9a` 已推远端并打 tag `gorch-r4-failopen-closeout-20261109`。
- **仍未闭合**：八跳第 4 跳未进 `run_all`；冲突形态全链未真跑；修复后未重跑全链真跑；`main` 与工作分支未合流。
- **复发**：坑 2 是 L79 坑 1 的同类复发