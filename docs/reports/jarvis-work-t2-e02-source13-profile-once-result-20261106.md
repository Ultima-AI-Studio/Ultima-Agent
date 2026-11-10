# E02 原资料零推理接线单例结果

原单 `wo-ultimaagent-20261101-0021`，T2。北京时间 2026-11-06 18:58，用户授权的单次接线验证已执行并结束：**FAIL**，约 **9.04 秒**，没有重试。独立结果复核为 **PASS_FAILED_RESULT_PRESERVATION**，仅确认失败证据与解释可信，不能把本例改记为通过。

## 实际执行与原因

- run_id：`6e8e644e-962a-4afe-83ed-e488b6da5fc1`。root 入口 1 次、原 `run_profile` 1 次、reader 0 次、独立结果复核 1 次；本授权的运行与复核额度均已用完。
- 父进程错误：`Worker exited before complete independent progress`。worker 原始栈显示：Ollama 包导入时建立默认 `Client()`，User-Agent 调用 `platform.machine()`，Windows `platform.uname()` 读取 `socket.gethostname()`，被原 `WorkerAudit` 的广泛 socket 事件拒绝规则阻断。
- 失败发生在原 `private_scope` 尚未 yield 的初始化阶段。`run_profile` 此时原样抛出异常，因此没有 `service-first-result.json`、`profile-first-result.json`、reader 或 `research.md`。研究提交和模型推理没有到达；没有完整 profile 计数收据，不能把路径判断写成 OS 网络测量。
- 本例没有证明 8B 研究能力，也没有证明 SDK 研究写入与读回已接通。产品 source13 候选与原 profile/SDK、38 项运行输入字节均保持；此次不是 HELLO 清理余量再次不足。

## 清理、保护身份和限制

原入口清理记录 PASS：两个 worker 成员和一个只观察的控制台均消失，日志已关闭。root 后续只读核验确认这三个原身份及 root 原生身份均已不在；七个保护进程的原生创建时间、程序路径、父 PID 和命令摘要全部匹配。只证明观察时点；不扩大为持续可用、语音声学效果或整台电脑无其他活动。

没有 UI、音频或服务变更，没有模型/研究提交。原生 DNS 次数与 OS 包数未测量，保持未知。本例正常 SSRF 的允许范围原为 `raw.githubusercontent.com` 受限 DNS，但实际在更早的导入阶段退出。

预检曾因辅助脚本把 CIM 创建时间按全精度相等比较而误拒。随后核验发现七个原生身份均匹配，改为复用已审查入口原有的 `snapshot_identity_matches`（最多 20 个 FILETIME tick 的 CIM 精度差），预检通过后才执行唯一实跑。原误拒输出和脚本保留；没有放宽封存入口的生产身份规则。

## 独立复核与证据

证据根：`H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-root-entry-20261106`。

- 原始失败：`runs/6e8e644e-962a-4afe-83ed-e488b6da5fc1/control/terminal.json`、`process/worker.stderr`。
- release/consumed、root 启动与退出、前后核验：`release/`、`execution/`。
- 结果包：`execution/result-manifest.json`，36 项，SHA-256 `8b4be01051fa19d149d21706aeb342464e5ae958ae5356d962e6902e727e644f`。
- 独立结果报告：`review/independent-profile-once-result-review.json`，SHA-256 `6fd6c09b37de9b3ec593c03d23728414ed643fd55c945f617b4f4aaa226d29dd`。reviewer 仅只读审查，没有重跑测试、用例或原生查询。
- root 登记：`execution/result-registration.json`。准备 PASS 和原 89 项离线检查保持其原范围，不能代替本次实际 FAIL。

E01 固定 3/3、E03 同候选三正一负仍保留原通过记录；E02 真实研究、T2 出口、T3–T5 与 Owner 仍未通过。

## 下一步具体范围

见 `docs/plans/jarvis-work-e02-source13-sdk-cold-import-fix-plan-20261106.md`。建议在新隔离候选修复 SDK 冷导入兼容，精确处理本机 hostname 事件，保留其他网络拒绝与原所有权/关闭检查；先增加真实新进程冷导入回归，独立准备复核通过后才分配一次新单例和结果复核。原包及本次失败完整保留，未修改 frozen profile，未开展补修或第二次实跑。

本地项目/镜像 commit 与 tag 见 `execution/result-checkpoint.json`。远端 push 仍受此前自动审批 `blocked by policy` 阻断，本轮未重试或绕过。
