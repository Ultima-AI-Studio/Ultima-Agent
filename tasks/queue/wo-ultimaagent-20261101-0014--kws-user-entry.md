# 工单 wo-ultimaagent-20261101-0014 ｜ UltimaAgent ｜ 工程 ｜ KWS 唤醒词用户入口 + 持久化

> 原单 ID：`wo-ultimaagent-20261101-0014` ｜ 显示标题：UltimaAgent｜工程｜KWS 唤醒词用户入口+持久化（工单 E）
> 依据：G-DISPATCH-001 自主推进版 + G-TASKFLOW-001 ｜ 方案：`docs/plans/plan-voice-three-issues-20261101.md`（2026-11-01 定稿，Owner 拍板"整体派发"）
> 北极星：贾维斯（自然人机交互：说"把唤醒词改成XX"即生效并记住）
> 创建：2026-11-01 ｜ 状态：待派发

---

## 一、目标与范围

### 1.1 目标（Result）

用户**用自然语言改唤醒词并持久化记住**：
- 语音说"把唤醒词改成星期五 / 以后叫星期五唤醒我" → 模型听懂 → 改词生效（热重载，同 PID 不重启）→ 播报确认（"唤醒词已改为星期五"）→ **写回 `voice-profile.json` 的 `wakeword.custom`**，daemon 重启后仍生效。
- 一致性收敛：当前 `voice-profile.json custom=null` 但 `models/sherpa/kws/keywords.txt` 含"查天气"行（双源不一致），核对来源后回填或清理并落盘记录。

### 1.2 范围冻结（边界，禁止越界）

- **只做**：interaction 意图层新增"改唤醒词"分支 + 调 `voice_profile.save_user_override` 写回 + 一致性核对 + 对应测试与证据。
- **禁止修改**：
  - KWS 模型 / onnx / tokens.txt / `keywords.txt` 现有 6 变体与 ULTIMA 行（改词走 `scripts/kws_reconfig.py` 公开 CLI，不手改文件）；
  - KWS 全局参数数值（`docs/specs/kws-wakeup-params-baseline.md` 冻结基线，零漂移）；
  - `voice_profile.py` 既有逻辑（0003 冻结）——**只调公开接口** `save_user_override` / `load_profile`，如需接口调整必须申报；
  - daemon 音频栈（音量/并发/采集链路，感知层已收口，本单不碰）；
  - W6/HUD UI 大改（语音入口为先，UI 设置项后续单接）；
  - 守护进程不得杀/重启（热重载必须同 PID）。

### 1.3 写域

| 文件 | 动作 | 说明 |
|---|---|---|
| `src/brain/interaction.py` | 修改 | 新增"改唤醒词"意图分支（近音容忍：改/换/叫/唤醒词），调用 kws_reconfig + save_user_override + 生成播报确认文本 |
| `scripts/kws_reconfig.py` | 只读调用 | `--replace/--add` 改词（0009 交付，不改其实现） |
| `src/brain/voice/voice_profile.py` | 只读调用 | `save_user_override({"wakeword":{"custom":...}})` 写回 profile（0003 冻结，只调接口） |
| `config/voice-profile.json` | 运行期写回 | `wakeword.custom` 持久化（"记住"） |
| 测试文件 | 新建 | 意图命中 + 写回断言 + 重启语义断言 |
| `docs/reports/stage-kws-user-entry-20261101.md` + evidence/ | 新建 | 阶段报告与证据 |

---

## 二、DoR 就绪门

| # | 就绪项 | 判定 | 证据 |
|---|---|---|---|
| 1 | 验收 Gate 可判定 | ✅ 封闭清单（§四） | 改词生效/记住/一致性/回归 |
| 2 | 无未决依赖 | ✅ 前置 0009 completed（改词 CLI 已冻结） | 全局登记 0009=completed |
| 3 | 写入域已声明 | ✅ §1.3 | — |
| 4 | 推理强度已声明 | ✅ T0 medium / T1 medium / T2 medium / T3 high / T4 low | — |
| 5 | 禁止项已写 | ✅ §1.2 | — |

---

## 三、执行步骤（T0→T4，逐 T Gate PASS 再进下一条）

