# DeskBox 开源桌面整理 · 配置能力底座与 Windows 客户端样式底座适配评估

- **日期**：2026-11-15
- **作者**：豆包主脑（UltimaAgent 管理端）
- **对象仓库**：`Tianyu199509/DeskBox`（主仓，GPL-3.0-only）；伴生仓 `Tianyu199509/deskbox-agent`（MIT）
- **结论一句话**：**不适合作为可直接嵌入的「配置能力底座」或「Windows 客户端样式底座」——GPL-3.0 与「不采 GPL 底座」红线直接冲突，且配置/样式均与 DeskBox 自身领域强耦合、并非独立可移植库。** 真正价值是：①配置侧一套成熟范式（slice 组合 + 版本化迁移 + 原子弹性存储 + 源生成 + 契约测试）可在只读前提下黑盒借鉴、自研实现；②样式侧本质就是 WinUI 3 + Windows App SDK（现有 HostShell 已同栈），无额外可提取框架；③1.6.0 的 MCP/声明式 widget 是一条「不嵌入代码、经 IPC 调用独立进程」的潜在运行时集成缝，需另作裁定与合规确认。

---

## 1. 判定卡（结论摘要）

| 候选路径 | 判定 | 理由 |
| --- | --- | --- |
| 直接嵌入作为「配置能力底座」 | **不推荐（红线否决）** | ①GPL-3.0-only 与「不采 GPL 底座」冲突；②`SettingsService`/`AppSettings` 是 3723 行/54KB 的应用内「上帝服务」，与小组件领域强耦合，非独立库；③关键助手多为 `internal`/`sealed`，无干净包边界 |
| 直接嵌入作为「Windows 客户端样式底座」 | **不推荐（无独立框架 + 红线）** | ①样式主体是标准 `XamlControlsResources`（WinUI Fluent），DeskBox 只加一层薄应用 token，不是独立设计系统；②Mica/Acrylic 等材质直接来自平台；③GPL 同样禁止复制 |
| 只读留库、黑盒借鉴范式、自研实现 | **推荐（本次执行）** | 已 clone 到 `_vendor/deskbox` 只读留存；配置范式与 token 约定可作为自研/拼装的事实参照，不复制代码 |
| 经 1.6.0 MCP + 声明式 manifest 做运行时集成 | **待评估（需拍板）** | 外部进程经 stdio/命名管道让独立运行的 DeskBox 渲染原生 widget，不链接代码；但 DeskBox 成为运行时依赖（独立 GPL 应用），IPC 边界的合规口径需确认 |
| 回退到旧 MIT 版本 | **不成立（已核验）** | 最早发布标签 v1.4.0 起 LICENSE 即为 GPL-3.0，无可用的 MIT 发布标签；逐 commit 追溯即便存在也是冻结、无上游的快照，不建议 |

---

## 2. 开源事实核验（2026-11-15 现核验）

- 主仓：`https://github.com/Tianyu199509/DeskBox`，默认分支 `main`，浅克隆最新提交为合并 PR #589 `feat/160-kickoff`（1.6.0 进行中）。
- 许可证：**GPL-3.0-only**（`LICENSE` 为 GNU GPL v3 全文）。
- 定位：Windows 桌面整理工具（Stardock Fences 的开源替代），在原生桌面之上叠加可自由放置的 WinUI 3 小组件；不替换 Explorer、文件仍是普通文件、本地优先、数据不外发。
- 技术栈：C#、WinUI 3、Windows App SDK 2.5.1、.NET 10 Native AOT（可选审计 profile）、Rust 原生 Shell 层（可选）；目标 `net10.0-windows10.0.22621.0`，支持下限 `10.0.19041.0`，`WindowsPackageType=None`（非打包），x64/ARM64，当前版本 1.5.9。
- 热度与社区：**约 9140 stars / 488 forks / 16 subscribers / 105 open issues**；**仅 1 位贡献者**（Tianyu Zhu，单人开发）；仓库创建 2026-06-11，最近 push 2026-11-10。
- 发布节奏：极高频，1.4.8（2026-08-29）→ 1.5.9（2026-10-23）约两个月 12 个版本，平均 1–2 周一版。
- 伴生仓：`https://github.com/Tianyu199509/deskbox-agent`，**MIT**，PowerShell + JSON，提供 1.6.0 的 MCP 配置、widget manifest 示例与配套 Skill。

