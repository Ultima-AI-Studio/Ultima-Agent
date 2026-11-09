# G-ORCH 开源照搬映射与施工顺序

> 日期：2026-11-09 ｜ 状态：开发权威依据 ｜ 上游方案：`gorch-multi-channel-rollout-plan-20261109.md`
>
> **铁律**：不自己写判断算法，只做接线。每一项能力必须能指到一个成熟项目的具体文件或命令，且经过实测。找不到现成件的，先停下来报 Owner，不自行发明。

---

## 0. 一句话

并发所需的隔离、冲突、合并，worktrunk 和 ccpm 都有现成件；原方案里"自研三件"经实测**两件被直接覆盖、一件是 DeepSeek 的产出而非代码**。真正要写的只有"按顺序调用现成工具"的薄编排层，里面不含任何判断逻辑。

---

## 1. 四个 vendor 的处置结论（均已实测）

| vendor | 星数 | 许可证 | 处置 | 实测依据 |
|---|---|---|---|---|
| `cft0808/edict` | ~17k | 见原仓 | **已移植**（看板状态机） | 13 子命令全通、8 进程并发零丢失 |
| `max-sixty/worktrunk` | ~12k | MIT/Apache | **直接用 `wt.exe` v0.81.0** | switch/list/merge/remove 全跑通（见 §4） |
| `automazeio/ccpm` | ~8.4k | 见原仓 | **移植 shell 脚本** | git bash 下 source/函数可用 |
| `golutra/golutra` | ~3.8k | **BSL 1.1** | **不引入** | 完整 Tauri 桌面应用 + BSL 商业限制，整体引入等同 OpenClaw 覆辙；只参考其多 CLI 适配思路 |

---

## 2. 照搬映射表（本文核心）

### 2.1 已落地（提交 `4cbff024` 及更早）

| 能力 | 来源 | 落地形态 | 改动纪律 |
|---|---|---|---|
| 看板状态机 | edict | `scripts/gorch/kanban_update.py` + `file_lock.py` + `utils.py` | 逻辑零改动，仅显示层换现代用语 |
| 执行段单通道 | 组装 | `scripts/gorch/codex_channel.py` | 真跑 GORCH-009 通过，143.7s exit 0 |
| 执行角色卡 | 新写（现代用语） | `agents/execution/SOUL.md` | 唯一一份，不按职能拆分 |

### 2.2 Phase 2 · 并发（全部照搬，零自研算法）

| 能力 | 成熟来源 | 精确调用 / 文件 | 实测结果 |
|---|---|---|---|
| 建 worktree + 分支 | worktrunk | `wt -C <repo> switch -c <branch> -y` | 一次建成分支与物理 worktree |
| 查看各通道状态 | worktrunk | `wt -C <repo> list` | 列出全部 worktree/分支/路径 |
| 物理隔离写 | worktrunk（git worktree） | 每个分支一个独立目录 | 两 feature 目录互不干扰 |
| **串行合并** | worktrunk | `wt -C <repo> merge <branch> -y` | fast-forward 合并，文件真实进 main |
| 清理 worktree + 分支 | worktrunk | `wt -C <repo> remove <branch> -y` | 后台删除，list 立即消失 |
| **依赖判断** | ccpm `lib.sh` | `unmet_deps <task_file>` | 函数在 git bash 可调用 |
| **冲突判断** | ccpm `lib.sh` | `active_conflicts <task_file>` | 读 frontmatter `conflicts_with` |
| 可开工清单 | ccpm `next.sh` | `bash next.sh` | 依赖满足且无冲突才列出 |
| 引用完整性 | ccpm `validate.sh` | `bash validate.sh` | 缺引用/坏 frontmatter 报错 |
| 任务结构载体 | ccpm 约定 | frontmatter `depends_on`/`parallel`/`conflicts_with` | 声明式，不运行时算文件交集 |