### T0 环境盘点（medium）
- [ ] C1 读 `src/brain/interaction.py` 意图链路（_normalize_utterance / _FUZZY_* / _try_agent_fallback），确认新增意图分支的接入点与近音容忍机制。
- [ ] C2 读 `scripts/kws_reconfig.py` 真实 CLI 行为（--replace/--add 的语义、备份、热重载触发方式），确认只读调用即可完成改词。
- [ ] C3 读 `voice_profile.save_user_override` / `load_profile` 公开签名（只读，不修改），确认写回 profile 的方式与校验逻辑。
- [ ] C4 一致性核对：`config/voice-profile.json`（custom=null）vs `models/sherpa/kws/keywords.txt`（含"查天气"行）——排查来源（0009 测试/训练痕迹/manual 改动），给出收敛决定（回填 custom 或清理行）并落盘说明。
- [ ] C5 证据落盘 `docs/reports/evidence/kws-user-entry/t0-env-probe.txt`。
- Gate：C1-C5 全绿 → T1。

### T1 意图分支 + 写回实现（medium）
- [ ] C1 interaction 新增意图：命中"改/换/叫 + 唤醒词/叫醒"句式（近音容忍，含"唤醒词"同义误识如"唤新词/花新词"登记观测）→ 解析新词文本。
- [ ] C2 改词链路：调 `kws_reconfig.py`（优先 --replace 语义或按工单 A 实际行为）→ 热重载日志出现（pid 不变）→ 调 `save_user_override({"wakeword":{"custom": <新词>}})` 写回 profile。
- [ ] C3 播报确认：生成"唤醒词已改为XX"文本（走现有 TTS 链，不新写播放逻辑）。
- [ ] C4 一致性收敛：按 T0-C4 决定执行（回填 custom 或清理 keywords 行），profile 与 keywords.txt 对齐。
- Gate：注入"把唤醒词改成星期五"→ 改词+写回+确认文本三者都发生；证据 `t1-entry.txt`。

### T2 自动化验证（medium）
- [ ] C1 意图命中单测：多句式变体（改成/换成/以后叫/唤醒词改成）注入 → 意图识别正确。
- [ ] C2 持久化断言：save_user_override 后 profile custom=新词；模拟 load_profile → custom 生效。
- [ ] C3 重启语义：模拟 daemon 重启加载 → 新词在 keywords 且可被 `apply_to_daemon` 推导（不真重启 daemon）。
- [ ] C4 回归：`tools/venv-openjarvis/Scripts/python.exe -m pytest src -q` 全绿 + voice-profile/语音专项全绿（工程验收必须用 venv-openjarvis 解释器）。
- Gate：C1-C4 全绿 → T3。

### T3 收口（high）
- [ ] C1 基线零漂移核对：`kws-wakeup-params-baseline.md` 数值零变动（仅可追加变更记录）。
- [ ] C2 冻结 tag：`git tag ultimaagent-kws-user-entry-20261101`（先 commit，`git rev-parse` 可解析）；**推送用免代理：`git -c http.proxy= -c https.proxy= -c http.https://github.com.proxy= push`**。
- [ ] C3 阶段报告 `docs/reports/stage-kws-user-entry-20261101.md`（Gate 证据 + CLI 输出 + 热重载日志 + 一致性收敛记录）。
- Gate：C1-C3 全绿 → T4。

### T4 回执（low）
八字段（见 §五）。

---

## 四、验收口径（封闭清单，全绿才过）

| Gate | 判定 | 证据位置 |
|---|---|---|
| 机制 | 语音命令改词 → 热重载成功（daemon 日志 pid 不变）+ profile custom 写回成功 | t1-entry.txt + voice-listen.log 摘录 |
| 功能 | 新词可唤醒（离线 KWS 断言）；播报确认文本生成；重启语义下 custom 仍生效 | t2/ |
| 一致性 | profile custom 与 keywords.txt 对齐（收敛决定落盘） | stage 报告 |
| 回归 | pytest 全量绿（venv-openjarvis）+ 专项绿 | t2/ |
| 冻结 | tag `ultimaagent-kws-user-entry-20261101` 存在且可解析 | git tag -l |

---

## 五、执行端回执（八字段，必填）

| 字段 | 值 |
|---|---|
| 链路号/工单号 | wo-ultimaagent-20261101-0014 |
| 执行端 | Codex（gpt-5.6-sol，codex exec） |
| 完成状态 | 已完成 / 阻塞 / 已终止（三选一） |
| 根因结论 | （一句话） |
| 产出路径 | src/brain/interaction.py、测试、stage 报告、evidence/ |
| 验收证据 | T0-C1~C5 / T1 / T2-C1~C4 / T3-C1~C3 逐条 PASS + pytest 摘要 + 热重载日志 |
| 越界声明 | 无=明确写"无"；含未动范围（KWS 模型/参数基线/voice_profile 逻辑/daemon/UI） |
| 环境声明 | 真机：热重载 pid 实测；如仅离线验证须写"仅离线预期，真机待验收" |

## 附：推理强度
T0 medium ｜ T1 medium ｜ T2 medium ｜ T3 high ｜ T4 low
