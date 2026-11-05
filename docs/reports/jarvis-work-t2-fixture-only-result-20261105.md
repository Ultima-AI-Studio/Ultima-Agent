# UltimaAgent T2：单次夹具诊断完成，未复现文本清空

日期：2026-11-05；原工单：`wo-ultimaagent-20261101-0021`。

**已按用户授权完成独审及唯一一次夹具诊断。诊断证据完整，主测试文本未变化；原先间歇性清空的原因仍未确定，E03/T2 尚未通过。** 当前候选 `7975e477665c02820fa235b73d203718bd33b2c9`、当前社区 8B 与全部历史失败保持原归属。

本次授权为 `call_8a6fef41fb9445a988111284dd48982b` 的“授权独审，通过后运行一次夹具诊断”。原 R1 独审发现 `FIXTURE-SOURCE-ENTRY-01`：旧 controller 的来源检查会读取本包没有的 `code/inputs.json`。原包没有运行。新建 fix1，仅把桥接层前后两处来源检查改接现存的固定候选 guard；本包依赖仍由自己的 manifest 验证。新增三例先复现失败，修复后共 **90 项离线测试通过**；实际候选 guard 的只读检查通过。同一 reviewer 对该缺陷及新增风险复核 **PASS**。

2026-11-05 **17:56:09—17:56:20（北京时间）**完成一次 `fixture-origin-01`。从准入后到采集、清理、边界和审计完成的计时为 **10.704 秒**，未触发 30 秒停止请求，满足诊断的 60 秒完成条件。该计时不包含准入前的只读来源与保护检查。

| 检查 | 本次证据 |
| --- | --- |
| 主测试文本 | 初始化及基线均为 41 UTF-16 单位，SHA-256 `69867afb7063d8fa99fbe714dbe7f9c75f0272b47b2ca288b6e633b80a6a379d`；选区仍为 0—41 |
| 第二测试文本 | 初始化及基线均为 39 UTF-16 单位，哈希一致，选区 0—0 |
| 输入来源记录 | 完整起止；两条探针和两条 `0x0282` 通知；没有 `EM_REPLACESEL`，旧分类器记录键盘/IME 输入事件为 0 |
| 来源解释 | API 调用可用，但记录的 `origin_id=0/unavailable`；未识别发送进程，不能据此断言输入由谁产生 |
| 清理 | PASS；四条自有/观察进程身份记录均已退出，另行 CIM 回读仍无残留 |
| 保护边界 | PASS；七个保护角色的 PID、创建时间、映像、父进程及命令哈希一致 |
| 语音状态 | 官方入口回读 ready、fresh、worker_ready、instance_lock_held 均为 true，原 run_id 与 PID 保持 |
| 调用范围 | 本诊断的产品 CLI、模型和音频操作均为 0；未测量共享模型服务的其他活动 |
| 额度 | 1/1 已消费，剩余 0，不重试，无产品验收分 |

Root 直接对照实际 fixture 身份、初始化读回、原始基线、输入来源日志和终态，独立于测试日志完成回读。这里的“独立于测试日志”不表示新增了第二个 reviewer；现场结果回读由 Root 完成。两个原始观察文本只留在本机 Git 忽略的 `actual/`，对外记录保留长度、哈希、选区、进程身份和消息元数据。

原 R31 曾出现同一控件从 41 字符变空并收到 `EM_REPLACESEL`；本次未出现该消息且文本未变。这只能说明该异常不是本次夹具启动和观察的必然结果。单次未复现不能证明问题已修复、不能排除时序或输入干扰，也不能回推用户当时是否打字。R31 的输入来源继续记为 UNKNOWN。

后续不再盲改夹具或重复消耗诊断轮次。下一步是准备**当前候选 E03 round1 的正式单例验收包**，沿用已审查的输入来源记录、前台/选区与来源检查，保留原 60 秒门和失败即停规则。正式用例必须重新满足其自身审查、实际用例 authority 和保护/WIP 前置条件；本次 fixture-only 授权不覆盖产品运行。顺序仍为 E03 三轮正例及负例 → 同候选 E01 → 当前 8B 的 E02 → T2 出口后 T3—T5/Owner。当前候选正例 0、负例 0，T2 BLOCKED。

证据根：`H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e03-fixture-only-diagnostic-20261105-r1-fix1`。

- fix1 manifest：`c0af805df895516a6dcdae086668b3ca1095707939f1e3500957c047837eb4fb`。
- 独审闭合：`independent-review-closure.json`，SHA-256 `d3f35d982c613f18d1efa0e88b7076afba899efd26d8ee7dc55d26aa6d9b2f33`。
- 实际终态：`actual/fixture-origin-01/terminal.json`，SHA-256 `aa9f2a29de69e2782ef5ec1dbabfc69077933711ec71ffe14b691bc867d36f25`；不含原文的逐字节副本为 `verification/diagnostic-terminal-readback.json`。
- 交叉回读：`verification/diagnostic-readback.json`；保护与语音回读：`verification/final-protected-readback.json`。
- 原 R1 的 manifest `c9fa33fa…c7f7b9f4` 及 NEEDS_FIXES、原 R31 的失败终态均未覆盖。
