# UltimaAgent 项目引导索引（INDEX）

> **本文件是 UltimaAgent 的执行入口**：任何开发 / 审计 / 同步动作前，先读本文件定位权威源，再读对应范式，最后动手。
> 版本：2026-10-20 ｜ 制式：Ultima AI 项目引导索引（由 `_shared\templates\项目引导索引模板.md` 生成）

## 0. 三条铁律

1. **先读本 INDEX → 再读权威范式 → 再动手**（Codex 派单 prompt 首段强制引用本文件）
2. **权威源只有一份**：本地 `H:\UltimaAI\_shared\`（唯一权威）｜ GitHub `Ultima-AI-Studio/UltimaDocs`（云端镜像）｜ 飞书（备份）。项目 `docs\shared\` 只是同步副本，改内容一律改 `_shared` 权威源再同步，禁止在副本上直接改。
3. **产出型任务默认由主脑派 Codex 执行**：本窗口只承接工单，派单前必须先登记全局主表，禁止绕过全局登记直接派发。

## 1. 权威源地图

| 内容 | 本地权威 | 云端镜像 |
|---|---|---|
| 范式（UI / Codex / 全局根目录 / 存档总纲） | `H:\UltimaAI\_shared\paradigms\` | GitHub UltimaDocs `docs/shared/paradigms/` |
| 品牌资产（logo / 图标 / 组合规范） | `H:\UltimaAI\_shared\brand\` | GitHub UltimaDocs `docs/shared/brand/` |
| 模板（工单 / 审计 / 报告） | `H:\UltimaAI\_shared\templates\` | GitHub UltimaDocs `docs/shared/templates/` |
| 全局队列主表 | `H:\UltimaAI\_shared\queue\global-queue-index.md` | 本地权威（不镜像） |

## 2. 本项目必读规范（按序，缺一不可）

1. `docs\INDEX.md`（本文件）
2. `docs\shared\paradigms\Codex-外部执行端调用范式.md` —— 派单 / 回执 / WIP / DoR
3. `docs\shared\paradigms\UltimaAI-全局根目录范式-方案.md` —— 目录骨架 / 三层数据 / **GitHub 桥接与授权 §5.1**
4. `docs\shared\paradigms\Ultima-UI样式范式.md` —— 涉及界面/图标时必须读
5. `docs\shared\brand\README.md` —— 涉及品牌/logo/组合时必须读
6. UltimaAgent 特有：见 `docs\` 下产品文档

## 3. GitHub 与三层同步

- **组织**：`Ultima-AI-Studio`（**根路径只允许与项目同名的仓库**；备份等放同名仓库内部子路径）
- **全局文档库**：`UltimaDocs` → https://github.com/Ultima-AI-Studio/UltimaDocs
- **本项目仓库**：未建（登记后创建同名仓库）
- **三层链路**：本地权威（`_shared\` + 产品目录）→ 复制 `ultima-docs-repo\docs\shared\` → commit/push UltimaDocs → 飞书导入备份
- **认证**：Git Credential Manager + PAT（禁硬编码 token，凭证入加密 vault）
- **失效排查**：401=PAT 失效；`Repository not found`=仓库不存在或无权（用 GitHub MCP 创建后续推）；网络=保留 commit 续推

## 4. VPS 资产台账

| IP | 规格 | 系统 | 用途 |
|---|---|---|---|
| `161.33.167.206` | 一核 1G | Ubuntu 24.04 | UltimaRadar 充值数据采集在用（nginx:80 / python:8721 / sshd:22）；可再挂轻量项目 |
| `198.13.46.208` | 四核 **8G（实测 7941MB）** | Debian 13 | **未启用待分配**；域名 `namechatai.space` 挂此机 |

**VPS 工具链与安全（2026-10-20 实测已装）**：
- 161：sqlite3 / git / node v22 / tmux / htop / nginx / curl / python3 / jq / rsync / zip / unzip ✅
- 198：sqlite3 / git / tmux / htop / nginx（已装未启动）/ python3 / curl / jq / rsync / zip / unzip ✅
- 安全：**ufw active（仅放行业务端口）+ fail2ban active（sshd 防爆破）**，两台均已启用
- 连接：root 密码存主脑加密 vault（见下节），本机用 `vault.ps1 get` 取用；禁止明文

> **凭证管理（强制）**：VPS root 密码 / API key / Token 等敏感凭证**不写入本项目任何文件**，集中存于主脑加密 vault（`H:\UltimaAI\_shared\vault\`，DPAPI 加密，**禁入 git / 云盘 / 飞书 / 聊天**）；需用时向主脑申请，用 `vault.ps1 get <名称>` 解密取用，用后即弃，禁止明文落盘。

## 5. 全局调度与监察

- **全局主表**：`_shared\queue\global-queue-index.md`（所有项目派 Codex 必须登记一行：项目/工单/状态/冻结门/回执）
- **派单模型（强制）**：**一单一进程**——一张工单 = 一次 `codex exec` = 一个独立进程/会话，禁止"一包多单"
- **WIP 双层（强制）**：**每项目执行中 ≤1 + 全项目执行进程 ≤3**；审计中 ≤1；跨项目可并行（读本 INDEX 即视为已接受此约束，超限先问主脑）
- **看门狗**：定时巡检全局主表，发现阻塞 / 越界 / 回执缺失 / 冻结门未闭合即上报
- **本产品队列**：`tasks\queue\`（已建 8 单，5 门冻结）；工单三段式 + DoR 五项，见 Codex 调用范式

## 6. 本产品状态速览

Agent 产品线，队列冻结推进中

---

**对齐方式**：本 INDEX 由主脑统一维护；内容变更走 `_shared` 权威源 + 三层同步，项目无需自行改动。
