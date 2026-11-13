# Codex 工单 · Next-00（建仓与骨架）

> 版本：v1.0 ｜ 状态：pending（前置：0054 收口冻结 tag）｜ 适用工具：Codex（本地执行端）
> 用法：按 T0→T8 顺序逐条执行，Gate PASS 后冻结再进下一条。
> 范围依据：`docs/plans/plan-ultimaagent-next-rebuild-20261113.md` §三/§四/§五（N-00 行）+ **先行规则** `docs/specs/next-双域分离与开工设置规范.md`（开工前必读）

---

## 0.1 设置与功能要求（十项，缺一不派）

| # | 字段 | 本卡取值 |
|---|---|---|
| 1 | 模块与职责边界 | 只做「建仓 + 双域骨架 + 构建/门禁骨架 + 契约骨架」，不做任何业务实现 |
| 2 | 写入域 | `H:\UltimaAI\UltimaAgentNext\` 全量（唯一可写域）；旧仓只读 |
| 3 | 对外契约 | 八模块契约骨架（Core/Voice/Shell/Surface/Memory/Middleware/Update/Lifecycle），只定签名与事件名 |
| 4 | 依赖与来源 | Python 运行时（官方发行版）+ .NET/WinUI 项目模板（微软官方）；不引入第三方运行时依赖 |
| 5 | 配置项 | `config\app.json`（版本/日志级别/端口）、各模块配置模板，全部落 `config\` |
| 6 | 端口·路径·阈值 | 工程域 `H:\UltimaAI\UltimaAgentNext`；客户端域默认 `%LOCALAPPDATA%\UltimaAgent`（安装期可改）；探活端口 8756（N-05 使用，本卡只登记） |
| 7 | 失败行为 | T0 前置不满足 → 立即停止并回执，不建目录；构建失败 → 不产出 dist；打包白名单缺失项 → 失败 |
| 8 | 日志与观测点 | `tools\precheck.ps1` 输出分段标记：`BUILD` / `TEST` / `DEPSCAN` / `DOMAINSCAN` / `ASSETSCAN` |
| 9 | 验收判据 | 见 T0~T8 的 Gate；总验收跑 `precheck.ps1` + `check-zero-docs.ps1` |
| 10 | 客户端域影响 | 本卡建立客户端域目录契约与 `release-assets.json` 骨架；不产生任何实际运行时资产 |

---

## 0. 范围冻结

**本阶段只做**：

1. 在 `H:\UltimaAI\UltimaAgentNext` 建仓与目录骨架（八原子模块目录按新命名口径，五大能力模块为组织层不落目录）；
2. 构建骨架可跑（Python 包 + 原生壳项目骨架双构建 0 警告 0 错误）；
3. `precheck` 一条命令（构建 + 单测 + 依赖扫描）；
4. `config/` 唯一配置面落地，环境变量降级为测试注入；
5. 模块对外契约骨架（只定接口签名与事件名，不实现逻辑）；
6. 最小文档面：LICENSE + README 一页级。

**本阶段不做**：

- 不从旧仓复制任何代码文件（`.py/.cs/.xaml/.ps1` 一律禁止）；
- 不引入任何模块的业务逻辑实现（契约骨架留 NotImplemented / 空实现）；
- 不接语音、不接模型、不做界面渲染；
- 不建任何 Windows 计划任务；
- 不写 00-19 文档体系、方案、过程文档（零开发文档铁律）。

---

## 1. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | 前置核验（目录/冻结 tag/旧仓只读） | 目标目录确认为空或不存在；冻结 tag 存在 |
| T1 | 目录骨架 + 命名口径 | 目录树与方案 §三一致；无旧命名（brain/voice-next/host-shell/ui/window） |
| T2 | 构建骨架（Python + 原生壳） | 双构建 0 警告 0 错误 |
| T3 | precheck 一条命令 | 单命令输出 PASS（构建+单测+扫描） |
| T4 | config 唯一配置面 | 无硬编码路径；env 仅测试注入 |
| T5 | 日志与错误通道 | 统一日志口；异常不吞 |
| T6 | 零开发文档自检 | 仅 LICENSE + README；无 docs 00-19 |
| T7 | 模块契约骨架 | 八模块契约文件齐；跨模块 import 只有契约层 |
| T8 | 总验收 | 全部 T 绿 + Next-00-frozen tag |

---

## 2. 任务明细

### T0 · 前置核验
**文件**：`H:\UltimaAI\UltimaAgentNext`（只读检查）、`tasks\queue\runs\wo-ultimaagent-20261113-0054-20261113T023840201172Z\final.json`
**写什么**：
1. 确认 `UltimaAgentNext` 不存在或为空目录；存在非空内容则停止并回执，不得覆盖；
2. 确认旧仓已打 `ultimaagent-v1-final-frozen-*` tag；未打则停止（前置门未闭合）；
3. 记录旧仓 HEAD SHA 与新仓初始状态，写入证据。
**验收（Gate T0）**：目录状态断言输出 + 冻结 tag 输出 + HEAD SHA，三者齐全。
**禁止**：在旧仓做任何写操作；不得以「先建后迁」为由把旧目录内容复制过来。

### T1 · 双域骨架与命名口径
**文件**：工程域 `src\Core\` `src\Senses\Voice\` `src\Shell\` `src\Surface\` `src\Memory\` `src\Middleware\` `src\Update\` `src\Lifecycle\` `tools\` `config\` `devtools\` `installer\` `dist\`；客户端域契约 `dist\client\`（预览树）+ `installer\release-assets.json`
**写什么**：
1. 工程域按先行规则 §四建目录，每模块一页 `CONTRACT.md`（只写契约，不写实现）；
2. 客户端域按先行规则 §三建**预览树** `dist\client\`：`runtime\ config\ data\ models\ logs\ plugins\` + 占位说明，用于边界扫描与打包演练（不含任何真实资产）；
3. `installer\release-assets.json` 建骨架，首批只登记 `config\*.json` 模板与 `version.json`，其余留空待后续卡片登记；
4. 目录命名逐一对照，确认无 `brain` / `voice-next` / `host-shell` / `ui` / `window` 等旧名；
5. `tools\domain-boundary.ps1`：断言工程域内无客户端绝对路径硬编码、客户端预览树内无 `.py/.cs/.xaml/.ps1/docs/.git`。
**验收（Gate T1）**：目录清单与先行规则 §三/§四逐项一致；旧名匹配数 = 0；`domain-boundary.ps1` 输出 `DOMAIN_RESULT=PASS`；`release-assets.json` 通过 JSON 校验。
**禁止**：客户端预览树内放任何源码/测试/构建脚本；建 `docs\` 00-19 体系；建 `tasks\queue`（队列不进交付工程）。

### T2 · 构建骨架
**文件**：`pyproject.toml`（或 `requirements.txt` + `setup.cfg`）、`src\Shell\HostShell\*.csproj`（原生壳项目骨架）
**写什么**：
1. Python 包可被 `pip install -e .` 与 `pytest` 发现；
2. 原生壳项目 `dotnet build -c Release` 可过（窗口可以只有一个空 Shell 占位，不渲染四角壳）；
3. 两个构建脚本落到 `tools\build.ps1` / `tools\test.ps1`。
**验收（Gate T2）**：`dotnet build` 0 警告 0 错误；`pytest` 收集到 ≥1 用例且通过；两脚本退出码 0。
**禁止**：引用旧仓任何项目引用/包名；引入第三方依赖未写来源与版本。

### T3 · precheck 一条命令（五段门禁）
**文件**：`tools\precheck.ps1`
**写什么**：
1. 五段依次串起并各自打印段标记：
   - `BUILD`：Python 打包 + 原生壳 `dotnet build -c Release`（0 警告 0 错误）
   - `TEST`：`pytest` 全绿
   - `DEPSCAN`：终端无关层 Windows-only 依赖扫描（0 处）
   - `DOMAINSCAN`：双域边界扫描（调 `domain-boundary.ps1`）
   - `ASSETSCAN`：`dist\client\` 每个文件都能在 `release-assets.json` 找到登记项（未登记 = FAIL）
2. 全绿输出 `PRECHECK_RESULT=PASS`；任一失败输出 `PRECHECK_RESULT=FAIL` + 失败段名，退出码 1。
**验收（Gate T3）**：成功路径 PASS；逐段注入失败（构建错一处 / 单测断言错 / 依赖加一个 windows-only / 预览树塞一个未登记文件）各得 FAIL 且定位到对应段；恢复后 PASS。
**禁止**：把任一段写成可跳过的开关；`ASSETSCAN` 白名单不得硬编码在脚本里（必须读 `release-assets.json`）。

### T4 · config 唯一配置面
**文件**：`config\*.json`（模块各自配置文件名按职责命名）、`src\Core\config_loader.py`
**写什么**：
1. 每模块一份配置文件，落 `config\`；读取只经统一 loader；
2. 环境变量只在测试注入通道使用，读取处加注释说明用途；
3. 硬编码路径/端口/阈值扫描为 0（阈值一律走配置）。
**验收（Gate T4）**：配置加载单测过；硬编码扫描 0 处；env 使用点登记表列出。
**禁止**：模块自行 `os.environ` 直读业务参数。

### T5 · 日志与错误通道
**文件**：`src\Core\logging_setup.py`、`src\Core\errors.py`
**写什么**：
1. 统一日志口（级别、轮转、落盘路径来自配置）；
2. 错误分类枚举 + 统一错误包装，业务层禁止裸 `except: pass`。
**验收（Gate T5）**：日志落盘可读；错误包装单测过；`except: pass` 扫描 0 处。
**禁止**：各模块自建 logger 实例绕过统一口。

### T6 · 零开发文档自检
**文件**：`tools\check-zero-docs.ps1`、`README.md`、`LICENSE`
**写什么**：
1. README 一页级：是什么、怎么装、怎么跑、许可证；
2. 自检脚本断言：仓库内不存在 00-19 编号文档、无 `docs/plans|reports|specs` 目录。
**验收（Gate T6）**：自检输出 `ZERO_DOCS_RESULT=PASS`；README 长度 ≤ 1 屏。
**禁止**：把旧仓方案文档复制进 Next「备查」。

### T7 · 模块契约骨架
**文件**：八模块各自 `CONTRACT.md` + `api.py`（或等价接口声明文件）
**写什么**：
1. Core：`Intent` / `Plan` / `confirm` / `memory_write_request`
2. Voice：`WakeEvent` / `Transcript` / `Speak` / `VoiceState` 七态
3. Shell：`HostTask` / `Restart` / `Status`
4. Surface：`AnchorUpdate` / `TranscriptStream` / `TaskPanel`
5. Memory：`Recall` / `Write` / `Forget`
6. Middleware：`Route` / `TaskWindow` / `Sandbox` / `Ticket`
7. Update：`CheckUpdate` / `ApplyUpdate` / `signature_verify`
8. Lifecycle：安装/升级/卸载三链 + `shipped_tasks=[]`
**验收（Gate T7）**：八份契约文件齐；契约签名可被静态读取；跨模块 import 只到契约层（扫描断言）；契约无实现逻辑。
**禁止**：在契约阶段夹带实现；新增方案外接口（新增走变更流程）。

### T8 · 总验收
**写什么**：
1. 全量 T 逐条复核；
2. `tools\precheck.ps1`（五段）与 `tools\check-zero-docs.ps1` 双跑；
3. 双域清单核对：工程域目录 vs 客户端域预览树逐项列出，证明无混用；
4. 阶段报告 + 证据目录（`devtools\evidence\next-00\`，仅证据不写方案）；
5. 打 tag `next-00-frozen`。
**验收（Gate T8）**：`PRECHECK_RESULT=PASS`（五段全绿）；`ZERO_DOCS_RESULT=PASS`；T0~T7 全绿；越界声明「无」；回执 8 键齐全。
**禁止**：带着任一 T 的残留缺陷宣告冻结。

---

## 3. 给编码代理的任务粘贴模板

```
N-00 T# <标题>：已完成，Gate 全绿（附证据路径）
产出：<文件清单>
Gate：<命令 + 输出摘要>
越界：无
```

---

## 4. 验收要点

- [ ] 范围冻结内逐项完成，无越界（无旧代码复制、无 00-19 文档、无计划任务）
- [ ] 每 T 验收清单全绿 + 自证完整（命令输出，禁「预计通过」）
- [ ] 契约骨架与方案 §三/§四 一致
- [ ] 8 键回执：链路号 / 工单号 / 通道 / 执行端 / 完成状态 / 产出路径 / 验收证据 / 越界声明
- [ ] 冻结 tag `next-00-frozen` 落库
