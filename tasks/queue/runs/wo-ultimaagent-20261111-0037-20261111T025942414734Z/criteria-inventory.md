# 0037 队列体检判据清单与双向反例

- 工单：`wo-ultimaagent-20261111-0037`
- 锁定 revision：`9cfc7fa655747d205279dd4bfde13aae790fd650`
- 审计对象：`scripts/queue-doctor.py` 的 `diagnose()`，以代码分支为准
- 改造前基线：`before.json`，2026-11-11 11:03:51 +08:00，P0=0 / P1=153，`--strict` exit 0
- 枚举口径：8 个基础判据，加 `add()` 在 legacy 记录上实际可生成的 3 个 `LEGACY_` issue code，共 11 个。`VIEW_DRIFT` 在进入全局检查前强制把 legacy 标志复位，因此不存在 `LEGACY_VIEW_DRIFT`；其余 P1 基础判据不会再加 `LEGACY_`。

## T0：现行判据与信号可信度

| # | issue code / 级别 | 断言的事实 | 现行信号（函数与字段） | 误报条件（假阳性来源） | 漏报条件（假阴性来源） | 信号类型 | 可证伪条件（必报 / 必静默） |
|---:|---|---|---|---|---|---|---|
| 1 | `CARD_MISSING` / P0 | UltimaAgent 队列记录存在一张属于该 `work_order` 的卡文件 | `rec.project/work_order` + `_card_for()` 调 `order_naming.resolve_card_path()`，只看返回路径是否 `exists()` | 卡真实存在但命名/别名未被 resolver 覆盖时，返回 `None` 而报缺 | resolver 命中一个文件，但文件内部身份属于另一工单或只是错误占位时，仍沉默 | 按命名/约定字符串匹配 + 文件存在 | `_card_for=None` 必报；返回任意 ROOT 下已声明路径必静默，不读取卡身份 |
| 2 | `CARD_UNTRACKED` / P1 | 已存在的卡在可复现的 Git 提交中可取得 | `_tracked_cards()` 读取 `git ls-files -- tasks/queue`；与 `card.relative_to(ROOT)` 的大小写敏感字符串精确比较 | Windows 上同一跟踪路径仅大小写表现不同会被当未跟踪 | 新卡仅 staged/intent-to-add、尚未进入 HEAD 时也出现在 index 列表，干净检出拿不到却沉默 | Git index 实测，但比较仍依赖路径字符串 | 跟踪集合不给相对路径必报；只要集合含同一字面路径就必静默，不核 HEAD blob |
| 3 | `FROZEN_WITHOUT_TAG` / P0 | `state=frozen` 有一枚可追溯到本单冻结事实的真实 Git tag | `_tags()`；`tag.startswith(order)` 或 `_tag_tokens(note)` 与 tag 集合求交 | 语义 tag 真实存在但不以前缀命名、note 又未登记时误报 | 任意无关/指错 commit 的前缀 tag，或 note 中偶然出现的现存无关 tag，都会让真缺口沉默 | 主要是按命名/约定字符串匹配；仅 tag 集合为 Git 实测 | frozen + 无前缀/note token 必报；放入任意 `order-*` tag 必静默，不核来源与 commit |
| 4 | `FROZEN_WITHOUT_RUN` / P1 | frozen 单有可归属该单且含派发证据的 run | `_run_dirs()` 只取目录名；`any(r.startswith(order))` | 含有效 `dispatch-record.json` 的语义命名 run 不以前缀命名时误报 | 只要建一个同前缀空目录便沉默，没有 `dispatch-record.json` 也通过 | 按目录命名字符串匹配，不读文件事实 | 无前缀目录必报；加入任意 `order-*` 空目录必静默 |
| 5 | `AUDIT_WITHOUT_RUN` / P0，note 命中结论时 P1 | `state=audit` 有可归属该单且含派发记录的真实审计 run | `rec.audit_run` 是否为空；目录是否存在；或任一目录名前 20 字符前缀匹配；空字段时以 note 的 `PASS/通过/审计完成/独立审计` 降级 | 独立审计证据真实存在但 `audit_run` 未回填，或 note 已明确结论，仍产生 issue | `audit_run` 与无关目录发生 20 字符前缀碰撞时沉默；指向存在的空目录也沉默 | 字段/命名字符串匹配，未读 `dispatch-record.json` | 空 `audit_run` 必报；构造相同 20 字符前缀目录必静默，即使目录无派发记录 |
| 6 | `STALE_BLOCKER` / P1 | blocked 理由所述条件现在已不成立 | `note` 是否含 `STALE_BLOCKER_MARKERS` 五个固定词 | note 说“不再占用审计名额”或引用历史措辞，即使阻塞仍有别的有效原因也报过期 | 同一过期事实换同义表述便沉默；命中词的条件若仍成立也无法区分 | 纯关键词字符串匹配，没有现状实测 | note 含任一 marker 必报；用未列同义词描述已消失条件必静默 |
| 7 | `ORPHAN_RUN` / P1 | 每个 run 目录都能由机器证据归属到队列中的工单 | `_run_dirs()` 目录名；与所有 `seen_orders` 做 `r.startswith(o)` | 语义命名 run 内有合法 `dispatch-record.json` 指向现存工单，仍因目录名不匹配而报孤儿 | 无关目录只要以任一工单号开头（含边界碰撞，如 `...00010` 对 `...0001`）便沉默 | 按目录命名字符串匹配，不读派发记录 | 无任一工单前缀必报；给目录加任一工单前缀必静默 |
| 8 | `VIEW_DRIFT` / render exit 非零时 P0、调用异常时 P1 | `render-queue-views.py --check` 已成功比较全部受管视图，且无差异 | `subprocess.run(... --check).returncode`；非零一律视作 drift，异常单独降 P1 | renderer 导入失败、权限错误等运行错误返回非零时，被错报成视图漂移 | checker 自身漏纳某个视图或错误地 exit 0 时，真实差异沉默 | 子进程实测，但把“检查失败”与“发现漂移”混为一类 | 任意非零必报；任意 exit 0 必静默，不验证 checker 覆盖面 |
| 9 | `LEGACY_CARD_MISSING` / P1 | legacy 记录的卡文件存在；与 #1 同事实，仅按政策从 P0 降级 | `state_flag[legacy]` + #1 信号；`add()` 给 P0 code 加 `LEGACY_` | 与 #1 相同：真实卡未被 resolver 命中仍报 | 与 #1 相同：错误身份占位文件被命中便沉默 | 按命名/约定字符串匹配 + policy 降级 | legacy + `_card_for=None` 必报该 code；返回任意路径必静默 |
| 10 | `LEGACY_FROZEN_WITHOUT_TAG` / P1 | legacy frozen 记录有可追溯到该单的真实冻结 tag；与 #3 同事实，仅降级 | `state_flag[legacy]` + #3 信号 | 与 #3 相同：语义 tag 未在 note 登记仍报 | 与 #3 相同：任意前缀 decoy tag 使真缺口沉默 | 按命名/约定字符串匹配 + policy 降级 | legacy frozen 无前缀/note token 必报；任意 `order-*` tag 必静默 |
| 11 | `LEGACY_AUDIT_WITHOUT_RUN` / P1 | legacy audit 记录有可归属的真实审计 run；与 #5 的 P0 路径同事实，仅降级 | `state_flag[legacy]` + #5 信号；空 `audit_run` 且 note 无结论时由 P0 加前缀降级 | 真实独立审计 run 存在但字段和 note 未登记时仍报 | 与 #5 相同：无关目录发生 20 字符前缀碰撞便沉默 | 字段/命名字符串匹配 + policy 降级 | legacy audit 空字段且无 verdict 必报该 code；构造前缀碰撞必静默 |

