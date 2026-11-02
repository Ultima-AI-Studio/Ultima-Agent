# T2 · S2 首次真实前缀独立基础设施审计
工单 wo-ultimaagent-20261101-0021，原始 HEAD f53a803。原试验 FAIL。事实与覆盖 NOT_ASSESSED。首次 S2 和一次原生 POST 已消费。对生成后的协议分支没有运行证明。

## 实际边界
独立读取原始 observer 全部四行，逐项对照 bootstrap、outcome、一次性 authority、冻结 rubric 和 root reconciliation。四份原包 SHA256 逐一重算一致，详见同目录 verdict.json。单独的 GET /api/tags 在 t0 前结束，bootstrap 与 observer 是同一次请求。trial 依次 GET /api/version 200、GET /api/tags 200、POST /api/chat 500；另有一条 POST intent。入口至 teardown 17.6735 秒，POST 往返 16.9837 秒，冻结 d−b 36.0000 秒。失败在时限内返回；缺少 stage END 和 caller 确认，机械门失败。NativeReAct 只记录 agent_turn_start、inference_start、输入 security_alert。无助手生成或有效原生/secured envelope，无 tool 事件、stage payload、票据消费、确认、writer/ack 或研究报告写入。owner 已关闭。SDK audit 文件与试验回执单独存在。无证据表明此次失败起因于投影、deadline、SDK 防护或 harness。成功返回路径及事实质量仍待真实生成证明。

## 原生失败与资源解释
2026-11-02 上海时间 14:51:45 GPU discovery 超时并复用旧值；同次调度报 GPU free 10.8 GiB。runner 自己报告预测 6983 MiB 对报告的 11100 MiB，继而装载权重时 cudaMalloc(4671766528 bytes / 4455.34 MiB) 失败，runner exit 1，14:51:59 /api/chat 500。故障精确落在权重分配。估算与采样都不保证某一时刻分配成功。相同 d3d1… 权重、16384 context、单并行、1024 batch/ubatch 在 13:33 同机冷启动 9.30 秒，同样的 CUDA0 model buffer 装入，13:34:50 有 chat 200。无法据此次故障判定 12 GiB 显卡先天容量不足，也不能消除当时设备侧内存或驱动约束的可能性。

成功装载时 Ollama 报主存 free 7.5 GiB/free_swap 6.6 GiB，失败时为 4.1 GiB/746.1 MiB。其后 root 记录 available 1826 MiB、commit 44865519616/51383439360 bytes（87%）、PID25724 private 12811997184 bytes。压力是有支持的候选因素。事后 Windows commit 与 Ollama 的 free_swap 来自不同时刻、不同计量；无分配瞬间主机与设备预算跟踪或受控反事实，不能认定主机提交额度、特定进程、设备碎片或驱动为唯一原因。

07:03:47Z relief receipt 中 PID25724 在核验前已不存在，Stop-Process 0 次，五个保护进程身份与前次相符；available 16336 MiB、commit 27865096192/51383439360 bytes。审计另一次 nvidia-smi 只读采样 free 10059/12288 MiB。退出发起方与分配失败因果均未知，未实测新装载。

## 范围裁决与下一步
当前 authority 到此终止。保留原报告、全部计数和 FAIL。若问题只在冷加载是否恢复，最小独立设计是由 controller 另行审签一次无来源内容的同 daemon/权重/上下文/装载参数冷加载资格测量，用独立目录、明确独立请求配额、无重试，记录前中后 commit、设备预算、驻留态和加载日志，并预定成功判据。不能把人为预热后的结果用作冷前缀证明。此次审计没有启动测量或修复。

若要问尚未试过的代码文件能否产生准确单节，S3 可作为一项前瞻的新试验。候选清单中的下一份 TypeScript 代码是 unified-agent.ts，含 processQuery 及工具与纯文本处理分支。原 query 的“可参考”未指定 S2 为必须引用材料，但 S2 对 manager 初始化、provider 选择的独有证据没有替代。S3 成功最多证明 S3 的本地机制获得准确引文和按时确认；不能证明 S2、两文件实际连接或整体架构覆盖。测试待审方案不得把本报告中的机制或标准答案传给模型。

新设计须显式标注 r2 在 S2 处已失败、改变原“通过才继续”门的原因、旧失败永久计入分母；预注册 S3 的选择理由、后续固定 S1/S4 顺序及逐份停止规则。沿用原 query、四正文、模型与摘要、投影/提示/schema、480 token、16k context、36s slice、同样冷态，最多新增 3 POST/6 trial GET，每来源一次，全组累计 ≤4 POST/8 trial GET，0 writer/ack。先由独立评审核对范围与覆盖限制，controller 再决定是否只放 S3，后两份也逐份复核。此前没有语义输出可供按答案择优，但事后换首要来源仍是修改研究问题；禁止改称原组通过、重记 S2 为 unused、挑选成功结果、跳过缺失覆盖。若验收要求 manager 特定行为，则该项继续未验证。此方案仅供审议，不放行产品、source10、E02 或原组的任何新请求。

## 证据定位
- 原包 H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/per-source-feasibility-20261102/S2-first/first-f53a803-r2。其父级试验目录含 controller-S2-first-authority.json、independent-prefix-rubric.md、S2-first-root-reconciliation.json 和 resource-relief-receipt.json。
- C:/Users/Administrator/AppData/Local/Ollama/server.log，同时参照当地 13:33–13:34 与 14:51:41–14:51:59。审计时行 41594、41738、41784、41904、41915 分别提供早次权重分配、早次 HTTP 200、本次估算、本次分配失败、HTTP 500。
- 工作树 docs/plans/jarvis-work-per-source-research-design-20261102.md 第 42、46 行冻结了 S2 先行和失败停止条件。