### 2.3 Phase 1 · 归位（标准协议 + 现有件，不自研算法）

| 能力 | 成熟来源 | 落地方式 | 说明 |
|---|---|---|---|
| DeepSeek 调用 | 现有 `call_deepseek`（urllib 标准库） | 每环节一次独立 HTTP request | 独立 request = 独立会话，不共享上下文 |
| 判据冻结 | Frozen Rubric 模式 | 固定 JSON schema，清单外类别拒收 | temp 0，输出过 JSON Schema |
| 主脑 8B | ollama 本地 OpenAI 兼容接口 | 标准 HTTP，只做路由/搬运/汇报 | 不做语义判断（AgentGate 前提） |
| ②③ 自审 | 独立会话 + 冻结判据 | 另一会话执行，留审→修→复验痕迹 | 不新造算法，复用同一调用通道 |

---

## 3. "自研三件"的最终覆盖结论

原方案 §4 标注"需要自研的只剩三件"，逐个核对后：

| 原"自研件" | 实测结论 | 覆盖者 |
|---|---|---|
| 串行合并队列 | **不用自研** | `wt merge` 已是成熟串行合并，逐个分支调用即可 |
| 写域冲突检测 | **不用自研** | ccpm 用 frontmatter `conflicts_with` 声明 + `active_conflicts` 在开工前拦截，不靠运行时算路径交集 |
| 批次表生成 | **不是代码** | 是 DeepSeek 拆解的 LLM 产出；结构直接套用 ccpm 的 frontmatter 字段，不另造 JSON 批次表 |

**结论：零自研算法。** 唯一新增的代码是薄编排层（按顺序调用 `wt.exe` 与 ccpm 脚本、传递参数、记录结果），它自己不做任何"能不能做/是否冲突"的判断——这些判断全部发生在被调用的成熟件内部。

---

## 4. worktrunk 实测记录（临时仓库，已清理）

| 步骤 | 命令 | 结果 |
|---|---|---|
| 建分支 a | `wt switch -c feature-a -y` | ✓ worktree `@ ...feature-a` |
| 建分支 b | `wt switch -c feature-b -y` | ✓ worktree `@ ...feature-b` |
| 查看 | `wt list` | 3 worktree，路径各自独立 |
| 合并 | `wt merge feature-a -y` | ✓ Fast-forwarded，`a.txt` 真实进 main |
| 清理 | `wt remove feature-b -y` | ✓ worktree+分支后台删除 |
| 收尾 | 临时仓库 `rm -rf` | 已确认无残留 |

---

## 4.1 主仓库接入发现（只读 `wt list`，未改任何文件）

- 主仓库已存在 **26 个历史 worktree**（绝大多数在 `~/.codex/worktrees/`，是 Codex 历史通道），其中 5 个带未提交改动——**全部不碰、不删**。
- 因仓库大、worktree 多，`wt list` 120s 超时（仍返回 26 行结果）。结论：新并发通道用独立命名前缀与独立目录，与历史 worktree 区分；编排不依赖 `wt list` 的全量扫描。
- 发现一个**更早会话遗留的悬空 worktree**（分支 `9ae14ebe` 指向已不存在的 `Temp/wt-probe`），非本次创建，待 Owner 决定是否清理，不擅自处理。

## 4.2 ccpm 受控实测（最小 `.claude/epics/demo/`，已清理）

构造 4 个任务（1 无依赖 / 2 依赖 1 / 3 声明与 1 冲突 / 4 依赖不存在的 99），两个场景：

| 场景 | 命令 | 实测结果 |
|---|---|---|
| 1=open | `next.sh` | #1、#3 ready；#2（依赖未完成）、#4（坏依赖）被 `unmet_deps` 拦，不列出 |
| 同上 | `validate.sh` | 抓到 #4 引用缺失 99（warning），引用完整性生效 |
| 1=in-progress | `next.sh` | #3 被 `active_conflicts` 标 "Ready but conflicts, Wait for #1"，**Summary 0 ready，开工前拦下** |

