# 完成语

- report version: `S1/v0.4`
- work order: `wo-s1-composite-window`
- phase: `T1-only`
- task: `s1-window-dsl-schema`
- status: `READY_FOR_REVIEW`
- completed at: `2026-10-21T13:59:37.963237+08:00`

原 T1 的 DS-01~04 已完成实现和开发自检：旧自研缩进 DSL 草案已按已批准
TD-01/ADR-007 对齐 A2UI v0.8；官方 schema/许可证固定到真实 commit 并离线缓存；
Ultima 独立 catalog、props、根/引用/环/可达性与安全默认校验均已落地。

这是“独立 T1 阶段完成、待独立 T1 审查”，不是整张工单完成。T2 renderer 与
ultra 背书、T3 语音四 IO 和双通道真机、完整 W5 和 Owner 冻结均未执行。

- 指定运行时：`H:\UltimaAI\UltimaAgent\tools\python31313\python.exe -B -X utf8`
- RED：实现不存在时真实失败。
- GREEN：25 tests，全部通过。
- 产品实现自修：0/2（命令通道和上游抓取包装调整不改变产品实现）。
- 无 GUI、显示器枚举、播放、录音、麦克风或远程运行时依赖。
- 未 commit/push/tag，未签 Owner 冻结。

## 2026-10-24 T1 修复续行

- report version: `S1/v0.4`
- work order: `wo-s1-composite-window`
- phase: `T1-only`
- status: `READY_FOR_REVIEW`
- evidence: `evidence/20261024T074717+0800/`

在保留原实现与旧失败回执的前提下，复现并最小修复两项 fail-closed 缺陷：
`deleteSurface` 不再能与 `dataModelUpdate` 混批；A2UI v0.8 `valueMap` 不再接受
官方 schema 未定义的递归嵌套。两项均先观察到单测 RED，再最小实现并 GREEN；
完整离线套件 28/28 通过，冻结门与来源 pin 读回通过，自修 2/2。

本结论仅为 T1 开发自测完成、待独立 T1 审查，不是独立验收；T2/T3/W5/Owner
冻结均未执行。原运行 `20261021T053435036433Z` 的 exit 125、无 final 事实保持不变。

## 2026-10-24 T1 独立审查 I1/I2/I3 修复续行

- report version: `S1/v0.4`
- work order: `wo-s1-composite-window`
- phase: `T1-only`
- status: `READY_FOR_REVIEW`
- evidence: `evidence/20261024T080632+0800/`

读取最新独立审查 `result.json` 后完成三项最小修复：Image/AudioPlayer 资源 URL
改为 `asset:local` 正向本地引用白名单；`final=False` 始终校验组件封套、支持
组件并集、props 与安全输入且永不提前 ready；图遍历改为迭代 DFS，合法 1101
节点链不再触发递归上限。两轮修复均先观察 RED，再完成 GREEN，自修 2/2。

完整原套件 33/33 通过；保留的独立审查探针在新开发证据目录重放 91/91
符合预期，不能据此自签独立验收。冻结门、10/36 项 source-manifest、生产
`tasks.json`、vendor pin 与旧 exit 125 无 final 事实均保持不变。T2/T3/W5/Owner
冻结未执行。

## 2026-10-24 T1 最新独立审查续行复核

- report version: `S1/v0.4`
- work order: `wo-s1-composite-window`
- phase: `T1-only`
- status: `READY_FOR_REVIEW`
- evidence: `evidence/20261024T081115+0800/`

本轮重新读取最新独立审查 `result.json`、`review.md` 与 `independent_probe.py`，
并在新证据目录重放当前原套件和同一审查探针。原套件 33/33 通过，91 个审查
用例全部符合预期且输入不变；I1/I2/I3 当前均可复现为已修复行为，因此没有
再次修改产品源码、规格或注册表，也没有制造重复 RED。本轮自修 0/2。

冻结门、v0.3 的 10 项与 v0.1 的 36 项 source-manifest、生产 `tasks.json`、
vendor pin 均通过新鲜读回。旧运行 `20261021T053435036433Z` 继续保持真实
exit 125、receipt_valid=false、state=blocked 且无 `final.json`。这是开发侧
复核回执，不是独立验收；T2/T3/W5/Owner 冻结均未执行。

## 2026-10-24 Video 资源遗漏修复续行

- report version: `S1/v0.4`
- work order: `wo-s1-composite-window`
- phase: `T1-only`
- status: `READY_FOR_REVIEW`
- evidence: `evidence/20261024T081918+0800/`

最新独立审查指出固定 standard catalog 还允许 `Video.url`，而既有正向本地资源
白名单仅覆盖 Image/AudioPlayer。新增测试先真实观察 final 与 final=False 下
scheme-relative、UNC、未知 scheme 共 6 个失败子例，再以一次最小修复把 Video
纳入同一 `asset:local` 规则；Video 未登记 Ultima renderer、未激活且不播放。

完整套件 35/35 通过；最新 91 项旧探针回归无 unexpected，新增 Video 定向探针
10/10 符合预期且输入不变。冻结门、10/36 项 manifest、生产 `tasks.json`、固定
vendor pin 和旧 exit125 无 final 事实均经新鲜读回保持。仅为开发自测回执，等待
监督端另启独立复审；T2/T3/W5/Owner 冻结未执行。
