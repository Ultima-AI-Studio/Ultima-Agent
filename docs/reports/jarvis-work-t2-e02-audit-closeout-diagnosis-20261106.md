# E02 冷导入判定卡点：审计拒绝证据补齐（诊断报告）

日期：2026-11-06
范围：T2 / E02 / source13 冷导入单例 FAIL（run `726b5883-f57c-4693-899e-17c9d1719b22`）
结论：**卡点在代码侧的证据缺口，不在环境、不在服务。**

## 一、结论先行

1. 环境侧已排除：Ollama 服务在跑（PID 5708，11434 端口有监听），运行时对账结果为 `PASS_RUNTIME_RECONCILIATION`，"环境被锁"这条已经不成立。
2. 真正的卡点：`profile.py` 的审计器被拒绝时**只记事件次数、然后抛异常**，失败封存只落 `failure-summary.json` 与 `closed-index.json`，**从不落 `audit.denied` 明细**；上层只把 `audit_clean / scope_clean / eager_clean` 三个布尔塞进计数器。于是 E02 只能看到三个 `false`，无法回答"哪个事件、在哪一行被拒"。
3. 本次已在**独立诊断包**内补上证据采集：拒绝时记录事件名与调用帧（最多 6 帧、最多 64 条），失败封存时额外写 `audit-denied-events.json`；**候选判定逻辑一行未动**。
4. 验证：新增 3 条离线契约测试，全量固定契约 **564 项全通过（564 passed / exit_code=0）**，白名单、依赖、包内文件三项核对均为 `True`。
5. 从失败 run 自己的产物里已定位到失败机制：**产品本身是成功的**（研究文件已写出、字节与哈希对得上、确认回执齐全），失败发生在收尾判定那一步；三个 `false` 里只有一个是真的原因，`eager_clean` 是被提前中断带出来的假阳性（详见第二节之二）。
6. 仍缺的只剩一个值：**"哪个事件、哪一行被拒"**。它只能由一次实跑产生，而这次实跑需要授权文件，授权文件由独立的 Root 端签发、原包已消费，主脑无法自签（详见第六节）。

## 二、根因（代码层，按函数定位）

| 位置 | 现状 | 后果 |
| --- | --- | --- |
| `profile.py` `class WorkerAudit.__call__` | 命中 `socket.* / subprocess.* / os.system` 等即 `denied[event]+=1` 后抛 `ValueError` | 只留事件名与次数，不留调用帧，不留上下文 |
| `profile.py` `def audit_closeout(audit)` | 本可输出 `clean / denied` | 结果从未落盘 |
| `profile.py` `def run_profile` 失败分支 | 只写 `failure-summary.json`、`closed-index.json` | 失败封存里没有审计明细 |
| `profile.py` `def selected_counters` | 把 `audit_clean / scope_clean / eager_clean` 三个布尔写入计数器 | 下游只能看到三个 `false` |
| `profile.py` `def mechanical_counters` | 三项必须为 `True`，否则不判为候选 | 三个 `false` 直接堵死，且无法定性 |

## 二之二、这次 run 的失败机制（已从产物直接定位）

依据失败 run 自己的产物，不需要重跑：`process/worker.stderr`、`control/terminal.json`、`worker/case/profile-first-result.json`、`worker/case/failure-summary.json`。

**失败栈**（原文摘录）：

```
profile.py line 570, in private_scope
    require(not dirty,'Private scope refusal or cleanup invalidates outcome')
ValueError: Private scope refusal or cleanup invalidates outcome
```

（新诊断包里同一行位移到 591，逻辑未改。）

**产品侧是成功的**：`product_status=succeeded`；`research.md` 已写出 711 字节、sha `a7e7e590…` 与记录一致；`ack_attempted / ack_admitted / ack_verified` 全为真；`file_verified_before_ack=True`；`native_posts=6`、`sdk_inference_start=6`、`sdk_inference_end=6`、`writer_end_confirmed=True`、`observer_incomplete=False`。

**收尾判定 `dirty` 共 7 个可能来源，逐项核对结果**：

| 来源 | 实测值 | 是否触发脏 |
| --- | --- | --- |
| `audit.denied` 非空 | 非空（`audit_clean=False` 即由此得出） | **是（唯一真因）** |
| `budget.refused` | 0（`metadata_refused=0`） | 否 |
| `browser.refused` | 0（`browser_refused=0`，含 DNS） | 否 |
| `browser.dns.refused` | 0（`ssrf` 全部记录 `refused=0`） | 否 |
| research 客户端重复构造 | `research_constructors=1`，无重复 | 否 |
| 各计数器 `refused` | `owner_refused=0`、`research_refused=0`、`native_refused=0` | 否 |
| `cleanup.errors` | 空（`secondary_errors=[]`） | 否 |

**由此得出两点**：
1. 三个 `false` 里真正的、唯一的原因是**审计器记录了一次拒绝**；其余六个来源全部干净。
2. `eager_clean=False` 是**假阳性**：`private_scope` 的收尾判定先抛异常，此时 `ExitStack` 还没退出，`own_ollama_types` 的 `finally`（它才会算 `clean`）根本没执行，`eager_clean` 取到的是初始化时的默认 `False`。它不代表 eager 阶段独立出了故障。

也就是说：E02 的失败不是"产品做不出来"，而是"产品做成了，但过程中有一次外部调用被审计器拦下、异常被吞掉只留计数，于是收尾判定判脏"。差的就是这一个事件名与行号。

## 三、本次改动（仅新增证据，不改变判定）