### T0 对账结论

- `diagnose()` 的实际基础 code 数为 8：`CARD_MISSING`、`CARD_UNTRACKED`、`FROZEN_WITHOUT_TAG`、`FROZEN_WITHOUT_RUN`、`AUDIT_WITHOUT_RUN`、`STALE_BLOCKER`、`ORPHAN_RUN`、`VIEW_DRIFT`。
- legacy 分支额外可达 code 数为 3：`LEGACY_CARD_MISSING`、`LEGACY_FROZEN_WITHOUT_TAG`、`LEGACY_AUDIT_WITHOUT_RUN`。
- 总条目数 `8 + 3 = 11`，与代码可达 issue type 一一对应；没有合并 `FROZEN_WITHOUT_RUN` 与 `AUDIT_WITHOUT_RUN`。
- 四条强制点名判据的可证伪条件已分别写在 #3、#5、#6、#7。

## T1：每条判据的双向反例

以下输出来自未修改的 `9cfc7fa6` 上直接调用 `diagnose()` 的临时目录夹具；夹具只替换状态文件、Git/tag/run 信号和 renderer 返回值，断言走完整 `diagnose()` 主路径。`hits=[]` 是判据在“现实不满足”样本下实际沉默的证明，不是静态推断。

| issue code | 假阳性样本（现实满足，现行仍报）与实际输出 | 假阴性样本（现实不满足，现行仍静默）与实际输出 | 假阴性长期隐身后果 |
|---|---|---|---|
| `CARD_MISSING` | 夹具中卡存在于 resolver 未覆盖的兼容别名路径，`_card_for` 给出当前实际信号 `None`。输出：`CARD_MISSING_FP_alt_existing ... hits=['P0:CARD_MISSING']` | resolver 返回 `tasks/queue/wo-other--mismatch.md`，但文件内部工单身份不是 `wo-fixture-20261111-0001`。输出：`CARD_MISSING_FN_wrong_identity ... hits=[]` | 错卡占位会让目标单在干净环境中无法派发或审计，却永不告警。 |
| `CARD_UNTRACKED` | Windows 同一跟踪文件仅大小写表现为 `TASKS/QUEUE/WO-FIXTURE.MD`，现行大小写敏感比较。输出：`CARD_UNTRACKED_FP_windows_case ... hits=['P1:CARD_UNTRACKED']` | index 中已有 staged-only 路径但 HEAD 尚无 blob，干净检出不可得。输出：`CARD_UNTRACKED_FN_staged_only ... hits=[]` | 本机能看到卡、被验 commit 看不到卡，工单会在交付后失踪。 |
| `FROZEN_WITHOUT_TAG` | frozen 单只有真实语义 tag `semantic-freeze-20261111`，未写入 note。输出：`FROZEN_WITHOUT_TAG_FP_semantic_tag ... hits=['P0:FROZEN_WITHOUT_TAG']` | 仓库只有无关 tag `wo-fixture-20261111-0001-decoy`，前缀碰巧匹配。输出：`FROZEN_WITHOUT_TAG_FN_decoy_prefix_tag ... hits=[]` | 没有冻结锚点或锚点指错 commit 的单会被当作已闭环，后续可在错误基线上推进。 |
| `FROZEN_WITHOUT_RUN` | `semantic-dispatch-run/dispatch-record.json` 可归属该单，但目录不以单号开头。输出：`FROZEN_WITHOUT_RUN_FP_semantic_dispatch_run ... hits=['P1:FROZEN_WITHOUT_RUN']` | 只有 `wo-fixture-20261111-0001-empty/` 空目录，无 dispatch record。输出：`FROZEN_WITHOUT_RUN_FN_empty_prefix_dir ... hits=[]` | 空目录可伪装执行证据，使没有实际派发记录的 frozen 单长期不可追溯。 |
| `AUDIT_WITHOUT_RUN` | `audit_run` 空但 note 有 `独立审计 PASS`；现行仍生成 P1 issue。输出：`AUDIT_WITHOUT_RUN_FP_note_verdict ... hits=['P1:AUDIT_WITHOUT_RUN']` | `audit_run=audit-identity-1234567890`，只有无关目录 `audit-identity-12345-unrelated` 发生前 20 字符碰撞。输出：`AUDIT_WITHOUT_RUN_FN_prefix_collision ... hits=[]` | 无关目录可替代真实审计 run，审计链断裂却不再出现 P0。 |
| `STALE_BLOCKER` | note 明说“已脱离 audit，不再占用审计名额”，当前 marker 仍报过期。输出：`STALE_BLOCKER_FP_resolved_phrase ... hits=['P1:STALE_BLOCKER']` | note 写“等待工作树恢复整洁；当前已经整洁”，使用同义词避开 marker。输出：`STALE_BLOCKER_FN_synonym ... hits=[]` | 已消失的阻塞继续占位，队列会永久停在 blocked 且体检看不见。 |
| `ORPHAN_RUN` | `semantic-run-with-record/dispatch-record.json` 指向现存单，但目录名无单号前缀。输出：`ORPHAN_RUN_FP_dispatch_record_identity ... hits=['P1:ORPHAN_RUN']` | 无关目录名 `wo-fixture-20261111-00010-unrelated` 仅以工单号字符串开头。输出：`ORPHAN_RUN_FN_prefix_collision ... hits=[]` | 真孤儿目录可借前缀碰撞隐藏，磁盘证据与队列会持续漂移。 |
| `VIEW_DRIFT` | renderer 因 `ImportError: renderer unavailable` exit 1，未完成比较，却被报成 drift。输出：`VIEW_DRIFT_FP_checker_error ... hits=['P0:VIEW_DRIFT']` | checker 漏管一个视图但 exit 0。输出：`VIEW_DRIFT_FN_checker_blindspot ... hits=[]` | 未纳入 checker 的视图可永久与 JSON 分叉，体检仍给出无漂移结论。 |
| `LEGACY_CARD_MISSING` | legacy 卡存在于 resolver 未覆盖路径。输出：`LEGACY_CARD_MISSING_FP_alt_existing ... hits=['P1:LEGACY_CARD_MISSING']` | resolver 命中错误身份占位文件。输出：`LEGACY_CARD_MISSING_FN_wrong_identity ... hits=[]` | 历史卡的真实身份丢失，后续追溯得到错误工单。 |
| `LEGACY_FROZEN_WITHOUT_TAG` | legacy frozen 单只有真实语义 tag。输出：`LEGACY_FROZEN_WITHOUT_TAG_FP_semantic_tag ... hits=['P1:LEGACY_FROZEN_WITHOUT_TAG']` | legacy 单只有无关前缀 decoy tag。输出：`LEGACY_FROZEN_WITHOUT_TAG_FN_decoy_prefix_tag ... hits=[]` | 历史冻结锚点失真后，回滚与审计会引用无关提交。 |
| `LEGACY_AUDIT_WITHOUT_RUN` | legacy 单有语义命名真实审计 run，但 `audit_run` 与 note 未登记。输出：`LEGACY_AUDIT_WITHOUT_RUN_FP_real_run_unlinked ... hits=['P1:LEGACY_AUDIT_WITHOUT_RUN']` | legacy `audit_run` 与无关目录前 20 字符碰撞。输出：`LEGACY_AUDIT_WITHOUT_RUN_FN_prefix_collision ... hits=[]` | 历史审计链被无关目录冒充，后续复核无法找到原始执行证据。 |

