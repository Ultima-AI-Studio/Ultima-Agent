# 阶段验收证据

- work order: `wo-s1-composite-window`
- phase: `T2-text-core-only`
- verdict: `READY_FOR_REVIEW`
- completion: `partial`
- evidence root: `evidence/20261024T085613+0800/`

## 前置与范围

- 最新独立计划背书 `reports/queue-observer/workflow/t2/20261024T003445-84169f240563/endorse-0/review.json` 实读为 `PASS`，只背书本阶段。
- 首轮实现独立复审 `reports/queue-observer/workflow/t2/20261024T003445-84169f240563/audit-1/review.json` 实读为 `REVISE`（2 Important + 2 Minor）；本开发回执只提交四项修复等待新独立复审，不冒充该文件为 PASS。
- T1 接受锚点 `reports/queue-observer/workflow/t1-accepted.json` 的独立结论为 `PASS`、`owner_approval=false`，16 文件源绑定为 `59df00d12438c8cf890cc941398bd68d60d749972a4769fbd28903b956d9397f`。
- `t1-protected-before.json` 与 `t1-protected-after.json`：16/16 逐文件哈希一致，聚合源哈希仍为上述固定值。
- `scope-audit.json`：`src/window` 文件集合仍恰为两个 T2 模块、一个 T2 测试和一个样例；相对首轮审计基线仅两个模块、该测试与 T2 卡发生允许内变化，无 forbidden 或 unexpected 文件。其他写入仅在本 T2 卡目录。

## RED → GREEN 与运行证据

- `red-result.json` 与 `red-test.log`：六个针对首轮复审发现的测试方法真实 RED；记录 26 个 T2 测试中 4 failure、3 error，命中超大整数、高深度转换、高深度渲染、空 `styles`、转换代理项和 renderer 代理项六个入口。
- `window-tests.log`：修复后窗口全量 61/61 通过；旧 `test_a2ui_validator.py` 35 项和 `test_text_core.py` 26 项均真实执行。
- `t1-probe-results.json`：按接受审查的原 91 案例重放，91 项无 unexpected、输入变化 0；旧 35 项 0 failure/0 error。
- `t1-guardrails.log`：exit 0；v0.3 10 项、v0.1 36 项 manifest 无 mismatch；生产 `tasks.json` SHA256 固定；vendor 三 schema 和 LICENSE hash 一致，运行时不依赖网络。
- 同一探针确认旧运行 `wo-s1-composite-window-20261021T053435036433Z` 的 `done.json` hash 不变，`exit_code=125`、`receipt_valid=false`、`state=blocked`，且 `final.json` 仍不存在。

## 转换、渲染与安全

- `result_to_a2ui.py`：只接受严格 JSON 基本类型、object、array；拒绝非字符串 key、非 JSON 类型、NaN/Infinity、循环和超深/超量/超长输入。转换只生成标准 A2UI `Text/Row/Column/List` 扁平邻接表，最后必须通过 T1 `final=True`。
- `offline_renderer.py`：支持集合明确固定为 `Text/Row/Column/List/Card`；仅接受 literal text 与 explicit child。资源、Button action、data binding/template、其他组件、输入 style 与 weight 均以确定性错误拒绝。
- `review-regressions.json`：默认 4301 位整数返回 `max_text_exceeded`，合法放宽文字限额后可安全转换；1050 层列表转换与 1050 层 Card 渲染在 `max_depth=2000` 下实际通过且输入不变；空 `styles` 返回 `unsupported_style`；转换文字/key及 renderer 文字/title 中的代理项均返回 `invalid_unicode`，合法 emoji HTML 可 UTF-8 编码。
- 新测试实际调用两个模块、解析 A2UI 组件树和 HTML，并以运行时包装确认转换与 renderer 均调用 T1 `validate_batch(..., final=True)`；核对正负向、转义、CSP、无 active tag/外部属性/CSS 获取、网络调用阻断和输入不变，不以源码关键词断言代替运行。
- `brain-empty-batch.json` 与 `brain-empty-render.html`：现有 Brain 实际读取空生产队列后生成的批次与静态 HTML。`t2-verification.json` 记录 DOM 解析、安全检查和 `tasks.json` 前后同哈希。

## 保留门

本阶段开发自检通过但尚待新的独立复审，没有勾选任务卡任何整项 acceptance。
未验收：CR-01 完整域、CR-02
WinUI/WebView2 原生窗口、CR-03 ≥90% 覆盖截图、CR-04 窗口+语音双通道真机、
T3 主题/悬浮球与语音四 IO、W5、Owner 审批、发布/tag 和 v0.4 冻结。
