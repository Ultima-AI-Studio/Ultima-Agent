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