---

## 3. 配置能力底座评估（事实基础 + 判定）

### 3.1 实际架构（本地源码实测）

- **`Services/SettingsService.cs`（3723 行 / 182KB，`public sealed`）**：围绕中心 `AppSettings` 的「上帝服务」。用 AOT 兼容的 `SettingsJsonContext`（源生成、camelCase、`UseStringEnumConverter`、`WriteIndented`）；暴露大量默认值/最小/最大常量与规范字符串别名；提供 `SaveDebounced` 与带 `SettingsChangeKind`（General/Appearance）的变更通知。
- **`Models/AppSettings.cs`（54KB 根模型）**：
  - 含 `SchemaVersion`（默认 1）与 **13 个 `[JsonIgnore]` 领域 slice**（Core、Performance、QuickCapture、Todo、Music、WidgetShell、FileWidget、Backup、CloudBackup、DesktopOrganization、WidgetLayout、Weather、Search）；
  - 约 **220 个扁平 passthrough 属性构成冻结的 on-disk JSON wire 契约（顺序敏感）**；领域 slice 持有状态，门面是遗留/序列化面；
  - 契约测试 `SettingsSliceOwnershipContractTests` 以棘轮方式约束门面引用，防止 slice 归属回退。
- **`Services/ResilientJsonStore.cs`（482 行，`internal static` 泛型助手）**：
  - 临时文件 + `File.Replace` 原子提交并保留 `.bak`；
  - 对瞬时冲突（HResult `0x80070497`、`0x80070020`）有 50/150ms 重试阶梯；
  - 损坏文件隔离为 `.corrupt-*`（每文件仅留最新 2 份）；带验证的就地兜底；依赖 `App.Log`。
- **`Services/SettingsMigrationService.cs`（687 行）**：`ISettingsMigration`（`FromVersion` + `Migrate`）+ `SettingsMigrationPipeline`，`CurrentSchemaVersion = 15`，注册 0→15 共 15 步；**copy-on-write 事务**——每步在反序列化副本上执行，失败整步丢弃，结果要么迁移到记录检查点、要么与输入逐字节一致。
- **密钥管理**：`PasswordVaultCredentialStore`（66 行，`internal`）封装 WinRT `Windows.Security.Credentials.PasswordVault`（Credential Locker，非经典 Win32 CredManager），Resource=`DeskBox/CloudBackup`；密码绝不进 settings.json，仅 provider/url/path/toggles 进 JSON。

### 3.2 判定：范式成熟，代码不可移植

- **成熟度高（值得借鉴的五件套）**：slice 组合 + 版本化事务迁移 + 原子弹性存储 + AOT 源生成 + 契约/归属测试。这是一套经过 15 个 schema 版本和 534 个测试文件打磨的工程范式。
- **但不能直接当配置库嵌入**：
  1. **GPL 红线**：复制即触发 copyleft，硬否决；
  2. **领域强耦合**：13 slice、220 门面属性全部是 DeskBox 小组件领域语义，拖入即带入整套领域模型；
  3. **无独立库边界**：`SettingsService` 是应用内单例、`ResilientJsonStore` 为 internal static，依赖 `App.Log` 等全局，未按可分发库封装；
  4. **平台绑定**：凭据走 WinRT `PasswordVault`，与终端无关层（Core/Voice/Memory/Middleware/Update）禁 Windows-only 依赖的边界冲突。
- **处置建议**：以本仓为只读参照，按「先开源替代排查、再自研」的口径，在自有代码中复现该范式（接口与字段按 Ultima 自身领域定义，不照抄实现）。

---

## 4. Windows 客户端样式底座评估（事实基础 + 判定）

### 4.1 实际架构（本地源码实测）