### 历史已发生的 10 条假阳性

下表是首轮活跃窗口 12 条 P0 中的 10 条误报：8 条 semantic tag 被 `FROZEN_WITHOUT_TAG` 的工单号前缀规则漏读；2 条独立审计有 note/tag 结论但没有派发器 `audit_run`，被 `AUDIT_WITHOUT_RUN` 当成 P0。0025 是当时真实缺 tag，0028 是只读评审却误设 frozen，二者不是假阳性，故不列入。

| 现行 code | 工单 | 现实证据（历史已发生） | 现行误报原因 |
|---|---|---|---|
| `FROZEN_WITHOUT_TAG` | `wo-ultimaagent-20261101-0013` | `ultimaagent-mainbrain-qwen3-8b-cleanup-20261101` → `89503678f4a670f16cf86e418fab0f2a5a1fe5c5` | tag 不以工单号开头 |
| `FROZEN_WITHOUT_TAG` | `wo-ultimaagent-20261101-0014` | `ultimaagent-kws-user-entry-20261101` → `b4fb88a37660d081fce43fd8da4ab50e876b6708` | tag 不以工单号开头 |
| `FROZEN_WITHOUT_TAG` | `wo-ultimaagent-20261101-0015` | `ultimaagent-asr-correction-20261101` → `c0f0c7bb4d35b4a26fe0935e21ba97c1a450eb07` | tag 不以工单号开头 |
| `FROZEN_WITHOUT_TAG` | `wo-ultimaagent-20261101-0016` | `ultimaagent-reply-constraint-routing-20261101` → `a3fca7c3751e8a2f3227c29b6eb3c09455ae0490` | tag 不以工单号开头 |
| `FROZEN_WITHOUT_TAG` | `wo-ultimaagent-20261101-0017` | `ultimaagent-reply-constraint-structured-20261101` → `5ef3ec30a8635b3232d78a1edcabdc7362d9ae07` | tag 不以工单号开头 |
| `FROZEN_WITHOUT_TAG` | `wo-ultimaagent-20261103-0022` | `ultimaagent-middleware-v1-20261103` → `34ac0c79bfc4252c46bd5128dcc25f5caa4c3d58` | tag 不以工单号开头 |
| `FROZEN_WITHOUT_TAG` | `wo-ultimaagent-20261103-0023` | `ultimaagent-jarvis-p0-20261103` → `baa3619861cae09e407836d7db8b6d9cf4283143` | tag 不以工单号开头 |
| `FROZEN_WITHOUT_TAG` | `wo-ultimaagent-20261108-0026` | `ultimaagent-audit-hardening-20261108` → `f0cad32b9314d68571a67a8f05e484642ef5c977` | tag 不以工单号开头 |
| `AUDIT_WITHOUT_RUN` | `wo-ultimaagent-20261101-0019` | 独立审计 note + `ultimaagent-wekws-offline-proof-20261101` → `b821333aa3c556c6c048440b727688eac86b90d1` | 独立审计不经派发器，`audit_run` 为空被当作链路断裂 |
| `AUDIT_WITHOUT_RUN` | `wo-ultimaagent-20261101-0020` | 独立审计 note + `ultimaagent-voice-next-live-pass-20261101` → `3a4f82537bc007ff0bd4c7ae3f0d1acc981f65a3` | 独立审计不经派发器，`audit_run` 为空被当作链路断裂 |

