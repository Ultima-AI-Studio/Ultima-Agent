# UltimaAgent 项目引导索引（INDEX）

> **本文件是 UltimaAgent 的执行入口**：任何开发 / 审计 / 同步动作前，先读本文件定位权威源，再读对应范式，最后动手。
> 版本：2026-10-24 ｜ 制式：Ultima AI 项目引导索引（由 `_shared\templates\项目引导索引模板.md` 生成）
> 2026-10-24 对齐根 INDEX：纳入 G-DISPATCH-001 与 G-WO-NAME-001（全局工单命名标准）
> 2026-10-28 ① 纳入派发执行环境规则（Codex ≥0.165.0 + 精简 CODEX_HOME，静默派发无弹窗，详见 §5）② 根 INDEX 更新 G-DISPATCH-001 为**自主推进版**：本项目自主调用 Codex 开发，遵守规范队列底线
> 2026-10-29 纳入 **G-TASKFLOW-001 任务工作流范式**：所有任务处理与下发统一走任务工作流（登记→计划评审→执行→独立审计→有界修复→验收→冻结），执行端无关（Codex/DeepSeek 可替换，工作流不变），详见 §5

## 0. 三条铁律

1. **先读本 INDEX → 再读权威范式 → 再动手**（Codex 派单 prompt 首段强制引用本文件）
2. **权威源只有一份**：本地 `H:\UltimaAI\_shared\`（唯一权威）｜ GitHub `Ultima-AI-Studio/UltimaDocs`（云端镜像）｜ 飞书（备份）。项目 `docs\shared\` 只是同步副本，改内容一律改 `_shared` 权威源再同步，禁止在副本上直接改。
3. **本项目自主推进开发，直接调用 Codex，遵守规范队列底线**（G-DISPATCH-001 自主推进版，2026-10-28）：本窗口负责工单登记与自主派发，派发前先登记全局主表；禁止绕过规范裸跑。

## 1. 权威源地图

| 内容 | 本地权威 | 云端镜像 |
|---|---|---|
| 范式（UI / Codex / 全局根目录 / 存档总纲） | `H:\UltimaAI\_shared\paradigms\` | GitHub UltimaDocs `docs/shared/paradigms/` |
| 品牌资产（logo / 图标 / 组合规范） | `H:\UltimaAI\_shared\brand\` | GitHub UltimaDocs `docs/shared/brand/` |
| 模板（工单 / 审计 / 报告） | `H:\UltimaAI\_shared\templates\` | GitHub UltimaDocs `docs/shared/templates/` |
| 全局队列主表 | `H:\UltimaAI\_shared\queue\global-queue-index.md` | 本地权威（不镜像） |

## 2. 本项目必读规范（按序，缺一不可）

1. `docs\INDEX.md`（本文件）
2. `docs\shared\paradigms\UltimaAI-任务工作流范式.md` —— **任务处理与下发工作流（G-TASKFLOW-001，执行端无关：登记→计划评审→执行→独立审计→有界修复→验收→冻结；Codex/DeepSeek 均同一套）**
3. `docs\shared\paradigms\Codex-外部执行端调用范式.md` —— 派单 / 回执 / WIP / DoR（当前默认执行适配器细则）
4. `docs\shared\paradigms\UltimaAI-全局根目录范式-方案.md` —— 目录骨架 / 三层数据 / **GitHub 桥接与授权 §5.1**
5. `H:\UltimaAI\INDEX.md` 全局强制规则 **G-DISPATCH-001** —— 各项目自主推进开发、直接调用 Codex，遵守规范队列底线（2026-10-28 自主推进版）
6. `H:\UltimaAI\_shared\paradigms\UltimaAI-全局工单命名标准.md` 规则 **G-WO-NAME-001** —— 新工单 ID / 显示标题 / 文件名统一格式；创建、阅读或提交工单前必读
7. `H:\UltimaAI\_shared\paradigms\UltimaAI-项目接入与任务队列派发范式.md` —— 项目接入、入队与接续（G-DISPATCH-001 自主推进版已批准生效，其余细则待复核）
8. `H:\UltimaAI\_shared\paradigms\UltimaAI-产品接入UltimaAdminCMS范式.md` —— 接入统一主控后台（CMS）：登记 / product.json 契约 / 三件套模板 / 验收；涉及接入 UltimaAdmin 时必读
9. `docs\shared\paradigms\Ultima-UI样式范式.md` —— 涉及界面/图标时必须读
10. `docs\shared\brand\README.md` —— 涉及品牌/logo/组合时必须读
11. UltimaAgent 特有：见 `docs\` 下产品文档

## 3. GitHub 与三层同步

- **组织**：`Ultima-AI-Studio`（**根路径只允许与项目同名的仓库**；备份等放同名仓库内部子路径）
- **全局文档库**：`UltimaDocs` → https://github.com/Ultima-AI-Studio/UltimaDocs
- **本项目仓库**：未建（登记后创建同名仓库）
- **三层链路**：本地权威（`_shared\` + 产品目录）→ 复制 `ultima-docs-repo\docs\shared\` → commit/push UltimaDocs → 飞书导入备份
- **认证**：Git Credential Manager + PAT（禁硬编码 token，凭证入加密 vault）
- **失效排查**：401=PAT 失效；`Repository not found`=仓库不存在或无权（用 GitHub MCP 创建后续推）；网络=保留 commit 续推

## 4. VPS 资产台账

> **唯一权威**：`H:\UltimaAI\_shared\server-assets.md`（全系共享：§一服务器清单 / §二工具链 / §三安全基线 / §四密钥台账 / §五凭证管理；变更只改该文件）。以下为本产品专属用途。

| IP | 本产品用途 |
|---|---|
| `161.33.167.206` | UltimaRadar 充值数据采集在用（nginx:80 / python:8721 / sshd:22）；可再挂轻量项目 |
| `198.13.46.208` | 已激活（2026-10-28）：Ultima Sentinel 部署机（前端审计台 + 后端 + 扫描服务）；域名 `namechatai.space` 挂此机 |

> **凭证管理（强制）**：VPS root 密码 / API key / Token 等敏感凭证**不写入本项目任何文件**，集中存于主脑加密 vault（`H:\UltimaAI\_shared\vault\`，DPAPI 加密，**禁入 git / 云盘 / 飞书 / 聊天**）；需用时向主脑申请，用 `vault.ps1 get <名称>` 解密取用，用后即弃，禁止明文落盘。

## 5. 全局调度与监察

- **调度权威**：本项目自主派发 Codex（G-DISPATCH-001 自主推进版）；UltimaManager 为可选监督/审计工具，不阻塞产品推进；全局主表 `_shared\queue\global-queue-index.md` 为聚合、预登记与证据入口，不是另一套派发器
- **派单模型（强制）**：**一单一进程**——一张工单 = 一次 `codex exec` = 一个独立进程/会话，禁止"一包多单"
- **派发执行环境（强制，2026-10-28 固化）**：Codex CLI 必须 **≥0.159.2（现装 0.165.0）**；派发一律设精简 `CODEX_HOME=C:\Users\Administrator\.codex-cli`（仅 model+auth，无插件/MCP/notify），禁用桌面应用 `~\.codex` 配置派发；全程静默无终端窗口（主进程隐藏 + 新版子进程隐藏启动）。队列引擎已内置（`run_worker.py`），手工派发按 `docs\shared\paradigms\Codex-外部执行端调用范式.md` §2 执行
- **WIP 双层（强制）**：**每项目执行中 ≤1 + 全项目执行进程 ≤3**；审计中 ≤1；跨项目可并行（读本 INDEX 即视为已接受此约束，超限先问主脑）
- **工单命名（强制）**：新工单按 G-WO-NAME-001 统一命名（`wo-<project-key>-<YYYYMMDD>-<NNNN>` + 显示标题 + `--<topic-slug>.md` 文件名）；存量工单保留原 ID，按全局主表登记映射
- **看门狗**：定时巡检全局主表，发现阻塞 / 越界 / 回执缺失 / 冻结门未闭合即上报
- **本产品队列**：`tasks\queue\`（已建 8 单，5 门冻结 + ORB 5 单）；工单三段式 + DoR 五项，见 Codex 调用范式

## 6. 本产品状态速览

Agent 产品线，队列冻结推进中；本项目自主调用 Codex 推进开发（G-DISPATCH-001 自主推进版）。

---

**对齐方式**：本 INDEX 由主脑统一维护；内容变更走 `_shared` 权威源 + 三层同步，项目无需自行改动。

- 当前T1自动审计修复闭环与T2前置：[2026-10-24实际闭环记录](reports/audit-repair-loop-20261024.md)。仅T1独立通过，原整单及Owner门保持。
