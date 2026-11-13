# Codex 工单 · Next-00（建仓与骨架）

> 版本：v1.0 ｜ 状态：pending（前置：0054 收口冻结 tag）｜ 适用工具：Codex（本地执行端）
> 用法：按 T0→T8 顺序逐条执行，Gate PASS 后冻结再进下一条。
> 范围依据：`docs/plans/plan-ultimaagent-next-rebuild-20261113.md` §三/§四/§五（N-00 行）

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

### T1 · 目录骨架与命名口径
**文件**：`src\Core\`、`src\Senses\Voice\`、`src\Shell\`、`src\Surface\`、`src\Memory\`、`src\Middleware\`、`src\Update\`、`src\Lifecycle\`、`tools\`、`config\`、`devtools\`、`installer\`、`LICENSE`、`README.md`
**写什么**：
1. 按上列路径建目录，每目录一个 `__init__.py`（Python 模块）或项目骨架文件；
2. 每个目录内 `CONTRACT.md` 一页，只写对外契约（接口签名/事件名/职责边界），不写实现；
3. 目录命名逐一对照方案 §三，确认无 `brain` / `voice-next` / `host-shell` / `ui` / `window` 等旧名。
**验收（Gate T1）**：目录清单输出与方案 §三逐项一致；旧名匹配数 = 0。
**禁止**：建 `docs\` 下的 00-19 体系；建 `tasks\queue`（队列不在交付工程内）。

### T2 · 构建骨架
**文件**：`pyproject.toml`（或 `requirements.txt` + `setup.cfg`）、`src\Shell\HostShell\*.csproj`（原生壳项目骨架）
**写什么**：
1. Python 包可被 `pip install -e .` 与 `pytest` 发现；
2. 原生壳项目 `dotnet build -c Release` 可过（窗口可以只有一个空 Shell 占位，不渲染四角壳）；
3. 两个构建脚本落到 `tools\build.ps1` / `tools\test.ps1`。
**验收（Gate T2）**：`dotnet build` 0 警告 0 错误；`pytest` 收集到 ≥1 用例且通过；两脚本退出码 0。
**禁止**：引用旧仓任何项目引用/包名；引入第三方依赖未写来源与版本。

### T3 · precheck 一条命令
**文件**：`tools\precheck.ps1`
**写什么**：
1. 串起：构建（python + dotnet）→ 单测 → Windows-only 依赖扫描 → 输出 `PRECHECK_RESULT=PASS`；
2. 任一环节失败输出 `PRECHECK_RESULT=FAIL` 并给失败环节名，退出码 1。
**验收（Gate T3）**：成功路径 PASS；人为注入一个失败（临时改错一个断言）后 FAIL 且定位到环节；恢复后再次 PASS。
**禁止**：把扫描跳过开关写死在脚本里。

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
2. `tools\precheck.ps1` 与 `tools\check-zero-docs.ps1` 双跑；
3. 阶段报告 + 证据目录（Next 仓内 `devtools\evidence\next-00\`，仅证据不写方案）；
4. 打 tag `next-00-frozen`。
**验收（Gate T8）**：双脚本 PASS；T0~T7 全绿；越界声明「无」；回执 8 键齐全。
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