产物目录：`H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-audit-closeout-20261106\`

| 文件 | 位置 | 改动 |
| --- | --- | --- |
| `profile-preparation/profile.py` | L184 `_audit_site` | 取最多 6 帧调用栈，格式 `文件名:行号:函数名`；**不记录参数值**；异常吞掉返回空帧 |
| 同上 | L180 `_SITE_LIMIT=64` | 单次失败最多记 64 条站点，超出置截断标记 |
| 同上 | L195 `class WorkerAudit` | 新增 `denied_sites`、`denied_sites_truncated`；拒绝分支计数后追加站点 |
| 同上 | L493 `audit_closeout` | 输出增加 `denied_sites` 与 `site_truncated`，原有 `clean / denied` 语义不变 |
| 同上 | L1551 `write_audit_evidence` | 新增：失败封存时写 `audit-denied-events.json`，已存在则返回 `None` 不覆盖 |
| 同上 | L2143 `run_profile` 失败分支 | 写完 `failure-summary.json` 后调用 `write_audit_evidence(folder, scope['audit'])` |
| `profile-preparation/test_profile.py` | 文件尾部 | 新增 3 条契约测试（见下） |
| `profile-preparation/manifest.json` | — | `package_root` 指向新包；`members` 重算哈希；`test_ids` 561 → 564 |

新增测试：
- `test_refused_event_receipt_names_event_without_arguments`：拒绝时记下事件名与帧格式，且参数值（`/private/target`、`-rf`）不出现在收据里。
- `test_failure_audit_receipt_is_written_once`：首次写返回摘要，内容为正确收据，重复调用返回 `None`（不覆盖）。
- `test_failure_audit_receipt_clean_and_bounded_sites`：66 次拒绝 → 计数 66、站点 64、截断标记为真；干净审计 → `clean=True`、`denied={}`、站点为空。

## 四、验证结果

**新增 3 条测试**：`3 passed, 561 deselected`，退出码 0。

**全量固定契约**（`run_checks.py --contracts`，专用解释器 `tools\venv-openjarvis\Scripts\python.exe` 3.13.16）：

| 判据 | 值 |
| --- | --- |
| 退出码 | 0 |
| 用例数 | 预期 564 / 实际 564 |
| 白名单完全一致 | True |
| 依赖未变 | True（1462 项） |
| 包内 5 个文件未变 | True |
| 限定口径 | `OFFLINE_SYNTHETIC_CONTRACTS_ONLY` |
| 结果 | `564 passed in 62.09s` |

运行目录：`code\profile-preparation-contracts-20261106T121302966692Z-77b78c80`（保留）；前两次失败运行目录已删除。

**两次失败的原因（都已排除，不是代码回归）**：
1. 只搬了 4 个成员文件，测试通过父目录访问 `cold/cold_import_probe.py`、`profile-adapter.py` 等兄弟资源 → 96 failed / 8 errors。补齐证据树（除 40MB `code/`）后消失。
2. 我方 shell 环境带 `DOUBAO_OFFICE_FORWARD_PROXY` 等代理变量，触发 `own_ollama_types` 的"环境注入"拒绝 → 13 failed。清理后消失。

**重要提醒**：跑这个契约必须在不带 `*_PROXY`、`OLLAMA_*`、`PYTHONPATH` 的干净 shell 里执行，否则会误判成代码问题。

## 五、边界（明确没做的事）

- 没有修改候选判定：`selected_counters` / `mechanical_counters` 一行未动，`audit_clean / scope_clean / eager_clean` 的语义与门限保持原样。
- 没有覆盖原精确绑定包 `e02-source13-cold-import-20261106`：原包只读，未写入任何内容。
- 没有跑真实冷导入，也**无法由主脑自行跑**：原包 `code\entry.py` 把包根写死在源码里，并强制校验"脚本自身路径必须等于包根下的 `code\entry.py`"；完整一轮要先有 Root 端签发的 `release/release.json`（原包该目录已消费为空），子进程模式又要等父进程先写 `entry-grant.json`，没有父进程会一直空转。自行伪造授权文件等于把"独立 Root 控制"这条前提拆掉，所以没有做。
- 没有改父级 `manifest.json` / `entry-manifest.json`：它们仍绑定原包 `profile.py`（`5c837adb…`）与 `test_profile.py`（`c9a3142c…`）的哈希；新包只改了自己的 `package_root / members / test_ids`。
- 没有走独立准备评审：原 README 要求"整包改动需独立准备评审"，本次未触发。

## 六、下一步（需拍板，按代价从小到大）

1. **只差一个值，且必须由授权方产生**：让 Root 端签发一次新的 `release.json`（不是主脑自签），用本诊断包跑一轮，失败时读 `runs\<run>\audit-denied-events.json`，就能看到"哪个事件、哪个文件第几行"。这是唯一能真正闭合 E02 的动作。
2. **再省一步的替代**：把审计落盘点从"`run_profile` 失败分支"前移到"`private_scope` 收尾判定抛出之前"，这样即使不判脏、也能随时看到拒绝记录；改动更小，但仍要一次授权才能取到历史那次 run 的值。
3. **要纳入正式流程**：把本诊断包提交独立准备评审，通过后再考虑替换正式包内的 `profile.py` / `test_profile.py`。

## 七、产物清单

- 诊断包：`H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-audit-closeout-20261106\`
- 改造后 `profile.py`：sha256 `288e99edbd535349fc0945d7740ccb0d7edc23d30120ba0616c98ade4b7780e3`
- 改造后 `test_profile.py`：sha256 `12240855144452ec91b267a1a712ed8ed91e2480a18eee492e47eecfc27bfa5a`
- 全量契约 receipt：`code\profile-preparation-contracts-20261106T121302966692Z-77b78c80\receipt.json`
- 原包（只读参照）：`...\e02-source13-cold-import-20261106\profile-preparation\profile.py`（`5c837adb…`）