- **`App.xaml`（34.5KB）**：建立在标准 `XamlControlsResources`（WinUI Fluent）+ CommunityToolkit Segmented 之上，**并非独立设计系统**。
- ThemeDictionaries（Light/Dark/Default/HighContrast 四套）中的自定义画刷大多镜像 WinUI 自带 token（SubtleFill、ControlStrongStroke、TextFill 等）。
- 三档圆角 4/6/8；字体 Microsoft YaHei UI / Segoe UI Variable；`WidgetTextShadow` 文字阴影；菜单用 `DesktopAcrylicBackdrop`；Mica/Acrylic 等材质直接来自平台。
- **`Services/ThemeService.cs`（235 行，`sealed`）**：Light/Dark/System 三态，经窗口根 `RequestedTheme` 应用；系统/自定义强调色（`AccentResourceScope` 覆盖）；窗口跟踪注册表，系统色变化经 200ms 防抖后刷新；Win32 标题栏深色模式。
- **`Styles/SettingsOverviewResources.xaml`**：仅一组间距/排版/圆角 token 与基于 WinUI Card/Text 画刷的样式，体量小；`Views/SettingsWindow.xaml` 达 287.9KB，各 Widget 内容 XAML 也很大。

### 4.2 判定：样式底座 = WinUI 3 本身，DeskBox 无额外可提取框架

- 现有 HostShell（WinUI 3 + WebView2）与 DeskBox **同栈**，所需 Fluent/Mica/Acrylic 能力平台已直接提供，无需借 DeskBox 获得。
- DeskBox 仅在平台之上加了一层薄应用 token（间距/排版/4-6-8 圆角），且这些 token 镜像平台语义，**不构成可独立移植的主题框架**。
- 叠加 GPL 红线，复制其 XAML 资源同样被否。
- **处置建议**：样式底座继续以 WinUI 3 + Windows App SDK 为准；可在只读前提下参考其 token 命名与圆角/间距约定，但不复制资源、不引入第二套主题运行时。

---

## 5. 潜在干净缝：1.6.0 MCP + 声明式 widget（待评估，非嵌入）

伴生仓 `deskbox-agent`（MIT）与主仓 1.6.0 揭示 DeskBox 正从桌面整理器演进为**带 MCP 接口的 WinUI 3 小组件托管平台**：

- **单一 stdio 入口 + 命名管道**：不开本地 HTTP/TCP 端口，由客户端按需拉起 `DeskBox.exe --mcp` 子进程，经当前用户命名管道与桌面宿主通信。
- **声明式 manifest（Draft 2020-12 JSON Schema）**：48 种视图节点（布局容器/控件/专用卡片/图表）、12 类原生数据源（systemMetrics、storageDrives、weather、calendar、clock、clipboard、rss、httpJson、aiMonitor 等）、QuickJS `logic.js` 脚本、30+ 动作类型、`${...}` 表达式、i18n 包、secret 设置项。
- **7 个 MCP 工具**：`deskbox_get_widget_spec`、`deskbox_get_capability_spec`、`deskbox_validate_manifest`、`deskbox_list_widgets`、`deskbox_upsert_widget`、`deskbox_capture_widget_preview`、`deskbox_push_widget_data`。
- **Stage-by-Default 安全**：`upsert` 未传 `commit:true` 仅校验/暂存返回 `stageId`，不改桌面；确认后同一 stageId 提交，幂等。
- 示例 widget：agent-hud（AI 状态看板）、sys-pulse（硬件监控）、news-rss（资讯聚合）、dev-toolbox（开发者工具箱）。

**适配含义与边界**：

- 这是**数据驱动、arms-length 的进程间接口**——外部 Agent 产出 JSON（数据而非链接代码），由独立运行的 DeskBox 进程渲染，理论上不形成代码层面的衍生作品；但该判断不构成法律意见，分发前需确认 IPC/数据边界的合规口径。
- 即便采用，DeskBox 仍是**独立的运行时依赖（用户另行安装的 GPL 应用）**，而非嵌入产品本体的底座；这与「开源拼装」相容，但属于架构级选择，需用户拍板。
- 伴生仓本身 MIT，其 Skill、脚本、schema、示例可自由使用；`ensure-deskbox.ps1` 提供环境检测与 SHA-256 校验安装。

---

## 6. 依赖许可、供应链与人力风险

