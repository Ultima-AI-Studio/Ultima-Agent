# 工单② W1 独立验收 · 2026-10-21

## 第一轮：只读预检

**U01 独立通过；W1 整体尚未签署。** 审计者 `/root/w1_acceptance`，不是宿主实现执行者。本轮仅核对现有文件及实际窗口截图，没有重新构建、启动或操控窗口、修改实现、停止进程、创建 tag 或代作 Owner 批准。后续正式轮应追加，保留本轮事实。

### U01 / T1 判断

依据 `docs/specs/environment-spec.md` §7.1 的 Owner 已批准阶段拆分，宿主强制开工门为 Windows/Git、SDK 8.0.425 与 WinUI3 真实构建、WebView2 Runtime 初始化/渲染/双向通信。语音和任务引擎产品验收继续在各自工单执行。

| T1 封闭验收 | 独立判断 | 核对事实 |
|---|---|---|
| 九项逐一列名、版本/路径及状态 | PASS | `logs/environment-check-2026-10-21.md` 九行逐项齐全，保留历史失败。 |
| 宿主阶段强制门全部 GREEN | PASS | Windows11 Pro x64 build26200、Git2.55.0.windows.3 有环境检查记录；SDK8.0.425 固定路径及 WinAppSDK1.8.260921001；实际 t2-build.log 0警告/0错误；环境 result.json 真实 probe PASS、Runtime155.0.4283.62、renderedText=rendered、web-received:host-ping；正式宿主 t3-webview.json 另有 initialized/navigationSucceeded=true 及消息往返记录。 |
| 就绪检查表落盘 | PASS | 上述环境检查文件真实存在且已独立读取，非仅任务卡勾选。 |

U01 可以供 W2 跨工单环境门行政收尾引用，无需等待 U04 多DPI或整单W1。这个签署范围是宿主阶段环境门，不扩大为语音产品质量或队列完整验收，也不是本轮重新执行全部九项 smoke。九项历史 GREEN 自述不取代其各自后续产品验收。

### 其他单元与待补证据

| 单元 | 本轮状态与正式复验条件 |
|---|---|
| U02 / T2 | 旧构建日志0警告/0错误；本轮独立查看 `logs/w1-native-2026-10-21T02-26-42-926Z/native-window.png`，实际深色客户区、Ultima Agent 标题及“宿主壳已就绪”文本清晰可见，关闭旧“白色客户区仍未证实”的该次运行缺口。当前后台仍可能改源码，最终源码与产物一致性及最终构建须后续核对。 |
| U03 / T3 | 既有正式宿主证据记录真实 WebView2 初始化、渲染和往返，支持此前功能成立；待最终源码/产物与新运行记录绑定后正式签署。 |
| U04 / T4 | 旧记录只证明144DPI的270物理/180逻辑和真实拖动；卡内 FB-03 要求多DPI下位置不偏移。仍缺真实96及144DPI的内部 DPI/逻辑-物理尺寸/Caption区域/拖动位置保持一致证据，不能以桌面截图缩放或替换数值代替。 |
| U05 / T5 | 旧 final positive exit0、negative exit1、1214窗口样本、既有进程身份13/13保持；这些绑定旧实现。待本次最终源码上重跑正常链、缺Runtime负向、全期窗口观测和进程身份前后回读，确认报告/退出码及产物一致。 |

整单还需逐条核对五任务回执三件套、T↔U映射、build→launch→window→exit总验收、文档登记及实际内部工单tag行政收尾。v0.1-frozen须工单①②完成及Owner版本门，本报告不创建或声称这些已发生。

### 证据固定与限制

`docs/reports/evidence/w1-independent-20261021/round1/` 保存本轮读取的门规格、五卡、环境与旧最终回执、原生截图和SHA-256清单（`result.json`）。截图审阅只确认该帧实际内容，不能据此推断多DPI或持续运行。后台开发未被干预；本轮不采集或输出会话 encrypted reasoning。

第一轮签署：**U01 PASS；W1 PENDING，等待最终构建、DPI与运行证据后追加正式复验。**

## 第二轮前置审查：DPI 新证据（非最终签署）

后台宿主执行仍在进行。本段仅只读审查新代码和已产生证据，未构建、未启动或操控窗口、未修改实现或停止进程；第一轮结论保留。

`MainWindow.xaml.cs` 的显式 `ULTIMA_HOST_DPI_ACCEPTANCE=1` 开关可达 `FloatingBallEvidence.RunAsync` 再到 `DpiAcceptanceEvidence.RunAsync`。测试用真实 `EnumDisplayMonitors/GetMonitorInfoW` 枚举显示器，`AppWindow.Move` 移动实际窗口，`GetDpiForWindow/GetWindowRect` 回读系统值。硬编码 ExpectedTopology 仅是比较期望，不替代实测值；未发现写假DPI或注入WM_DPICHANGED。

`logs/w1-host-resume-20261021T024845Z/t3-dpi-final/t3-dpi-dpi-acceptance.json` 记录PID57644在实际三个显示器为144/96/96 DPI、窗口270/180/180物理像素及180逻辑像素，三个一秒hold和恢复hold均零漂移，violations为空。与代码执行逻辑一致，支持真实跨DPI尺寸与稳定性成立。CaptionRegion是 `SetRegionRects` 成功后应用记录的宽高，不是额外native查询；仍须最终真实鼠标拖动验证区域生效。

`t3-final-build-attempt2` 的 started 指向用户目录SDK，实际build.log记录0警告/0错误，result退出0。首次NuGet失败保留。构建完成02:55:08Z，DPI运行02:55:57Z，时序相容，但目前构建与启动回执没有源码/EXE/DLL哈希和完整运行路径，尚不足以独立证明最终源→构建→运行不可混淆的绑定。最终交付需固定source manifest及产物哈希并与运行路径核对。

