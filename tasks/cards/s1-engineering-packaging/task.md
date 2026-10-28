# 任务卡：s1-engineering-packaging

- **task_id**：s1-engineering-packaging
- **stage**：S1（阶段一 v1.0）
- **标题**：工程封装与安装包（工程文件 → 单文件 EXE → 产品安装包）
- **创建**：2026-10-16 · 主脑立项（工单⑦；原工单⑦ 远程更新顺延为工单⑧）
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为发布物封装基础设施，是工单⑧（远程更新）的**上游**——更新通道推给客户端的"更新包"即本卡产出的安装包

## goal

将工程文件封装为**自包含单文件 EXE 执行文件**（零依赖可双击运行），再封装为**产品安装包**（可双击安装、含开始菜单/卸载项、WebView2 运行时依赖引导零弹窗、安装包签名防篡改），并作为工单⑧ 更新资产的唯一来源。禁止：不实现远程更新链路（工单⑧）、不实现多平台打包（阶段二）、不实现增量补丁（全量包替换）、任何前台弹窗。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: EXE 单文件封装 PASS（工程文件 → 自包含单文件 EXE，最小 .NET 发现环境真机运行；WebView2 已安装）
- [x] ACCEPT: 安装包制作 PASS（静默真机安装、开始菜单/桌面快捷方式、卸载项存在且可卸）
- [ ] ACCEPT: 依赖引导 PASS（WebView2 运行时缺失 → 静默安装、零弹窗）→ 2026-10-29 主脑补验：检测层真机闭环（已有→skip PASS；模拟缺失→install-silently+exit3 PASS，证据 pk03-webview2-missing-simulated.json）；缺失分支真机静默引导待净机（本机 Hyper-V 无 VM/ISO、无虚拟化软件）
- [x] ACCEPT: 安装包签名 PASS（与工单⑧ RU-03/RU-11 同钥，篡改拒绝，硬性要求）→ 2026-10-29 主脑补前置已闭环：真实 Ed25519 密钥对生成（私钥加密 PKCS#8 落 tools/publisher/keys/，口令注入 L8 keyId=ULTIMA_PUBLISHER_KEY_PASSPHRASE DPAPI 加密），安装包真实补签验签通过/单字节篡改拒绝，证据 pk04-real-signing.json
- [x] ACCEPT: 对接更新通道 PASS（安装包即更新资产，被工单⑧ 发布工具上传 + 客户端拉取校验闭环一次）→ 2026-10-28 RU-12 真实发布：安装包 dist/UltimaAgent-Setup-0.1.0.exe 上传 GitHub Release v0.1.0（id 426454992，4 资产 uploaded）+ T1 客户端拉取校验闭环一次成功（下载 99,766,174B、SHA256=61d1a7df… 冻结基线一致、Ed25519 双签名验签 PASS、篡改拒绝 PASS，证据 smoke-t1-t2-20261028.json）

## dependsOn[]

- （无任务级前置；版本级前置 v0.1+v0.2+v0.4 冻结登记于工单总卡 wo-s1-engineering-packaging.md）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\tools\packaging\`（封装与安装包制作脚本/配置）
- `H:\UltimaAI\UltimaAgent\dist\`（构建产物与安装包暂存，建议；不落盘明文）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-engineering-packaging\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（封装链路 + 依赖引导 + 签名安全）

## category + skill

- category: system · skill: eng.code + eng.build（构建发布）+ eng.security（签名需评审背书）

## receipt（完成时由 CodeX 回填）

- reviewReason: 主脑补验收口（2026-10-28）：PK-01/02 真机通过；PK-03 已有→skip + 模拟缺失→install-silently+exit3 PASS（缺失分支真机静默引导待净机，本机无 VM/ISO 硬约束）；PK-04 真实签名闭环（真实 Ed25519 密钥对 + 安装包补签验签/篡改拒绝）；PK-05 对接更新通道经工单⑧ RU-12 真实发布 + T1 拉取校验闭环 PASS。
- stdoutText: 实际版本 0.1.0；安装包 `dist/UltimaAgent-Setup-0.1.0.exe`，SHA-256 `61d1a7df02d36a8aa68b44868f39264a434f256cc865d491c714f51424d3814b`；已上传 GitHub Release v0.1.0。
- evidence: `docs/reports/wo-s1-engineering-packaging.md` + `docs/reports/evidence/wo-s1-engineering-packaging/` + `dist/release-artifact-inventory.json` + `docs/reports/evidence/wo-s1-remote-update-trigger/smoke-t1-t2-20261028.json`
- acceptance 逐项核对: PK-01 PASS；PK-02 PASS；PK-03 已有→跳过 PASS、缺失→静默安装模拟分支 PASS、真机净机待验；PK-04 真实签名 PASS；PK-05 真实上传+客户端拉取校验闭环 PASS。

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| PK-01 EXE 单文件封装 | 工程文件 → 自包含单文件 EXE（dotnet publish 单文件/自包含，零依赖可双击运行） | 零依赖环境双击运行成功；运行期窗口枚举：宿主 GUI 可见、其余计数 0（零弹窗 N7） | 运行实测 |
| PK-02 安装包制作 | 产品安装包（MSI/Inno Setup，含版本资源/图标/开始菜单/卸载项） | 可双击安装、快捷方式存在、卸载项存在且可卸 | 安装/卸载实测 |
| PK-03 依赖引导 | WebView2 运行时检测与静默安装 | 缺失时静默安装、零弹窗（N7：窗口枚举计数 0）；已有则跳过 | 引导实测 |
| PK-04 安装包签名 | 安装包签名（与工单⑧ RU-03/RU-11 同钥） | 签名可验、篡改拒绝（硬性要求）；无公钥 fail-closed 不判通过（B1） | 签名验证 |
| PK-05 对接更新通道 | 安装包即更新资产，与工单⑧ 发布/拉取链路闭环 | 发布工具上传 + 客户端拉取校验闭环一次成功 | 端到端闭环记录 |

## 环境前置（执行时经 L8 凭证中心注入，不落盘明文）

- 构建工具链：.NET SDK 8.0.425 / VS2022 / Python / WebView2（environment-spec 核验）
- 安装包工具链：MSI/Inno Setup 等（执行时选定并登记）
- 签名密钥对：与工单⑧ 更新签名同钥（私钥仅发布端持有；公钥注入工单⑧ RU-03）
- 产物目录：`H:\UltimaAI\UltimaAgent\dist\`（建议）