- **第三方包全部为 MIT/BSD 宽松许可**：CommunityToolkit.WinUI.* / CommunityToolkit.Mvvm（8.4.2）、WinUIEx（2.9.3）、H.NotifyIcon.WinUI（2.5.0-beta.1）、Microsoft.Extensions.DependencyInjection（8.0.1）、Markdig（1.3.2）、Windows App SDK 2.5.1；并显式 `ExcludeAssets=all` 排除 WinAppSDK 传递引入的 `Microsoft.Windows.AI.MachineLearning`（onnxruntime/DirectML，约 39MB）。
- **copyleft 仅来自作者对整体作品选择的 GPL-3.0**，而非底层依赖；Everything SDK 为第三方独立许可 DLL（按架构单独分发）。
- 规模：应用本体 925 个 C# 文件 / 281,815 行；Rust 原生层仅 8 个 .rs（聚焦特定 Shell ABI）；测试 534 个 .cs、契约 37 文件；总跟踪 1998 文件。
- **人力/演进风险（若作为运行时依赖需重点权衡）**：
  1. **单人开发**：1 contributor，无组织级背书，存在巴士因子；
  2. **高频 churn**：两月 12 版，API/契约在 1.6.0 仍在演进，外部集成面临接口变动；
  3. **项目仅约 5 个月**：105 open issues，长期维护与稳定性尚待时间验证；
  4. 代码签名走 SignPath Foundation，分发链路需纳入 SBOM/许可台账。

---

## 7. 处置建议与后续推进点

**本次处置（建议）**

1. 两仓继续在 `_vendor` 作**只读参考件**留存（与 ApkStart 同法），不复制、不链接、不混入产品本体任何 GPL 代码。
2. **配置能力**：不直接采用 DeskBox 代码；按「先开源替代排查、再自研」口径，以其五件套范式为参照，在自有工程中实现 Ultima 领域的配置模型（含版本化迁移与原子存储）。
3. **样式能力**：以 WinUI 3 + Windows App SDK 为唯一样式底座（已同栈），仅参考其 token/圆角约定，不引入第二套主题框架。
4. MCP/声明式 widget 路径作为**独立议题**保留，待用户就是否接受 DeskBox 运行时依赖拍板，并完成 IPC 边界合规确认后再立项。

**待需要时再做（本次不展开）**

1. 配置自研前的开源替代排查（MIT/BSD 配置/设置库），输出最小输入输出与契约，附排查结论。
2. 若评估 MCP 集成：验证 `--mcp` 协议稳定性、manifest 版本兼容策略、失败/宿主离线的 fail-closed 处理。
3. 若采用任何运行时依赖：补 SBOM/许可清单、上游 tag 锁定与更新策略、国内分发（Gitee/镜像）评估。
4. 与 `_vendor` 其他参考件（apkstart、krouter 等）统一登记，避免重复引入同层能力。

---

## 8. 克隆与落盘记录

- 主仓只读副本：`H:\UltimaAI\_vendor\deskbox`（`git clone --depth 1`，分支 main，1998 跟踪文件，未改）。
- 伴生仓只读副本：`H:\UltimaAI\_vendor\deskbox-agent`（MIT，未改）。
- 已读核心源码（相对 `src\DeskBox\`）：`App.xaml`、`DeskBox.csproj`、`Services\ResilientJsonStore.cs`、`Services\SettingsService.cs`、`Services\SettingsMigrationService.cs`、`Services\ThemeService.cs`、`Services\PasswordVaultCredentialStore.cs`、`Services\ICredentialStore.cs`、`Models\AppSettings.cs`、`Styles\SettingsOverviewResources.xaml`、`LICENSE`。
- 本调研文档：`H:\UltimaAI\UltimaAgent\docs\research\deskbox-config-style-base-research-20261115.md`。
- 本次为调研/只读评估，未触发产品本体开发，未执行所评估的任何运行时部署。

---

## 9. 引用资料

- 主仓 README / LICENSE / csproj / 源码（本地 `_vendor/deskbox` 克隆）：`https://github.com/Tianyu199509/DeskBox`。
- 伴生仓 README / manifest schema / 示例（本地 `_vendor/deskbox-agent` 克隆）：`https://github.com/Tianyu199509/deskbox-agent`。
- 官网/资料：`https://deskbox.fun/en/`、`https://www.desk-box.cn/`。
- 合规口径参照：Ultima 工程方法论 §10.4 供应链 License 审查（不采 GPL 底座）、§11 通用铁律。