前置审查未发现实质代码缺陷；待最终原生显示、真实鼠标、T5正负向及源码产物绑定后继续正式复验。本轮快照及哈希在 `evidence/w1-independent-20261021/round2-preliminary/`。**此段不签署最终W1。**

## 第三轮：正式功能复核与整单收口判定

**最终独立判断：U01–U05 功能验收通过；工单②整体仍 BLOCKED，不签整单完成。** 审计者 `/root/w1_acceptance`。审查与开发分离；本轮未操控UI、未停止任何进程、未创建审批或tag。保留前两轮与第三轮初始快照；最新固定结果在 `evidence/w1-independent-20261021/round3-final/result.json`，时间2026-10-21 03:24:24 UTC。

### 功能门

| 单元 | 独立结论 | 最终依据 |
|---|---|---|
| U01 / T1（EN-01–04） | PASS | 第一轮阶段环境门签署继续有效；九项枚举、状态、报告和历史失败均保留。 |
| U02 / T2（WI-01–04） | PASS | 架构为独立薄宿主，无编排/模型推理业务；正式入口实际构建0警告/0错误；最终原生截图独立查看，深色客户区、标题和中文就绪文本清晰可见。 |
| U03 / T3（WV-01–03） | PASS | `t3-webview`真实Runtime初始化、占位页渲染和web-ready→host-ping→web-received:host-ping；最终源码哈希与审查源码一致。 |
| U04 / T4（FB-01–03） | PASS | 无边框置顶；真实鼠标前后矩形3522,1770→3432,1680，移动(-90,-90)物理像素，03:13:06→03:13:30约24秒保持不变；AltF4后窗口为空。内部真实跨屏144/96/96DPI、270/180/180物理尺寸、180逻辑尺寸、一秒hold与恢复均通过。实际鼠标证明Caption区域可拖动；未声称鼠标跨屏拖动已经专门实测。 |
| U05 / T5（SC-01–03） | PASS（当前正式入口） | 正式交付 `scripts/selfcheck-host-shell.py` 与 `scripts/HostSelfcheck/`，从该入口实跑build→launch→window→正常exit0，报告落盘。WinEvent加进程树枚举仅允许宿主及内部WebView渲染面，意外窗口0；缺Runtime负向真实FAIL/exit1，意外窗口0。旧.ps1不再作为推荐入口，故该历史启动挂起不被冒充新入口通过。 |

最终正向证据：`logs/w1-delivered-selfcheck-verified-path-positive-20261021T0324/`；负向：`logs/w1-delivered-selfcheck-verified-path-negative-20261021T0325/`。我独立重算两套证据source_manifest和artifact_manifest，全部匹配当前文件；source-before与source-after完全一致。两套host-started的actualProcessExecutable均与预定完整路径相同，启动EXE/DLL哈希与当前文件一致，且匹配真实鼠标session：EXE `17ddfedbffc4eb0086e71e46f64e025df3284522df4f47de0c9016b71aa7a107`，DLL `738b8b74803eca8049cbecf4456123999a1f98963354917037d3e90311c811ee`。

第三轮初次bound-positive的actualProcessExecutable=null事实保留在 `round3/`，不将其写成成功的路径读回。后续C#改为QueryFullProcessImageNameW读取真实路径、失败即FAIL，再取得上述新正负向证据。独立重跑 `scripts/tests/test_host_selfcheck_entry.py` 两项监控start/stop故障回归，2/2通过，输出固定于round3-final。测试只启动隔离mock故障，不操控UI。

### 系统清理门：实质阻塞仍存在

旧自检pwsh PID59328、创建身份 `134370250506523457` 仍不能确认退出。03:24:24 UTC我使用同一只读进程句柄独立核对：创建身份相同，GetExitCodeProcess=1、WaitForSingleObject(handle,0)=258（WAIT_TIMEOUT）、退出时间=0。**exit code=1不能在此状态下解释为进程已经终止。** root此前精确身份定向TerminateProcess返回AccessDenied5；本审计没有重试终止、扩大权限或要求重启。

这不推翻当前新入口的完整功能证据，但它是本工单旧尝试产生且尚未清理的资源。不能宣称“本轮全部自建进程均已退出”或整单安全收口。必须取得该同一创建身份进程已signaled/实际退出的独立读回，或由Owner明确批准有范围、有剩余风险记录的清理例外，才能解除这一系统清理门；本报告不代批准例外。无需为此重新开发宿主功能或把所有成功测试再跑一遍。

### 行政门与真实执行状态

实际Codex adapter `tasks/queue/runs/wo-s1-host-shell-20261021T023427316731Z/done.json` 为exit125、receipt_valid=false、state=blocked。本审计的功能判断来源于独立读回，不将该adapter状态改成成功，也不伪造执行器成功回执。

工单总验收中五任务功能及T↔U映射通过。仍需监督端将本轮最终入口/证据追加到五卡三件套、权威清单与队列回执中；尤其T5旧landed-files仍只列.ps1，不应抹去历史，应追加正式.py/C#交付。src/host-shell/README现已同步新入口和阻塞事实。实际Git tag只见 `wo-s1-queue-engine-done`，未见 `wo-s1-host-shell-done`；须系统清理门解除后再完成该工单内部tag等行政收口。v0.1冻结仍属于工单①②完整收口后的Owner门，当前没有本审计批准。

**剩余实质系统阻塞只有旧PID59328清理未闭合；其余为最终证据/三件套、队列状态和内部tag行政收口。功能无新增待修项。最终签署：功能PASS，整单BLOCKED。**
