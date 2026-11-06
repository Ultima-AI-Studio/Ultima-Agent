# E02 SDK 冷导入补修与单例结果

当前状态：准备 PASS，实际单例尚未开始。用户 call_c6b188dbc9514611ad330bb3b8829619 已授权本次补修、必要独审，以及独审通过后单次零推理验证和一次独立结果复核。E02 真实研究与 T2 未通过。

## 本次修复

profile 仅精确放行 socket.gethostname 本机元数据读取；其余审计、原题四来源、SDK 真实类型与关闭、275/310/315 秒截止保持。根入口只改固定目录与 profile 摘要。原 SDK/vendor 和产品候选 269aca5 不改，当前 8B 不换。

真实 worker/reader 冷进程在 RED 中均复现原 hostname 拒绝，GREEN 中均完成真实 Ollama/HTTPX 构造与关闭，观察到的导入发送次数为零。探针使用合成 admission，仅验证初始化，不能冒充实际 profile。保留两轮 RED/GREEN 和最初 88/89 路径绑定失败；修正为原 Context.pins 路径派生后最终回归通过。

## 验证与独审

- profile：561/561，原 557 身份全部保留，新增 2 个真实冷导入和 2 个精确事件负例。
- 根入口：89/89，原测试身份和根入口语义保留；540 个历史绑定无变化。
- 独立准备：PASS。报告 H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-cold-import-20261106\review\independent-preparation-review.json，SHA-256 cc00876f08fca31496b80bcf22381e31fa1c7ed7720efab383998f7483f5d466。
- entry manifest：6e07ab69f0a61896730608dac9f0dafc75a986514e028deb52a28c32b5732fb6；44 个绑定。
- 封存包 manifest：21caeaff009e9079ff80ba39eaa1505dfa49c7458c5faee46392e4136fbadbd1；196 个文件。独审后不重封，新增报告和发布记录独立登记。

## 下一动作与边界

按 H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-cold-import-20261106\execution-proposal.md 只读核验七个保护进程；核验通过后执行已授权的一例原资料零推理接线验证。允许原正常 SSRF 的 raw.githubusercontent.com 限定 DNS；不调用模型、资料 HTTP、11434、UI、音频或服务，不重试。完成后一次独立结果复核。

旧失败 run 6e8e644e-962a-4afe-83ed-e488b6da5fc1 保持 FAIL。本次零推理即使通过也不计入 E02 真实研究三轮。E01 三轮、E03 三正一负已通过；T2 和后续/Owner 门仍未过。

本地准备 tag：ultimaagent-t2-e02-source13-cold-import-ready-20261106。远端同步仍保留此前自动审批 blocked by policy；本轮没有重试 push。
