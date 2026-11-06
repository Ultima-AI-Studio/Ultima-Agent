# E02 精确 IPv6 导入兼容补修：准备通过

原工单 wo-ultimaagent-20261101-0021，T2。当前状态：离线修复与独立准备审查 PASS；新的完整接线验证尚未运行。E01 同候选固定样本 3/3、E03 三正一负通过记录保留，E02 真实研究和 T2 仍未通过。模型继续只用当前社区 8B，产品候选仍为 269aca511d88412dbb9c15d23911138469a37aa2。

## 实际改动

已确认原 SDK 依赖 urllib3 在首次导入时调用 _has_ipv6("::1")。新的验证 profile 只允许固定源码、真实函数和模块初始化调用链中的 AF_INET6 / SOCK_STREAM / protocol 0 创建，随后允许同一 socket 一次绑定到 (::1, 0)。其他来源、地址、端口、重复创建/绑定、connect 等仍拒绝并留下记录；未完成关闭不能判为干净退出。SDK/vendor 和产品源码未改。

保留外部诊断中有效的 SDK 事件 JSON 键序修正和写入/读回事实。外部包 c794f6fd-3c87-4965-a612-4617d9f64783 虽有机械 PASS，但执行者自审、外层清单 8 项漂移，不能追认独立先审或计作 E02 研究验收。71 份原件已逐项快照核对；外部报告承认删除过早期离线失败目录，本次只记录缺口，不声称已恢复。新的 RED 和全部失败记录均保留。

## 验证和审查

- profile 584/584，原 566 个测试身份全部保留，新增 18 项精确探测检查；其中两条原宽泛例外测试按精确契约更新。
- 根入口 89/89，原测试身份及 275/310/315 秒截止、保护身份和清理规则保留。合计 673 项，定向子集不重复计数。
- RED 真实暴露 16 项缺口；全新进程的原 urllib3 探测验证关闭前不干净、关闭后干净。原 SDK worker/reader 两条真实冷导入回归保留。
- 独立准备审查：PASS，报告 H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-exact-probe-20261106\review\independent-preparation-review.json，SHA-256 a3e17eafda990bb30284788fa962c1ff899563227b66f278252b80d373ded576。
- entry manifest：d047dae29045fe6c0b32777d7212682cc78978a90bc0732e4b56f9326322c8bf，47 个绑定。
- profile 依赖清单：e15587c5a6d2229dc17e40b0ae8b24ed631de8ab69ceb9461fb5a07d7cb69e7b，1499 个绑定，包含安装版本 urllib3 的 36 个 Python 源文件。
- 稳定准备包 manifest：9ac00c1e1624790974df4eef81d87fe60a3c97c8f6814e1e466a6da52b8089eb，126 个成员；审查、发布、运行结果与缓存另存，未改封存包。独审后逐项读回零漂移。

## 下一例与授权边界

具体命令和范围见 H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-exact-probe-20261106\execution-proposal.md。下一例保留原题、四来源、零推理 MockTransport、限定 SSRF DNS、原截止及七个保护身份核验；不操作 UI、音频或服务。仅一例，失败不重试，随后一次只读独立结果复核。当前候选尚无 release/runs，实际调用和结果复核分配均为 0。

用户 call_c6b188dbc9514611ad330bb3b8829619 所授权的一例已用于旧候选 run 726b5883-f57c-4693-899e-17c9d1719b22，该例 FAIL 且独立失败保全复核已完成。本次准备没有复用该单例或外部诊断分配。下一次完整接线验证需新的明确分配。

零推理通过也只证明接线，不能代替当前 8B 的真实研究与真实联网验收。T3—T5 和 Owner 门不提前放行。

本地准备 tag：ultimaagent-t2-e02-source13-exact-probe-ready-20261106。项目及 UltimaDocs 镜像将按同一文本提交并读回。远端 push 仍受此前自动审批 blocked by policy 阻断，本轮没有重试或改用其他通道。
