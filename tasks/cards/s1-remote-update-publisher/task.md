# 任务卡：s1-remote-update-publisher

- **task_id**：s1-remote-update-publisher
- **stage**：S1（阶段一 v1.0）
- **工单**：工单⑧（wo-s1-remote-update，原工单⑦ 顺延）· U24
- **标题**：工程端一键发布工具（点发布 = 打 tag→构建→manifest+签名→上传 GitHub Release→宣告强制版本）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为工程端发布链路封装，长期基础设施；**上传资产 = 工单⑦（工程封装）安装包**

## goal

实现工程端一键发布工具：用户点击"发布" → 打版本 tag → 构建产物 → 生成 manifest（版本/哈希/强制位）→ 私钥签名（manifest + 包）→ 上传 GitHub Release → 可选宣告强制版本号。发布成功后可被客户端更新通道正常拉取与校验。禁止：不实现客户端侧（T1/T2）、不实现增量补丁、绕过签名（发布必签名）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 一键发布 PASS（点发布 → 全链路自动执行，一次成功）✅ 2026-10-28 RU-12 真实发布
- [x] ACCEPT: manifest 生成 PASS（版本/哈希/强制位齐全）✅ 2026-10-28 RU-12 真实发布
- [x] ACCEPT: 签名 PASS（发布端私钥签名 manifest + 包，客户端公钥可验）✅ 2026-10-28 PK-04 真实密钥 + RU-12 双签
- [x] ACCEPT: 上传与宣告 PASS（GitHub Release 上传成功；可选宣告强制版本号）✅ 2026-10-28 release v0.1.0 已上传宣告
- [ ] ACCEPT: 发布产物被客户端通道拉取校验闭环 PASS（发布 → 拉取 → 校验 → 更新 端到端一次）⏳ 依赖 T1/T2 客户端侧实测

## dependsOn[]

- s1-remote-update-trigger（触发链路就绪后封装发布端；版本级前置 v0.2+v0.4 冻结登记于工单总卡 wo-s1-remote-update.md）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\tools\publisher\`（一键发布工具）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-remote-update-publisher\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（发布链路 + 签名安全）

## category + skill

- category: system · skill: eng.code + eng.security（签名 ultra 需评审背书）

## receipt（完成时由 CodeX 回填）

- reviewReason: 主脑验收 RU-12 真实发布（2026-10-28，方案 A Owner 拍板：工作树/tag 豁免一次，工具代码未改）
- stdoutText: release_url=https://github.com/Ultima-AI-Studio/Ultima-Agent/releases/tag/v0.1.0；package_sha256=61d1a7df02d36a8aa68b44868f39264a434f256cc865d491c714f51424d3814b；published_at=2026-10-28T09:14:08Z
- evidence: docs/reports/evidence/wo-s1-remote-update-publisher/ru-12-real-release.json + GitHub API 回读（release 426454992，4 资产 uploaded）
- acceptance 逐项核对: 4/5 勾选（T3 范围）；第 5 项客户端拉取闭环待 T1/T2 实测后联合勾选

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| RU-09 一键发布流程 | 点发布 → 打 tag→构建→manifest→签名→上传→宣告 全链路 | 一次成功；工程端工具可带控制台，但更新链路产物/宣告不得弹窗（N4 口径：工程端 GUI 与用户前台 N7 边界） | 发布实测 |
| RU-10 manifest 生成 | 版本/哈希/强制位齐全 | 字段齐全；结构以 specs/update-manifest-schema.md 为唯一权威（N5 消除双源） | manifest 样例 |
| RU-11 签名 | 发布端私钥签名 manifest + 包 | 客户端公钥可验 | 签名验证 |
| RU-12 上传与宣告 | GitHub Release 上传成功 + 可选宣告强制版本 | 上传成功、宣告生效；工程端工具可带控制台，但更新链路产物/宣告不得弹窗（N4 口径） | 发布记录 |

## 环境前置（执行时经 L8 凭证中心注入，不落盘明文）

- 发布仓库：`Ultima-AI-Studio/Ultima-Agent`（已建 2026-10-16，公开 main；RU-12 已验证发布并回读确认）
- 写权限令牌：经 L8 凭证中心注入；Git 远端凭证同理
- 签名私钥：发布端持有（与客户端公钥成对，公钥注入 RU-03）