**关键确认**：ccpm 是声明式（冲突写在 frontmatter，不运行时扫文件），且拦截发生在选任务阶段，不是运行期写文件才暴露。

## 4.3 薄编排的确切形态（只接线，不含判断）

`unmet_deps` / `active_conflicts` 都接受任意 `task_file` 参数、只在同目录找 `<ref>.md`；**只有 `list_task_files` 硬编码 `.claude/epics`**。因此编排层绕过 `list_task_files`，对同批次目录里每个任务直接调这两个原函数：

```bash
source <ccpm>/lib.sh
printf 'UNMET:%s\n' "$(unmet_deps <task>.md)"
printf 'CONFLICTS:%s\n' "$(active_conflicts <task>.md)"
```

- “能不能开工”的判断 100% 在 ccpm 函数内；Python 只遍历、传参、读固定前缀结果，不解析 ccpm 的人类可读表格（避免再犯“Markdown 当类型系统”）。
- 建隔离用 `wt switch -c`、合并用 `wt merge`、清理用 `wt remove`，执行用现有 `codex_channel.py --workdir <worktree>`。
- 编排层自身不出现任何依赖/冲突/合并的算法；覆盖不了就停下报 Owner。

### 4.4 wt 自动化契约（临时仓库实测，已清理）

统一带 `--format json -y --no-hooks`，shell 不跟随用 `--no-cd`；PATH 前置 `Git\cmd`。

- **建隔离位**：`wt switch -c <branch> --path <dir>`，stdout 第一行为**单行 JSON**：
  `{"action":"created","branch":...,"path":...,"created_branch":true,"base_branch":...}`。
  重复对已存在分支调用（不带 `-c`）返回 `action:"existing"`，天然幂等，不重复建。
- **默认路径**：无配置时建在 sibling 目录 `<repo>.<branch>`；`--path` 可把 worktree 放进集中目录（experimental，分支名不变）。
- **合并**：`wt merge <branch> --format json`，输出**多行 pretty JSON**（须从首个 `{` 到末个 `}` 提取，不能只取第一行），字段 `branch/target/committed/squashed/rebased/removed`。
  - 纯 fast-forward 场景 `removed:false`，worktree 保留，需编排层显式再调 `remove`。
  - **冲突硬验收**：add/add 冲突时进程 `exit=1`，明确 `CONFLICT (...)`，rebase 停在未完成态，绝不静默成功。
  - 注意 `merge` 会先 squash 改写 target 历史；冲突后须 `git rebase --abort` 回到干净态（abort 后 target 指向 wt 建的 squash commit，实测内容完整）。
- **清理**：`wt remove <branch> --foreground -y` 同步删除 worktree 目录与已合并分支；未合并分支需 `-D`。

---

## 5. 运行环境约定（不是改代码，是调用前置）

| 项 | 约定 |
|---|---|
| git 不在 PATH | 调用 `wt.exe` 前当前会话 `PATH` 前置 `C:\Program Files\Git\cmd` |
| ccpm 脚本是 bash | 用 `C:\Program Files\Git\bin\bash.exe`（实测 v5.3.15）执行 |
| 自动化跳过交互 | 所有 wt 命令带 `-y` |
| 不依赖 cd | 统一用 `wt -C <repo>` 指定仓库，shell integration 不装也不影响 |
| 专用解释器 | 跑测试用 `tools/venv-openjarvis/Scripts/python.exe`，带 `-o addopts=` |
| Codex 需代理（OpenAI 国内被墙） | 执行前注入 `HTTPS_PROXY/HTTP_PROXY=http://127.0.0.1:7897`（clash-verge/mihomo，实测出口 US Phoenix，chatgpt.com 返回 200）；codex_channel 的 `run_codex` 未自定义 env，继承父进程代理变量。无代理时 codex 反复重连超时、正确返回 blocked（fail-closed） |

