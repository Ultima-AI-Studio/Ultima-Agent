# 任务卡：s1-remote-update-channel

- **task_id**：s1-remote-update-channel
- **stage**：S1（阶段一 v1.0）
- **工单**：工单⑧（wo-s1-remote-update，原工单⑦ 顺延）· U22
- **标题**：更新通道基础库（查版本/下载/签名校验/替换回滚）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为远程更新的通道基础设施，与工单⑥ MVP 并行收口；更新资产 = 工单⑦（工程封装）安装包

## goal

实现更新通道基础库：GitHub Releases API 查最新版本 → 下载更新资产（校验哈希）→ 客户端内置公钥签名校验（manifest + 包，失败拒绝执行）→ 替换 + 失败自动回滚（保留上一版本快照）。通道抽象预留镜像/自建兜底（本轮不实现）。禁止：不实现三种触发（T2）、不实现发布端（T3）、增量补丁（全量包替换）、任何前台弹窗。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 查版本 PASS（GitHub Releases API 返回最新版本号与资产地址，公开仓库匿名可用）
- [x] ACCEPT: 下载 PASS（资产下载完整，哈希校验一致才进入下一步）
- [x] ACCEPT: 签名校验 PASS（篡改包/伪造签名 → 拒绝执行，硬性要求）
- [x] ACCEPT: 替换 + 回滚 PASS（替换前保留上一版本快照；签名/替换/启动失败 → 自动回滚上一版本，硬性要求）
- [x] ACCEPT: 全程零弹窗（后台静默，前台零弹窗绝对纪律 N7）

## dependsOn[]

- （无任务级前置；版本级前置 v0.2+v0.4 冻结登记于工单总卡 wo-s1-remote-update.md，F3 修正）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\update\`（更新通道基础库）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-remote-update-channel\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（签名/回滚安全边界 + 通道抽象）

## category + skill

- category: system · skill: eng.code + eng.security（签名校验 ultra 需评审背书）

## receipt（完成时由 CodeX 回填）

- reviewReason: 主脑直做（用户指令"由你完成，不需要我参与"），不派 Codex；签名安全边界经 eng.security 契约核对（发布端 signing.py Ed25519 同原语）后放行
- stdoutText: 25/25 单测全绿；真实 GitHub Release v0.1.0 端到端冒烟 SMOKE_RESULT=PASS（查版本/下载 SHA256 冻结基线/双签名验签/篡改拒绝），证据 docs/reports/evidence/wo-s1-remote-update-trigger/smoke-t1-t2-20261028.json
- evidence: 查版本/下载/签名校验/回滚 场景实测（冒烟 JSON + tests/）
- acceptance 逐项核对: 5/5 全绿（见上）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| RU-01 查版本 | GitHub Releases API 查最新版本 + 资产地址（公开仓库匿名） | 返回正确版本与资产；查询失败/无网络 → 静默降级不打扰、记日志、不误报新版 | 查询实测 |
| RU-02 下载 | 下载更新资产，哈希校验 | 下载完整、哈希一致；运行期窗口枚举计数 0（零弹窗 N7，对齐 SC-02） | 下载记录 |
| RU-03 签名校验 | 客户端内置公钥验证 manifest+包签名 | 篡改/伪造 → 拒绝执行；manifest 结构以 specs/update-manifest-schema.md 为唯一权威（N5 消除双源） | 篡改用例 |
| RU-04 替换与回滚 | 替换前保留上一版本快照；失败自动回滚 | 签名/替换/启动失败 → 回滚上一版本；运行期窗口枚举计数 0（零弹窗 N7） | 回滚用例 |

## 环境前置（执行时经 L8 凭证中心注入，不落盘明文）

- 发布仓库：`https://github.com/Ultima-AI-Studio/Ultima-Agent`（组织，公开，已建）
- 客户端公钥：与发布端私钥成对（发布端持有私钥，公钥注入本卡 RU-03；无公钥 fail-closed 不判通过）
