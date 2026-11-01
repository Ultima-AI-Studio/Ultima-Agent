# UltimaAgent 工作能力改造 T0 基线与计划评审

- 原单：`wo-ultimaagent-20261101-0021`；用户已批准按顺序推进。
- 结论：T0 技术门 PASS；下一步仅启动 T1。原单、产品能力、Owner 冻结和发布均未完成。
- 方案/契约：工作能力交付计划 r2 与目标验收契约 r2；R01—R08、E01—E08 保持本轮目标。

## 已完成

1. 固定 E01 三条事实、输出名、可信输出根和请求目录；其余 E 用例的目标、失败条件与所属阶段保持，后续阶段在进入前补齐运行材料。
2. 新建受管隔离工作区：`C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent`，分支 `codex/jarvis-work-capability`。仓库级开启 Git 长路径支持后完成创建。
3. 固定 220 项当前输入，发现 117 项未跟踪；隔离副本逐项核验补齐，并通过实际导入发现及补齐三项提示词/配置依赖。源码快照共 223 项，保存在 T0 的 zip 与逐文件哈希清单。
4. 隔离副本 `agent_server` 导入成功；现有文字接口/SSE/工具回归 14 项通过。该结果仅为改造前基线。
5. 核对安装依赖 OpenJarvis 1.0.4、pytest 9.2.0；五个关键 SDK 文件与 vendor 一致，并记录实际 Rust 模块摘要。
6. 通过项目 QueuePlanner 接口登记原单，全局主表放入权威条目区；Manager 持久镜像独立读回该原单。18766 展示服务未运行，未为本单重启它。

## 独立计划评审

r1 返回 REVISE，五项问题均保留原意见：可信输出根、SDK 构造线程与 metadata 丢失、旧产物假成功、真实 CLI/候选启动隔离、基线与验证命令。

r2 采用最小修订：可信服务配置根和服务器生成目录；两个限域文件别名在构造时捕获绑定；请求内 ledger 留下实际调用；服务端重新打开核验；真实 `cli --work`；隔离端口/运行目录；旧接口兼容。独立新会话复核 PASS，remaining_findings 为空。

| 输入 | 审查绑定的 SHA256 |
|---|---|
| 计划 r2 | `78d6d0e2584d47894a8e84fbf419b1c7ea8df818996124b63e05459e3ce69ae4` |
| 契约 r2 | `99ebc2de134683d986b62799b70814a9f336f7813f03725687fe469a8edf7047` |
| 固定样本 r2 | `e8d8c0e75a54d8f04221f54aabaec94a36fe6398a00d5745f6ae746e66038225` |

源输入为规划提交 `f6eb808`、223 项快照与 r2 覆盖；快照内的 r1 文档属于历史输入，重建时以当前已审查的 r2 为准。Git 提交号不能单独替代未跟踪运行输入清单。

## 回执与边界

- 证据根：`data/evidence/jarvis-work-capability/T0/`。
- `t0-gate.json`、`independent-plan-review-r1.json`、`independent-plan-review-r2.json`、`review-inputs-r2.json` 绑定门禁与源摘要。
- `input-baseline.json`、`baseline-required-supplement.json`、`runtime-inputs-snapshot.zip`、对应 manifest 和 `sdk-readback.json` 固定输入与依赖。
- `baseline-tests.xml/log` 记录 14 项回归；`registration-receipt.json` 记录实际登记读回。
- 两次 CLI 适配尝试因只读访问/配置/窗口审计问题失败，保留原始回执及 `adapter-attempts.json`，不作为 PASS 证据；有效独立评审来自单独的审查会话。
- 越界：无产品实现改动、无新录音/截图/播放、无模型推理；原语音 run_id 与 PID 32856/18068 保留。注册元数据、隔离副本和规划证据属于本单准备范围。
- 开源替代：继续复用 NativeReAct、ToolRegistry、SDK 文件工具和 SessionStore；本阶段无自研产品算法。快照扫描命中仅为凭证单元测试中的字面夹具，未捕获认证文件，命中及审阅记录保留。

下一门：T1 失败测试 → 实际 SDK 集成 → 回归 → 同一候选从真实文字入口连续三轮 E01 → 独立代码/产物审查。机械成果核验与三事实语义验收分别记录。
