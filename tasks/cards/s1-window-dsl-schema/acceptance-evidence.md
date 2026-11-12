# 验收证据

- report version: `S1/v0.4`
- phase: `T1-only`
- verdict: `READY_FOR_REVIEW`

## DS-01 / DS-02

- `docs/specs/component-dsl-schema.md` 已从旧“待 TD-01 评估”的缩进 DSL 草案更新为
  已冻结的 A2UI v0.8 扁平邻接表协议。
- 官方仓库固定到 commit `059b8d34874f96c0395dbfe23e6cc8b41cdb0f87`；
  三份 JSON schema 和 LICENSE 的路径、许可证与 SHA256 见
  `evidence/20261021T135937+0800/upstream-pin.txt`。
- Ultima catalog ID 为 `urn:ultima-agent:a2ui:v0.8:window-catalog:v1`；18 个目录项
  均带 propsSchema/tokenRefs/renderer/registered/status，全部 `active=false`。

## DS-03 / DS-04

- RED：`evidence/20261021T135937+0800/red-test.txt`。
- GREEN：`evidence/20261021T135937+0800/green-test.txt`，25/25。
- 官方固定 Row 实例既单独对官方 standard catalog 核对，也作为完整扁平图根验证。
- 合法 Ultima 多布局树通过。
- 未知组件、未知/非法 props、缺必填、重复 ID、悬空、缺根、环、不可达、
  多 surface、外部 catalog、catalog 混用、脚本/eval、远程资源均真实拒绝。
- `final=False` 中间批次返回不可渲染；`final=True` 强制完整图；不声称跨调用流式实现。
- 输入不被修改；运行时不访问网络；图校验使用真实 DFS，不以 mock 替代。

## 冻结与范围

- `evidence/20261021T135937+0800/guardrails-final.json`：
  `check_version_gates` PASS；v0.3 10/10、v0.1 36/36；固定 tag commit 一致；
  生产 `tasks/tasks.json` SHA256 未变；vendor SHA256 全部通过。
- `evidence/20261021T135937+0800/scope-audit.json`：写入均在本 T1 精确域内。
- 独立 T1 审查仍待执行；T2/T3/W5/Owner v0.4 冻结仍待执行。

## 2026-10-24 T1 修复续行开发证据

- 两项回归测试均在实现修复前真实失败，见
  `evidence/20261024T074717+0800/red-test.txt`。
- 最小修复后完整离线套件 28/28 通过，见
  `evidence/20261024T074717+0800/green-test.txt`。
- `check_version_gates`、v0.3 10 项 manifest、v0.1 36 项 manifest、生产
  `tasks/tasks.json` 与固定 vendor 哈希初末一致，见
  `evidence/20261024T074717+0800/guardrails-final.json`。
- 原运行 `20261021T053435036433Z/done.json` 仍为 exit 125、receipt_valid=false、
  state=blocked，且 `final.json` 不存在；见 `old-failure-preservation.json`。
- 这是开发方自测证据，不是独立 T1 验收；T2/T3/W5/Owner 冻结没有推进。

## 2026-10-24 独立审查 I1/I2/I3 修复开发证据

- RED：`evidence/20261024T080632+0800/red-test.txt`，记录资源定位、中间封套/安全、
  支持子集和 1101 节点递归失败的两轮先失败结果。
- GREEN：`evidence/20261024T080632+0800/original-tests.log`，33/33 通过。
- 审查探针开发重放：`evidence/20261024T080632+0800/probe-results.json`，91 个案例
  全部 `pass_=true` 且输入不变；这是开发回归，不是独立审查结论。
- 冻结与来源：`evidence/20261024T080632+0800/guardrails.log`，
  `check_version_gates` PASS；v0.3 10 项、v0.1 36 项 manifest 无 mismatch；生产
  `tasks.json`、三个 vendor schema 与许可证 hash 一致，运行时无需网络。
- 旧失败：重放结果确认旧 `done.json` hash 未变、exit 125、receipt_valid=false、
  state=blocked 且 final 不存在。
- I1：Image/AudioPlayer 仅接受 `asset:local` 或安全分段后缀；网络位置、UNC、
  反斜杠、遍历、绝对路径、未知 scheme、百分号编码和动态 path 定位均拒绝。
- I2：中间帧强制封套/支持并集/props/安全检查；只延期最终 catalog 归属和完整图，
  合法中间帧仍为不可渲染。
- I3：环/悬空/不可达规则保留，1101 节点合法链通过且输入未改变。

## 2026-10-24 最新独立审查续行复核证据

- 新证据目录：`evidence/20261024T081115+0800/`；旧开发与旧独立审查证据均未覆盖。
- `original-tests.log`：当前原套件 33/33 通过。
- `probe-results.json`：从最新独立审查脚本重放 91 个案例，全部 `pass_=true`
  且 `unchanged=true`；该结果是开发复核，不是独立验收签署。
- `guardrails.log`：`check_version_gates` PASS；v0.3 10 项、v0.1 36 项 manifest
  无 mismatch；生产 `tasks.json` 与固定 vendor 来源哈希不变。
- `scope-audit.json`：本轮前后 15 个 T1 产品文件和 108 个保护域文件逐项哈希
  一致；产品实现、规格、注册表、旧独立审查目录、scripts/queue_engine/brain/
  shared/sync 均未被本轮改写。
- `final-readback.json`：独立脚本汇总上述证据，并再次确认旧 exit 125、无 final。

结论仍为 `READY_FOR_REVIEW`：I1/I2/I3 的开发侧回归已通过，监督端需在本进程
退出后另启独立审查。T2/T3/W5/Owner 冻结没有推进。

## 2026-10-24 Video 资源遗漏修复开发证据

- 新证据目录：`evidence/20261024T081918+0800/`；旧开发与独立审查证据未覆盖。
- `red-test.txt`：修复前 Video 的 `//`、UNC、未知 scheme 在 final/final=False
  共 6 个子例未拒绝；合法 `asset:local` 及既有 HTTPS 拒绝分支按预期。
- `original-tests.log`：完整套件 35/35 通过，含 Video 两个批次边界的正反向测试。
- `video-probe-results.json`：Video 10 个 final/final=False 用例均符合预期、输入不变。
- `catalog-url-fields.json`：固定 standard catalog 的资源 URL 组件枚举为
  AudioPlayer、Image、Video，三者现受同一正向白名单约束。
- `probe-results.json`：最新独立审查脚本的 91 项开发重放无 unexpected；只证明
  I2/I3 与既有回归未倒退，不冒充新的独立审查。
- `guardrails.log`：`check_version_gates` PASS；v0.3/v0.1 的 10/36 项 manifest、
  固定 tag、生产 `tasks.json` 与 vendor pin 全部通过末次读回。
- `scope-audit.json`：相对前一开发回执仅四个获准产品文件变化，108 个保护域
  文件一致，最新审查三文件哈希记录在案；scope_violation=false。
- `final-readback.json`：再次确认旧运行 exit125、receipt_valid=false、blocked、
  无 final；本轮为 `READY_FOR_REVIEW` 开发回执，T2/T3/W5/Owner 冻结未推进。
