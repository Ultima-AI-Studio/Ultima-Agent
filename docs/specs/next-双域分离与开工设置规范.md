# UltimaAgent Next · 双域分离与开工设置规范（先行铁律 v1.0）

> 状态：Owner 要求先行建立，**任何 Next 代码开工前必须遵守** ｜ 日期：2026-11-13
> 归属：本文件是 Next 的**规则权威源**（留存旧仓 docs/specs，靠 tag 引用；Next 仓内不复制）
> 上位：`docs/plans/plan-ultimaagent-next-rebuild-20261113.md`（总纲）｜ 关联：`docs/specs/hud-layout-zone-plan-20261031.md`、`docs/specs/kws-wakeup-params-baseline.md`

---

## 一、为什么先立规则

旧仓的病根不是代码写错，而是**边界没定**：开发目录与运行目录混用、临时脚本与产品资产混放、测试夹具进了交付、源码被当成运行时依赖。Next 从零重写，第一条规矩就是：**两个域物理隔离，单向流动，任何东西往客户端域加必须先登记**。

---

## 二、双域定义（物理隔离）

| 域 | 位置 | 装什么 | 谁写 | 是否进安装包 |
|---|---|---|---|---|
| **工程域**（Engineering） | `H:\UltimaAI\UltimaAgentNext` | 源码、构建脚本、测试、夹具、打包工程 | 开发者 / Codex | **否**（只有构建产物经打包进入） |
| **客户端域**（Client） | 安装目录（默认 `%LOCALAPPDATA%\UltimaAgent`） | 可执行、运行时、配置、数据、模型、日志、插件槽 | 安装器 / 运行时自身 | **是** |

**单向流动（唯一合法方向）**：

```
工程域  ──构建──▶  dist/（产物）  ──打包──▶  UltimaAgent-Setup.exe  ──安装──▶  客户端域
```

**双向禁止**：

- 禁止**反向**：工程域运行时不得把客户端目录当开发依赖去读取/写入（调试需读写时，用 `devtools` 沙箱副本，用后即弃）；
- 禁止**混入**：工程域源码、测试、脚本、docs、git 元数据**一律不得**出现在客户端域。

---

## 三、客户端域目录契约（锁定，改动走变更）

```
%LOCALAPPDATA%\UltimaAgent\
├─ UltimaAgent.exe              # 主壳可执行（启动入口，唯一）
├─ HostShell.exe                # 常驻托管壳（如需独立进程）
├─ runtime\                     # Python 运行时与依赖（解包后的 wheel，白名单内）
├─ config\                      # 运行时配置（用户可改）
│   ├─ host-tasks.json
│   ├─ interface-routing.json
│   ├─ voice-profile.json
│   └─ app.json                 # 全局：版本/日志级别/端口
├─ data\                        # 运行时数据（记忆库、任务窗口、状态）
├─ models\                      # KWS / CV3 模型文件
├─ logs\                        # 运行日志（轮转）
├─ plugins\                     # v1.1 插件槽（v1.0 空目录）
└─ version.json                 # 版本号 + 签名信息（单一版本来源）
```

**客户端域禁止项（出现即 Gate 失败）**：