---

## 6. 施工顺序（每步带机检验收）

| 序 | 动作 | 来源 | 验收（机检，不靠人读） |
|---|---|---|---|
| S1 ✅ | ccpm 脚本归位到 `scripts/gorch/ccpm/`（**原文复制，不改逻辑**） | ccpm | git bash 下 `bash validate.sh` 可跑；文件与源逐字节一致（提交 `59cfd538`） |
| S2 ✅ | 主仓库接入 worktrunk 验证（不建真分支，先 `-C` list 只读） | wt.exe | `wt -C <主仓库> list` 正常返回，不改动任何文件 |
| S3 ✅ | 薄编排：按 frontmatter 调 ccpm 原函数选可开工项（fail-closed） | 组装 | 12 条 gate 单测，选出的清单与 ccpm 原函数一致（提交 `59cfd538`） |
| S4 ✅ | 薄编排：为可开工项调 `wt switch` 建隔离位（幂等，`--base @`） | wt.exe | 真实建 2 worktree 基线正确、幂等 existing、blocked 跳过；5 条单测（提交 `4b744d26`） |
| S5 ✅ | 通道内调 `codex_channel.py` 执行（现有件，execute 子命令 fan-out/join） | 已落地 | 真实 2 通道并发：各自独立 run-dir、产物落各自 worktree、交叉串单检查均 False；7 条 execute 单测（提交 `7e50634d`，三文件回归 40 passed） |
| S6 | 薄编排：验收通过后逐个 `wt merge` + `remove` | wt.exe | 故意造一个冲突 frontmatter，在 S3 阶段被拦，不进执行 |
| S7 | 全量回归 + 打 tag | — | 现有 117 passed 不回归；无 tag 不报完成 |

**S6 的冲突拦截是硬验收**：必须在编排/开工阶段（S3）就拦下，证明冲突不是等到运行期写文件才暴露。

---

## 6.1 角色可替换的边界（2026-11-09 Owner 指令）

Owner 明确要求：**执行边界不绑定 DeepSeek 与 Codex，不同角色可替换 API 或其他大模型**。该边界已成独立契约，不写在本文件的施工顺序里：

> **`docs/specs/execution-slot-contract.md`** —— 三插槽（主脑位 `S-MAIN` / 审议位 `S-REVIEW` / 执行位 `S-EXEC`）的接口定义、硬边界、回执统一结构、替换方式（配置 vs 改码）、两条路径现状与八跳空档、已知缺口、可机检判定。

与本文件的分工：**本文件管「照搬哪些件、按什么顺序拼」**（施工口径）；**该契约管「拼好之后每一段认什么接口、能换谁」**（运行时口径）。两者不重复。

契约中已如实标注的现状要点：

- **契约上三插槽都可替换；代码上只有 `S-REVIEW` 的 base_url 与 `S-EXEC` 的 exe 路径能纯配置替换**，其余要改代码（`model` 硬编码 4 处、执行位 cmd 是 codex 专属参数）。
- 当前有**两条互不相连的路径**：A 审议链（`run-gorch.py`→`orchestrate-order.py`→DeepSeek，只到 ④ 排程）与 B 执行链（`batch_orchestrator.py` gate/provision/execute→`codex_channel.py`，S5 已跑通）。**接通二者是 S7 的核心工作**。

---

## 7. 边界（明确不做）


- 不整体引入 golutra（BSL + 完整 Tauri 应用）。
- 不在薄编排层里写任何冲突/依赖/合并的判断算法。
- 不改 ccpm 脚本与 worktrunk 的内部逻辑；只做复制和调用。
- 不让 Codex 获得裁决权/打 tag 权（沿用铁律 §9）。
- 若某一步发现现成件覆盖不了，**停下来报 Owner 并附排查结论**，不临时自研。