### 当场复现命令与输出

下列 10 个命令均在锁定 revision 的当前仓执行；每个 tag 都由 `git tag --list <exact>` 返回自身，随后 `git rev-parse <tag>^{commit}` 返回上表 commit。已超过 Gate 要求的至少 5 条。

```text
git tag --list ultimaagent-mainbrain-qwen3-8b-cleanup-20261101
ultimaagent-mainbrain-qwen3-8b-cleanup-20261101
git tag --list ultimaagent-kws-user-entry-20261101
ultimaagent-kws-user-entry-20261101
git tag --list ultimaagent-asr-correction-20261101
ultimaagent-asr-correction-20261101
git tag --list ultimaagent-reply-constraint-routing-20261101
ultimaagent-reply-constraint-routing-20261101
git tag --list ultimaagent-reply-constraint-structured-20261101
ultimaagent-reply-constraint-structured-20261101
git tag --list ultimaagent-wekws-offline-proof-20261101
ultimaagent-wekws-offline-proof-20261101
git tag --list ultimaagent-voice-next-live-pass-20261101
ultimaagent-voice-next-live-pass-20261101
git tag --list ultimaagent-middleware-v1-20261103
ultimaagent-middleware-v1-20261103
git tag --list ultimaagent-jarvis-p0-20261103
ultimaagent-jarvis-p0-20261103
git tag --list ultimaagent-audit-hardening-20261108
ultimaagent-audit-hardening-20261108
```

### T1 Gate 结论

- 11/11 issue code 均有假阳性与假阴性各 1 个，且全部由未修改代码的 `diagnose()` 主路径实际运行。
- 11/11 假阴性均有 `hits=[]` 输出证明沉默，并逐条记录长期后果。
- 10 条历史已发生假阳性已全部列出；其中 10 个真实 tag 均现场 `git tag --list` + `rev-parse` 复现。
- T0/T1 产物先于任何 `scripts/queue-doctor.py` 或测试改动落盘。