- `.py` 源文件（`runtime\` 内的依赖包除外，且必须在白名单登记）
- `.cs` / `.xaml` / `.sln` / 构建脚本（`build.ps1` / `precheck.ps1` 等）
- 测试用例、夹具、测试数据
- 任何 `docs` 文档、README 之外的说明文件
- `.git` / `.gitignore` / 开发期临时文件

---

## 四、工程域目录契约

```
H:\UltimaAI\UltimaAgentNext\
├─ src\                 # 八原子模块（Core / Senses\Voice / Shell / Surface / Memory / Middleware / Update / Lifecycle）
├─ tools\               # build.ps1 · test.ps1 · precheck.ps1 · package.ps1
├─ config\              # 配置**模板**（打包时作为客户端 config 种子）
├─ installer\           # .iss + release-assets.json（资产白名单唯一登记处）
├─ devtools\            # 本地调试夹具、证据输出（永不进包）
├─ dist\                # 构建产物（.gitignore）
├─ .gitignore
├─ LICENSE
└─ README.md            # 一页级
```

**工程域禁止项**：

- 禁止出现 `docs\plans|reports|specs|decisions` 等 00-19 文档体系（零开发文档铁律）；
- 禁止把 `devtools` 内容打进安装包；
- 禁止在 `src` 内写一次性脚本（脚本一律进 `tools` 或 `devtools`）。

---

## 五、往客户端域加东西的唯一合法通道：资产登记

**任何新增客户端资产**（文件 / 目录 / 配置项 / 注册表项 / 启动项 / 服务项）必须走登记：

1. 在 `installer\release-assets.json` 登记一条：
   ```json
   { "path": "config/host-tasks.json", "source": "config/host-tasks.template.json",
     "purpose": "Shell 托管任务权威声明", "user_editable": true,
     "uninstall": "keep" }
   ```
2. 打包脚本**只按白名单取**，白名单外一律不进包；
3. `uninstall` 字段决定卸载行为：`delete` / `keep`（用户数据默认 `keep`，资产默认 `delete`）；
4. **未登记资产 = 打包直接失败**（硬门，不是警告）。

同一条规则适用于「往客户端文件夹里加东西」这句话的全部含义：**先登记、后落地**。

---

## 六、每步开工前置：设置与功能要求表（十项，缺一不派）

**每张 N 系列工单在派发前必须填满下表**（写进卡片头部「设置与功能要求」段），任何一项缺省或写「视情况」= 不具备派发条件。

| # | 字段 | 要求 |
|---|---|---|
| 1 | 模块与职责边界 | 一句话，超出这句话的事不做 |
| 2 | 写入域（fileDomain） | 精确到目录；越界写入=任务失败 |
| 3 | 对外契约 | 接口签名 / 事件名，跨模块只能经此通信 |
| 4 | 依赖与来源 | 每个依赖写来源（开源/自研），自研附开源替代排查结论 |
| 5 | 配置项 | 键名 / 默认值 / 是否用户可改 / 落在哪个 config 文件 |
| 6 | 端口·路径·阈值 | 具体数值；未定项标「待 N-xx 定案」并写决策时点，禁「视情况」 |
| 7 | 失败行为 | 超时 / 异常 / 降级路径，逐条写明 |
| 8 | 日志与观测点 | 事件名 + 关键字段，供验收脚本断言 |
| 9 | 验收判据 | 可机检命令 + 期望输出（禁「界面好看」类） |
| 10 | 客户端域影响 | 是否新增资产、是否登记、卸载行为 |

---

## 七、八模块的具体设置基线（已定值 / 待定项分开）

> 已定值来自既有冻结规格；**待定项必须在对应工单派发前定案并回填本表**，不得边写边猜。

| 模块 | 已定设置 | 待定项（决策时点） |
|---|---|---|
| Core | 意图分级 L0>L1>L2>L3；路由配置 `config/interface-routing.json`（schema v2）；复述确认双通道 | 意图分类黄金集规模与准确率阈值（N-01 定案） |
| Senses.Voice | **权威源=`next-感知交互参数基线-20261113.md`**：唤醒词「幂幂」threshold **0.30**（v1 仍 0.25 冻结不动）+ 连续 2–3 帧确认 + 唤醒后 0–5s +10%/5–10s +20% + pre-roll 1.5s；打断最小持续 **300ms**、检测→停播 ≤150ms、TTS flush ≤60ms、LLM cancel ≤40ms、淡出 15ms、混合 VAD；会话静默超时 **10s**（可配 5–15）、单次监听 15s；七态状态机；warm_progress 0/25/50/75/100；CV3 音色冻结参数；采样率按 DISPLAY/AUDIO 既有基线 | ASR 供应商与超时（N-04 定案）；唤醒阈值实测定值；VAD/AEC 具体实现（N-04 定案） |
| Shell | Guardian 20s 探活 / 3 次失败 / 300s 冷却；探活端口 8756；Job 归属判据「强杀 3s 内消失」；自启=启动文件夹 .lnk；零计划任务 | 主壳与托管壳的进程边界（N-05 定案） |
| Surface | 四角壳 8 锚点职责锁定；锚位宽度 `clamp(280px,24vw,352px)`；常驻仅顶/左上/右上；中央零遮挡；任务管理器面板 960×640 | 150% DPI 紧凑网格阈值（N-06 定案） |
| Memory | 三层：工作/长期/温度；写入由 Core 裁决 | 存储后端选型与检索 top_k（N-03 定案） |
| Middleware | 执行端可替换、一次一主、票据可追 | 沙箱形态（进程级/目录级，N-02 定案） |
| Update | 签名 scope 暂标 `temporary-test-only`；必须有回滚路径 | 更新源地址与灰度策略（N-11 定案） |
| Lifecycle | `shipped_tasks=[]` 唯一权威声明；`.iss` 只读不写；卸载零残留 | 默认安装目录与静默安装参数（N-11 定案） |

---

## 八、门禁：双域边界必须可机检

`tools\precheck.ps1` 必须包含以下五段，任一失败即 `PRECHECK_RESULT=FAIL`：

1. **构建**：Python 打包 + 原生壳 `dotnet build -c Release`，0 警告 0 错误；
2. **单测**：`pytest` 全绿；
3. **依赖扫描**：终端无关层（Core/Voice/Memory/Middleware/Update）Windows-only 依赖 = 0 处；
4. **双域边界扫描**：工程域内无客户端路径硬编码；客户端域（`dist\client\` 预览树）内无源码/测试/构建脚本/文档；
5. **资产登记校验**：`dist\client\` 内每个文件都能在 `release-assets.json` 找到登记项，未登记项 = FAIL。

---

## 九、违规处置

| 违规 | 处置 |
|---|---|
| 两个域混用（源码进客户端 / 开发期读客户端） | 任务失败，回退该改动 |
| 未登记资产进客户端域 | 打包失败，阻塞发布 |
| 复制旧仓代码 | diff 审查打回（新文件路径 + 无旧包名 import 双断言） |
| 写入域越界 | 任务失败，重做 |
| 卡片缺设置与功能要求表 | 不派发（DoR 不通过） |

---

## 十、新增需求怎么进来

任何「往客户端域加东西」或「改八模块契约」的诉求，一律走变更流程：登记 → 评估（是否属 v1.0 出包边界）→ 排进 N 序列或 v1.1 批次 → 回填设置表 → 再派发。**不得就地扩张**。
