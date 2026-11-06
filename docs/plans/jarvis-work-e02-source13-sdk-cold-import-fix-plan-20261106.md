# E02 原 SDK 冷启动兼容补修提案

状态：用户通过 `call_c6b188dbc9514611ad330bb3b8829619` 明确授权补修、真实冷导入回归、必要独立准备复核，并仅在复核通过后进行一次新零推理接线验证及一次独立结果复核。原单 `wo-ultimaagent-20261101-0021`，T2；不重置任何旧失败。准备通过前不签发实际 release。

## 已确认的问题

2026-11-06 的单次原题、原四来源零推理接线验证，run `6e8e644e-962a-4afe-83ed-e488b6da5fc1`，实际 FAIL，root 耗时约 9.04 秒。worker 调用了原 `run_profile`，但在 `private_scope` 进入 `own_ollama_types` 时失败；没有服务研究结果、profile 结果、reader 或 `research.md`。

调用栈为原 Ollama 包导入 → 默认 `Client()` → User-Agent 的 `platform.machine()` → Windows `platform.uname()` → `socket.gethostname()` → `WorkerAudit` 拒绝。该事件读取本机名称；本次源代码路径尚未走到研究提交或模型推理。不能把这一结论扩大为对整个 OS 网络流量的测量。

失败来源：`data/evidence/jarvis-work-capability/T2/e02-source13-root-entry-20261106/runs/6e8e644e-962a-4afe-83ed-e488b6da5fc1/process/worker.stderr`。原 guard 在 B 包 `profile-preparation/profile.py:180`，`own_ollama_types` 在约 195–243 行，`run_profile` 在约 2067 行。封存入口和 profile 未修改；本次不是 HELLO 清理余量再次不足。

## 最小改动与固定边界

1. 保留现有 B/E 包、manifest、单次 release/consumed、失败运行及独审报告；新的修复候选使用独立目录和新输入绑定。产品候选仍为 `269aca511d88412dbb9c15d23911138469a37aa2`，仅当前 8B 配置，SDK/vendor 不改。
2. 在新 profile 候选中精确处理 `socket.gethostname` 这一 SDK 导入所需的本机元数据事件。保持其他 socket/subprocess 拒绝、原受限 `getaddrinfo` 域名规则、HTTPX 真实类型/所有权/关闭核验、固定题目、四来源、原 scanner/writer、单次消费和 275/310/315 秒最大截止。
3. 新根入口仅做接入新 profile 所必需的固定路径、源码摘要和 manifest 更新；原 Owned、原生身份、只读退出句柄、保护身份和本轮已通过的余量逻辑保持。不能通过预热 `platform` 缓存代替冷启动兼容证明。
4. 若首次真实冷导入暴露另一项 SDK 本机初始化事件，先记录精确事件、调用来源和副作用；仅同一导入兼容问题可在这一离线修复范围内处理。需要网络、模型、外部进程、服务变化或研究算法改动时，不扩展此提案。

## 验证顺序

- 先使用保留的真实失败作为回归依据，增加全新隔离 Python 子进程中的真实 Ollama/HTTPX 冷导入用例。覆盖 worker 和 reader 的实际原所有权上下文；不能仅测试提前缓存或伪造导入对象。
- RED 应复现已知导入拒绝；修复后 GREEN 应证明原 SDK 构造完成、原关闭检查满足、模型和实际 HTTP/11434 请求未发生。
- 保留原有审计负例，并补足精确 hostname 事件之外的 socket、DNS、subprocess 拒绝检查；保留当前 89 个入口测试身份以及 B 相关原契约。测试只在新候选中运行，原失败和收据不改。
- 封存精确源码、证据和执行提案，进行必要独立准备复核。只有独立 PASS 与 root 处置一致后，才可能执行下一条单次接线验证。
- 若用户一并授权下一次运行：仅一个新 root/profile、一个新 reader、两次原读回及一次只读独立结果复核；正常 SSRF 的 `raw.githubusercontent.com` 受限 DNS 范围明确保留；不调用模型、资料 HTTP、11434、UI、音频或服务操作。失败不重试，不计入真实 E02 研究三轮。

## 交付条件

修复与真实冷导入证据、独立准备复核、明确的新单例分配（如获授权）、原始结果和结果复核、项目 docs/UltimaDocs 镜像及本地 commit/tag。E02 真实研究、T2 出口、T3–T5 与 Owner 门保持独立。远端 push 仍保留已有自动审批阻断，不重试或绕过。

## Task 1: 隔离候选与真实冷导入回归

新根 `data/evidence/jarvis-work-capability/T2/e02-source13-cold-import-20261106`，保留原 B/E 字节与失败包。复制原 profile/adapter 与根入口，只做必要新位置绑定。先在全新 `-I -B -X utf8` Python 进程中从原 worker/reader 作用域进入真实 `own_ollama_types`；导入所有权检查完毕即停止，不执行研究。真实 SDK、不预热 platform、不替换 HTTPX 类。保留 RED，再精确修复本机 hostname 事件并验证 GREEN 和其他审计负例。

Expected: RED 复现 socket.gethostname 拒绝；GREEN 同时覆盖 worker/reader 原导入上下文、真实类型与关闭，网络/模型提交仍无发生。探针只用合成 admission 验证初始化，不能冒充真实 Root 分配或完整 profile。

## Task 2: 原契约与根入口回归

固定新增候选 manifest，运行原 557 项契约及新增冷导入/拒绝用例，再运行原 89 项根入口检查。新入口仅改变固定位置/摘要，清理余量和原时限不变。核对原测试身份、源码前后哈希和旧失败包。

Expected: 新候选全部相关检查通过，原 557 和 89 身份保留，旧包字节不变；这仍不是实跑通过。

## Task 3: 独立准备复核与封存

绑定新 profile、根入口、原题/四来源与全部依赖；新的只读 reviewer 审查精确源码和 Task 1/2 证据。原始报告保留，root 逐项处置。只在独立 PASS 后登记准备通过并签发用户已批准的一次短期 release。

Expected: 独立准备 PASS、本地 commit/tag 与镜像读回一致；未通过时不实跑。

## Task 4: 已授权单例及独立结果复核

按原执行范围核验七个保护身份，执行一次新的零推理原资料 profile，失败不重试。随后一次只读独立结果复核；无论成败都保留原始结果、清理/保护身份、计数限制与最终登记。E02 真实研究仍由后续原验收门决定。

Expected: 单次分配严格消费，真实结果如实登记，实际 SDK 写入/新 reader/两次读回逐项证明；任何缺项不得记通过。
