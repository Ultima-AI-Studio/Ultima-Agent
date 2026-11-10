# E02 SDK 冷导入隔离候选

用户 `call_c6b188dbc9514611ad330bb3b8829619` 已授权补修、真实冷导入回归、必要独立准备复核；只有准备 PASS 后可运行一次零推理接线验证，再做一次独立结果复核，失败不重试。产品候选仍为 `269aca511d88412dbb9c15d23911138469a37aa2`，当前 8B 摘要不变。

唯一 profile 行为改动：`WorkerAudit` 精确允许 `socket.gethostname` 本机元数据事件。其他 socket/subprocess 拒绝、限定 SSRF DNS、原四来源、SDK 真实类型和关闭检查、275/310/315 秒截止均保持。根入口仅重新绑定本目录和 profile 摘要。原 base manifest 的历史 import_path 保留，实际入口仍按原 Context.pins 派生当前 package 路径。

`cold/cold_import_probe.py` 在全新 `-I -B -X utf8` 进程进入真实 worker/reader 作用域和真实 own_ollama_types；使用合成 admission，仅验证初始化。所有权上下文正常退出后用探针哨兵停止，不进入产品导入或研究提交。探针另拒绝所有 DNS、socket I/O 和子进程。真实 Ollama/HTTPX 不替换为假类，不预热 platform。此证据不等于完整 profile 或真实研究通过，也不是 OS 网络总量测量。

原 557 项 profile 契约保留，新增两个真实冷导入和两个精确事件负例；原 89 项入口测试身份与代码保留。初始 root 绑定回归 88/89 的路径派生断言失败已保留于 `offline/cold-binding-full89`；修正绑定后另留新收据。`cold-evidence/red-1`、`red-2` 及对应 GREEN 不覆盖。

旧 B/E 包及上次失败运行不改，`inputs/preserved-before.json` 记录 540 个旧绑定。旧准备 PASS 只作历史依赖，本候选必须得到新的 `review/independent-preparation-review.json` PASS 和对应 root gate。未签发 release 前任何准备证据均无实际运行权限。

E01 三轮、E03 三正一负已通过。E02 真实研究、T2 出口、后续阶段及 Owner 门仍未通过。本地提交、tag 和镜像按完成节点登记；此前远端自动审批阻断保留，不重试或换渠道。
