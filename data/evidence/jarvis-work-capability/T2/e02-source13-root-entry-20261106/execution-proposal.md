# E02 原资料单例零推理接线验证提案

本提案仅在当前入口独立准备审查与 root 处置通过、用户明确分配一次运行及一次只读结果复核后执行。准备记录、E01 已消费的授权和离线测试均不提供本次运行权限。

当前状态：首轮独审为 `NEEDS_FIXES`，指出清理余量不足。新差异已进入一次有界修复；该独审不覆盖修复后的哈希。本提案保持关闭，不能由原审查或 root 自测签发实际运行权限。

目标是验证原题、原四来源、真实 SDK 写入与独立读回在当前 source13 候选上能够接通。冻结候选为 `269aca511d88412dbb9c15d23911138469a37aa2`，配置仅接受当前 `qwen3-8b-uncensored` 及摘要 `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`。本例由已审查的原 profile 提供零推理协议响应，不调用模型，也不证明 8B 已会研究。

- 原题 774 字节，SHA-256 `d359dcde318278823ad1e9c48b70c604f0d614152c0b0ec26b88ca310821f61e`；原四来源 corpus SHA-256 `9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002`。不替换题目、语料、人设、扫描器或 SDK 写入机制。
- 一次 root 分配、一次原 `run_profile`、一个全新 reader、两次原 `RootControls.readback`；失败不重试。产物只能落在本根 `runs/<run_id>/worker/case`，协议产物为 `research.md`。不直接写入产品默认资料目录。
- 第一段代码记录唯一 monotonic origin。工作原截止 275 秒，profile 清理 310 秒，worker/reader 实际退出及父进程最终验证 315 秒，不续期。父进程另在 275 秒前观察原服务返回文件、310 秒内观察完整 profile 结果；后一证据比只信 worker 时间更保守，可能拒绝清理已及时完成但封存文件晚出现的运行。
- R1 修复另在启动、身份确认和每次等待前预留原 Owned 清理所需余量：按已登记成员的原 15 秒 CIM 调用、每成员完整 10 秒终止准入、每启动器 2 秒等待、最终保护观察及文件封存计算。新增角色还预留三次原 CIM 启动/身份观察。典型两个成员的等待余量为 132 秒，四个成员为 214 秒；因此等待可能分别在原 origin 的约 183 秒、101 秒前结束，新 reader 启动会更早拒绝。它保留原最大时限但缩短可用等待窗口，可能使本来内部及时的运行失败，不能把它宣传成享有完整 275／310 秒消费窗口。未知树、OS 调用或文件 I/O 异常仍按失败记录，不承诺所有故障都能清理成功。
- 保留原正常 SSRF 分支：允许为 `raw.githubusercontent.com` 做受限 DNS 解析。禁止资料 HTTP、真实 11434 请求、模型推理、UI、音频和服务变更。**不能把本例称为完全无网络**；原生 DNS/缓存/网络包计数继续为未知，不用 Python 层记录冒充 OS 证明。
- 复用 E01 已接受的 Owned 启动/清理和七个保护角色核对。保存的保护基线仍须在执行时由原生身份、FILETIME、父 PID、命令摘要逐一重新通过；旧快照不证明当前运行状态。仅清理本例由该 helper 正式登记的精确身份，不处理未知或生产成员。
- worker HELLO 只作比较。父进程先从 Owned/CIM 验证实际 worker/reader，再保留同一原生进程的只读句柄观察退出码；venv 启动器成功不等于实际 worker 成功。
- 外层机械成功只产生 `PENDING_RESULT_REVIEW`，需另一次只读独立结果复核。即便通过，也不计入 E02 真实 8B 研究三轮或真实联网事实验收；E02/T2/T3–T5/Owner 原门不变。

授权到达后由 root 新建短时 `release/user-approval.json` 与 `release/release.json`，绑定当前 entry manifest、独审、run_id 和 nonce；独占 `release/consumed.json` 消费一次。当前包不附可用授权模板或成功分配。

固定启动命令（尚未执行）：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -I -B -X utf8 'H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-root-entry-20261106\code\entry.py'
```

无需暂停键鼠。本例无窗口、语音或模型操作。若受保护身份、环境或短时授权不匹配，入口拒绝；该运行额度不会自动续发。
