# 已授权的单次零推理接线验证

依据用户 `call_c6b188dbc9514611ad330bb3b8829619`；本文件不发放 release。新候选准备独审 PASS 后，root 才能按下述顺序执行，禁止用旧包 PASS 替代。

1. 验证当前包和 entry/profile 依赖哈希、产品候选 269aca5、当前 8B 摘要；独审报告必须绑定同一 entry-manifest 和外层 manifest，root gate 必须绑定报告的精确字节。确认原运行证据不变。
2. `verification/profile-once-preflight.py` 仅原生身份与 CIM 只读对照，七个保护身份必须与既有 baseline 一致。沿用原 `snapshot_identity_matches` 的 CIM 精度规则，原生 creation/exe/parent/命令摘要仍精确相同。核对没有同入口进程，实际 codex exec 并发小于三；不把 app-server/exec-server 算作执行器。不调用模型或服务 API。
3. root 根据本次已授权 scope 写一次新 approval、最多 120 秒有效的 release 和一次独占 invocation 记录，使用固定 venv 的 `-I -B -X utf8 code/entry.py`，无参数启动。调用 `verification/execute-profile-once.py` 仅一次；不得复用旧 release/consumed。子进程静默启动；原生成员登记、清理余量、275/310/315 秒最大截止沿用当前入口。
4. 原题、四来源、原 SDK 写入与读回流程；正常 SSRF 允许 `raw.githubusercontent.com` 的限定 DNS。资料 HTTP、实际 11434 请求、模型推理、UI、音频和服务操作均为零授权。最多一例 profile、一个独立 reader 和两次原读回；不合格或失败均结束本次序列，不重试。
5. 实际退出后保存原始 stdout/stderr、terminal、计数/写入/读回证据；`verification/profile-once-postcheck.py` 只读核验保护身份、清理与原绑定。记录的是观测时点，不宣称持续在线或 OS 全局无网络。若原 profile 结果缺失，不能伪造完整计数。
6. 分配本次已授权的一次只读独立结果复核，核对真实输出、引用和来源、原 SDK 写入、新 reader/两次读回、限制及失败。无论 PASS/FAIL 均落盘、镜像和本地 commit/tag。此零推理接线结果不计入 E02 三轮真实研究验收。

冻结产品和旧 B/E 不改，不启动/结束任何保护服务，不换模型。远端 push 保持此前自动审批阻断，未获放行不重试。
