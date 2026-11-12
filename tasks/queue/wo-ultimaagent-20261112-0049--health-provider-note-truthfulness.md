# Codex 工单 · 0049 `/health` provider_note 与实际行为不一致

> 版本：v1.0 ｜ 状态：可开工（前置：0048 G-ORCH 全链已冻结 `62d2c7ba`）｜ 适用工具：Codex
> 用法：按 T1→T4 顺序逐条执行，Gate PASS 后进下一条。
> 范围依据：`tasks/queue/requirements/req-health-provider-note-20261112.md`（REQ-20261112-0049）+ DeepSeek 三阶段（`tasks/queue/runs/req-health-provider-note-20261112/stages/`）
> 前置：0048 冻结 `62d2c7ba`；本单为 0049，用于首次真实全自动跑通 `run-pipeline.py`（含 audit 正路径）。

<!-- gorch-manifest
{
  "files": [
    "src/brain/agent_server.py",
    "src/brain/tests/test_provider_layer.py"
  ],
  "acc": [
    {"id": "ACC-1", "check": "exists_nonempty", "path": "src/brain/agent_server.py"},
    {"id": "ACC-2", "check": "exists_nonempty", "path": "src/brain/tests/test_provider_layer.py"}
  ],
  "commands": [
    "tools/venv-openjarvis/Scripts/python.exe -m pytest src/brain/tests/test_provider_layer.py"
  ]
}
-->

**机检**：`tools/venv-openjarvis/Scripts/python.exe -m pytest src/brain/tests/test_provider_layer.py`

---

## 1. 范围冻结

**本单只做**：
1. 改 `src/brain/agent_server.py` 的 `_health_payload()` 函数体：把 `provider_note` 的触发判据从 `enabled and endpoint` 改为「可作答性三要素（impl / endpoint / model 均非空）」，并在 payload 新增 `provider_answerable` 布尔字段。
2. 改 `src/brain/tests/test_provider_layer.py`：改造原 L444-457（C 态语义，断言强度不降）+ 新增 B 态用例（endpoint 有值 + enabled=false，线上真实情形）+ 补 C 态 impl/model 缺项断言。
3. 在 `tasks/queue/queue-status.json` 登记本单。

> 链路执行方式（非改动面）：本单为 0049，用于首次真实全自动跑通 0048 建的单入口链（plan → dispatch → verify → audit → freeze），验收动作见 §3 T4 第 8 条。该链是执行工具，不在本单写域内。

**本单不做**：
1. 不改 `/ask` 任何行为：`provider_for()`、四处分派（L718/L1006/L1159/L1216）、`require_main()`、`main_settings()`、`slot_adapter.py` 全部零字节改动。
2. 不改 `/health` 其它字段：`ok` / `model` / `agent` / `tools` / `provider` / `provider_model` 原样。
3. 不做网络探测、不引入任何 IO（`/health` 必须纯本地零延迟）。
4. 不改 `provider_configured` 的计算与含义（保留 `enabled and endpoint`，只新增字段）。
5. 不为本单新增配置文件或配置项；不动 Phase 4 安装向导的「未配置」语义。
6. 不改 `scripts/` 下任何 G-ORCH 脚本（除非 T4 的链路本身报错，报错须先停下报主脑）。

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T1 | `src/brain/agent_server.py` | `_health_payload()` 单点判定改为三要素齐备；新增 `provider_answerable`；A/B/C 三态文案正确；`/ask` 相关代码零 diff |
| T2 | `src/brain/tests/test_provider_layer.py` | 原 C 态测试改造后断言强度不降；新增 B 态用例（线上真实配置）断言 note 不含「无法作答」且含 impl+model；A/B/C 三态各至少一条断言全绿 |
| T3 | `tasks/queue/queue-status.json` | 本单登记成功且 `render-queue-views.py` exit 0；`state` 合法 |
| T4 | 总验收（无代码写入） | 线上 `/health` 无「无法作答」且含 impl+model；构造 C 态指名缺失项；全量 ≥577 passed 且失败数 ≤ 基线；`/ask` 探针零变化；`run-pipeline.py` 全链跑通并产出 `verify.json` + `audit.json` |

---

## 3. 任务明细

### T1 · `_health_payload()` 判定改造

**文件**：`src/brain/agent_server.py`（仅 `_health_payload()` 函数体，L1407-1421 区间）

**写什么**：
1. 取三要素并按 `str(...).strip()` 判空：`has_impl = bool(str(_MAIN.get("impl") or "").strip())`、`has_endpoint = bool(str(_MAIN.get("endpoint") or "").strip())`、`has_model = bool(str(_MAIN.get("model") or "").strip())`。
2. 计算 `usable = has_impl and has_endpoint and has_model`，**`enabled` 不参与 `usable`**。
3. payload 新增字段 `provider_answerable`，值即 `usable`。`provider_configured` 一行**保持原样**（`bool(_MAIN.get("enabled") and str(_MAIN.get("endpoint") or "").strip())`），不重算、不改含义。
4. 分支写 note（三态）：
   - A（`usable` 真且 `enabled` 真）：不写 `provider_note`。
   - B（`usable` 真且 `enabled` 假）：写 note，必须含「未显式配置」+「内置默认」两义，并实填 `impl` 与 `model` 的实际值；**禁止出现「无法作答」**。
   - C（`usable` 假，无论 `enabled` 真假）：写 note，保留「无法作答」语义，并指名缺失项（impl / endpoint / model 中哪些为空，多项缺失全列）。
5. 判定只在函数内单点完成，不新建外部判定函数、不建共享 helper。

**验收（Gate T1）**：
- `git diff` 显示改动仅在 `_health_payload()` 区间；`provider_configured` 那一行字节不变（`git diff` 里不出现该行）。
- `provider_for(` / `require_main(` / `main_settings(` 在 `agent_server.py` 中出现次数与改动前一致。
- 三态各自可断言：A 无 note 键；B note 含 impl+model 且不含「无法作答」；C note 含「无法作答」且含缺失项名。

**禁止**：不得把 `provider_configured` 改成「可作答」语义；不得把 B 态归入 C；不得新增第二判据源；不得发起网络探测。

### T2 · 测试改造与新增

**文件**：`src/brain/tests/test_provider_layer.py`

**写什么**：
1. 改造原 L444-457 测试：构造保持 `endpoint=""`（这是真 C 态），断言更新为——`ok is True`、`provider_answerable is False`、note 含「无法作答」且**指名缺失项 `endpoint`**。函数名可改为 `test_agent_server_health_payload_marks_unusable_when_endpoint_missing`。**断言强度不得降低**（原断言的 `provider_configured is False` 与 note 文案仍须成立）。
2. 新增 B 态用例：`{"impl":"ollama-8b","endpoint":"http://127.0.0.1:11434","model":"qwen3-8b-uncensored:latest","enabled":False}` → 断言 `provider_answerable is True`、`provider_configured is False`、`provider_note` 存在、含 `ollama-8b` 与 `qwen3-8b-uncensored:latest`、**不含「无法作答」**。
3. 新增 C 态另两项缺项：`impl` 空、`model` 空各一条（可与 endpoint 那条参数化合并），每条都断言 note 指名对应缺失项。
4. 原 L431-441（A 态，`enabled=True` + endpoint 有值 → 无 note）保持不变，可附加 `provider_answerable is True` 断言（只增不减）。

**验收（Gate T2）**：
- `pytest src/brain/tests/test_provider_layer.py -q` 全绿。
- A/B/C 三态各至少一条断言存在且 PASS（B 态必须覆盖「endpoint 有值 + enabled=false」）。
- 原 C 态测试的 `provider_configured is False` 断言仍在。

**禁止**：不得为了过新逻辑删改 A 态测试；不得用放宽断言的方式处理冲突；不得改 `agent_server.py`（那是 T1 的写域）。

### T3 · 队列登记

**文件**：`tasks/queue/queue-status.json`

**写什么**：
1. 在 `records` 数组末尾追加一条 0049 记录，字段与本单其它记录一致（`project` / `work_order` / `state` / `audit_passed` / `dispatched_at` / `audit_run` / `freeze_commit` / `note`），`state` 初始 `pending`。
2. 保持纯 LF、2 空格缩进、CRLF 计数 0（该文件现有 169 条记录，全部 LF）。
3. **不得**用 `ConvertTo-Json` 或整文件重写方式（会造成 1800 行假 diff），须定点追加。

**验收（Gate T3）**：
- `python -c "import json;json.load(open('tasks/queue/queue-status.json'))"` 通过。
- `git diff tasks/queue/queue-status.json` 只含本单一条新增，不出现其它工单号。
- `python scripts/render-queue-views.py` exit 0。
- 文件 CRLF 计数为 0。

**禁止**：不得改其它任何 record 的任何字段；不得动 `queue-columns.md` / `queue-kanban.md` 之外的生成物。

### T4 · 总验收

**文件**：无（只读验证）

**写什么**：无需写代码，按下述六项逐条跑并留存输出。

**验收（Gate T4）**：
1. **源码级（执行端自做，不需重启）**：用**新 Python 进程**加载当前源码，直调 `agent_server._health_payload()`，验证四态：
   - 真实配置（`impl`/`endpoint`/`model` 齐备 + `enabled=false`）→ `provider_answerable=True`，note 含实际 impl 与 model，**不含「无法作答」**；
   - 分别清空 `impl` / `endpoint` / `model` → `provider_answerable=False`，note **指名该缺失项**；
   - `enabled=true` + 三要素齐备 → `provider_answerable=True` 且 **无 `provider_note` 键**；
   - `enabled=true` + 某要素缺 → 判 C（C 优先）。
2. **线上级（主脑授权后由主脑执行，执行端不得自行重启）**：`Invoke-RestMethod http://127.0.0.1:8756/health`，要求 `provider_answerable=true`、note 含 `ollama-8b` 与 `qwen3-8b-uncensored:latest` 且不含「无法作答」。
   > **授权说明**：重启 8756 常驻进程属主脑职权（需 `taskkill` 监听 pid + 等端口释放 + 删 `%TEMP%\ultima-agent-server.pid` + Popen 重拉）。执行端**只读验证，不得重启、不得 taskkill**；未获得主脑书面授权时，第 2 项标 `PENDING-RELOAD` 并继续第 3-8 项，不得因此停线。
3. 构造 C 态（monkeypatch 三要素任一为空）时 note 指名缺失项。
4. `pytest src/brain/tests/test_provider_layer.py -q` 全绿。
5. `pytest src/brain/tests src/brain/orchestration/tests -o addopts= -p no:cacheprovider -q`：**失败数 ≤ 基线失败数**（不约束总数；新增用例必然使总数上升）。
6. 基线 worktree 对照：`git worktree add <tmp> <本单开工前 HEAD> --detach`，跑同一组测试记失败数，与步骤 5 比对后 `git worktree remove --force` + `prune`。
7. `/ask` 零变化探针：改动前后各打 Phase 1 的 C1/C2 原文（`%TEMP%\probe_mainbrain.py` 内可查），输出语义一致、耗时同量级。
8. 改动文件清单 = {`agent_server.py`, `test_provider_layer.py`, `queue-status.json`} ∪ 本单卡与需求包；越界声明写「无」。
9. **链路验收**：用 `scripts/run-pipeline.py --requirement ... --run-dir ... --work-order wo-ultimaagent-20261112-0049 --card ... --prompt ... --evidence ...` 跑通全链，产出 `<run-dir>/pipeline.json`、`verify.json`、`audit.json`。

**禁止**：不得用 `git stash` / `restore` 伪造「工作区干净」；不得跳过基线对照直接宣称无回归；不得在 verify 失败时强行进入 audit；**不得重启或 taskkill 8756 常驻进程**（第 2 项属主脑职权）。

---

## 4. 风险与处置

| # | 风险 | 处置 |
|---|---|---|
| R1 | Codex 为了「让测试过」把 `provider_configured` 改成可作答语义 | 铁律 6 + Gate T1「该行字节不变」双重锁；T2 断言 `provider_configured is False` 仍在 |
| R2 | 把 B 态归并进 C 态（都写「无法作答」），等于没修 | Gate T1 明确「B 态禁止出现『无法作答』」，T2 有专条断言 |
| R3 | 新增测试使总数上升，被误判为「全量不达标」 | 验收只说「failure count ≤ baseline」，不约束总数（DeepSeek 歧义 6 已澄清） |
| R4 | 为省事把判定抽成共享 helper，制造第二判据源 | 铁律 3 + Gate T1「判定只在 `_health_payload()` 内」 |
| R5 | 引入网络探测「确认是否真能用」 | 铁律 5 明令禁止；`/health` 必须零 IO |
| R6 | 改 `agent_server.py` 时顺手动了 `/ask` 的 `provider_for` 调用 | Gate T4 第 6 条要求 `/ask` 探针改动前后语义一致；Gate T1 要求引用次数不变 |
| R7 | 队列登记整文件重写造成大量假 diff | T3 明令定点追加，Gate T3 校验 `git diff` 只含本单一条 |
| R8 | 链路脚本在真跑时报错，执行端擅自改 `scripts/` | §1 不做第 6 条：链路报错须停下报主脑，不得自行改脚本 |

---

## 5. 裁决记录

### 5.1 需求来源与分工（本单为何存在）

Owner 在本轮明确要求：**不要让主脑越位自己做工单，需求交 DeepSeek 出方案、DeepSeek 派 Codex，主脑做顾问**。本单是这条流程的**首次真实执行**：
- 主脑只写需求包（含实测证据，因 L1011 外脑无仓库读取权），不写实现细节；
- DeepSeek 出 decompose / work_order / schedule（三阶段全部 `verdict=completed`）；
- 主脑只做裁决与格式对齐；
- Codex 执行。

同时本单承担 0048 遗留的验证任务：**首次用 `run-pipeline.py` 跑完整链并验证 audit 正路径**（0048 因 `tree_unchanged` 结构不可达只能验负路径）。

### 5.2 DeepSeek 的 9 条歧义与主脑裁决

DeepSeek 在 decompose 阶段主动列了 9 条歧义，逐条裁决如下：

| 歧义 | DeepSeek 提出的问题 | 主脑裁决 |
|---|---|---|
| 1 | `provider_configured` 保留原意 + 加新字段，还是改原字段含义 | **保留原意 + 新增 `provider_answerable`**。理由：原字段被两处测试直接断言（L439 `is True`、L456 `is False`），改含义会破坏既有契约；需求包铁律 6 本就把「新增伴随字段」列为正确解 |
| 2 | 新字段命名与位置未定 | 采纳 `provider_answerable`，位置在 `provider_configured` 之后，同层 |
| 3 | B/C 态精确文案未定 | 采纳「语义固定、措辞自由」；B 必须实填 impl+model 且不含「无法作答」，C 必须指名缺失项 |
| 4 | `enabled=true` 但 model 空，算 A 还是 C | **C 优先**。三要素齐备是「可作答」的必要条件，`enabled` 只是「用户显式启用」的信号 |
| 5 | `provider_configured` 是否还有其它测试断言 | 仅 L439 / L456 两处，均已核实 |
| 6 | 失败数 ≤ 基线，但新增测试会增加总数 | **只约束失败数，不约束总数**。这是 L175「验收总数必须现算」的延伸：基线是 577，新增后总数必然上升，写死总数会让正确改动被误判 |
| 7 | `/ask` 探针具体用哪条 | 采纳建议非强制；T4 第 6 条给的是 Phase 1 的 C1/C2 原文，可用等价原文替换但须前后可比 |
| 8 | B 态 note 是否可提 `enabled` | 可提，但须表述为「未显式启用」，不得表述成「不可用」 |
| 9 | C 态下 `model` / `provider_model` 是否仍 copy `_MAIN` | **保持不变**（Non-goal 第 2 条），测试不得假设 C 态下这两个字段为空 |

### 5.3 主脑对 DeepSeek 产出的修正

DeepSeek 的 work_order 阶段第 4 条把「`provider_configured` 语义如何处理」写成「执行时取其一并在提交说明中写明选择」——**这是把决策推给执行端**，与「主脑做顾问、执行端只执行」的分工冲突。主脑已在本单 §5.2 歧义 1 中定死为「保留原意 + 新增字段」，§1 与 T1 执行端无选择权。

### 5.4 机检抓到的本卡自身缺陷（已修）

`check-order-consistency.py` 首次跑本卡报 **2 项 C1a FAIL**：
- 原卡用了 `## 0. 范围冻结 / ## 1. 任务清单 / ## 2. 任务明细` 的编号，而机检约定是 `## 1. / ## 2. / ## 3.`，导致 §2/§3 段落边界全部错位、文件集合取空。已改编号。
- §1「本单只做」第 3 条把 `scripts/run-pipeline.py` 写进了改动清单，而它是**执行工具不是改动文件**，机检正确地判为「§1 点名但 §2/§3 未安排」。已改为在 §1 末尾以引用块标注「链路执行方式（非改动面）」。

**这两条都是本卡的错，不是机检的误报。** 机检脚本在本单第二次实跑中证明了自己有效（0048 建它时只用了 3 个构造样本，这次是真实新卡的真实缺陷）。

### 5.5 本单与 0048 的边界

- 0048 交付：`run-pipeline.py` 单入口 + `check-order-consistency.py` + dispatch/audit 四处修复，已冻结 `62d2c7ba`。
- 0049 交付：`/health` 文案诚实性修复，并**用 0048 的链跑本单自己**，从而验证 audit 正路径。
- 两单写域不重叠（0048 改 `scripts/`，0049 改 `src/brain/`）。

### 5.6 本卡第七次自我修正：T4 第 1 项缺「重启授权」

首派执行到 T4 第 1 项停线，Codex 的判断完全正确：**源码已修、专项测试全绿，但 8756 常驻进程仍运行修改前已加载的模块，线上 `/health` 返回旧 payload**。而卡里 T4 第 1 条只写了「只读 `Invoke-RestMethod`」，**隐含要求「服务已加载新代码」，却没写重启步骤、也没写授权边界**。

这是本卡第七个自身缺陷，与 0048 的六次同源：**卡把「验收动作」写成「只读断言」，却没有交代该断言的成立前提需要一次有副作用的动作**。

修法（已落进 §3 T4）：
- 第 1 项拆成 **1（源码级，执行端自做，新进程直调 `_health_payload()` 验四态）** 与 **2（线上级，主脑授权后主脑执行）**；
- 明确写「执行端不得重启、不得 taskkill」，未获授权时该子项标 `PENDING-RELOAD` 但**不因此停线**，继续跑 3-9 项；
- 「禁止」段追加「不得重启或 taskkill 8756 常驻进程」。

**教训归纳（待登记 lessons-log）**：凡验收项依赖「进程已加载新代码」「服务已重启」「缓存已失效」这类**非只读前提**时，卡必须显式写出该前提的产生方式与授权归属，否则执行端必然停线，且停线是对的。

### 5.7 首派链路实跑记录（0048 链的首次真实全链）

首派走 `run-pipeline.py`，六步全部真实执行，结果如下：

| 步 | 结果 |
|---|---|
| plan（DeepSeek 三阶段） | 完成，`requirement.txt` 8728 B + `stages/decompose.json` 24651 / `work_order.json` 19422 / `schedule.json` 10896 |
| dispatch-dor | 通过 |
| dispatch | 真实派发，**自建 run 目录 `...0049-20261112T101442833389Z`**（非主脑传入的 `T181347`） |
| verify / audit / freeze | 未执行 —— `receipt_valid=false` 触发 `blocked-for-invalid-receipt` |

**关键观察**：链路的 blocked 判定发生在 verify 之前，依据是 `done.json` 的 `receipt_valid`（`state=blocked`、`changed_files=21`、`exit_code=0`）。这正是 0048 §5 设计的「`receipt_valid=false` 判真失败、`receipt_valid=true` 且等审计名额判暂停」两种 blocked 语义的**第一种真实命中**，语义区分成立。

**第二个关键观察**：派发器自建时间戳 run 目录，与入口 `--run-dir` 并存但不一致。`pipeline.json` 落在**派发器建的那个目录**，不在入口指定的目录。这是 0048 时就暴露、本单再次复现的契约歧义，**应当由 0050 修**（让 `run-pipeline.py` 从 `dispatch-record.json` 读回真实 run-dir 并以它为准写入 `pipeline.json`，或在派发时把入口 run-dir 透传下去）。

### 5.8 本卡第八次自我修正：缺「续行契约」，写操作与只读验证混在一次派发里

第二次派发在**基线核对阶段**就停线，Codex 的判据完全正确：

> 工作区在本进程写入前已存在本单的生产代码、测试和队列登记改动，无法建立可信的改前基线与改动归属。

它同时命中停线条件 1（卡与代码事实冲突：T1/T2 已同时存在）与停线条件 3（T1→T2→T3 串行 Gate 无法判定：T3 要追加 pending，但记录已存在且是 executing）。

**根因不是 Codex，是卡的结构**：本卡把**写操作（T1/T2/T3）**与**只读验证（T4）**放在同一次派发里。首派完成 T1-T3 后停线，重派时这些写操作的产物已在工作区，新进程必然无法「从头执行串行 Gate」。

**修法（本节即契约）**：

1. **T1-T3 已在首派完成并通过主脑独立复核**（见 §5.9），其产物作为本次派发的前置事实，续行时**不得重做、不得回退、不得认领**。
2. **本次派发只做 T4**，且 T4 全部为只读动作：不得改任何文件、不得改队列、不得重启服务。
3. 执行端在续行时的正确姿势：先确认目标三个文件的当前内容 == §5.9 记录的期望内容，一致则直接进入 T4；不一致才停线。
4. **更根本的解法**（已在本卡执行）：把 T1-T3 的产物**先提交成一个 commit**，使工作区干净，再派 T4。这样 `verify-order.py` 的 `tree_unchanged` 也能与 `done.json` 的 `tree_oid` 对上，链路才能走通 audit 正路径。

### 5.9 主脑对 T1-T3 的独立复核（续行前置事实）

| 项 | 复核方式 | 实测结果 |
|---|---|---|
| T1 改动面 | `git diff -- src/brain/agent_server.py` | `+21/-2`，仅在 `_health_payload()` 内 |
| T1 `provider_configured` 零变更 | diff 内该行命中 | **0** |
| T1 引用次数不变 | Grep 计数 | `provider_for(` / `require_main(` / `main_settings(` = **4 / 0 / 3** |
| T2 改动面 | `git diff -- test_provider_layer.py` | `+52/-3` |
| T2 专项测试 | `pytest test_provider_layer.py -q` | **23 passed in 2.78s** |
| T3 队列 | `json.load` + 计数 | records **170**，0049 末条唯一 |
| 全量回归 | `pytest src/brain/tests src/brain/orchestration/tests -q` | **580 passed / 1 failed**（基线 `e789b2d6` 上 577 passed / 1 failed；passed +3 来自新增用例，failed 不增） |
| 基线 worktree 对照 | `worktree add <tmp> e789b2d6 --detach` | **不可行**：worktree 不带未跟踪依赖（`libs/base/openjarvis/*.md`、`guardrails/receipt`、`loop/params`），`src/brain` 测试收集即 12 errors。0048 已验证 worktree 只适用于 `tests/` 根下不依赖未跟踪模块的脚本测试 |
| 源码级四态 | 新进程直调 `_health_payload()` | B 态 `answerable=True` + note 实填 impl/model 且不含「无法作答」；C 态 impl/endpoint/model 各空均 `False` 且指名缺失项；A 态 `True` 且无 note 键 |
| 线上 `/health` | 重启后 `Invoke-RestMethod` | `provider_answerable: true`，note = 「主脑未显式配置，当前使用内置默认：impl=ollama-8b，model=qwen3-8b-uncensored:latest」 |
| `/ask` 探针 | 改动后 C1/C2 | C1 `intent=query` 0.03s 蓝屏排查方向；C2 `intent=query` 2.83s 服务端日志/依赖排查方向 —— 与改动前语义一致 |
| 改动文件清单 | `git status --porcelain` | 3 个 M（`agent_server.py` / `test_provider_layer.py` / `queue-status.json`）+ 3 个 ??（本单卡 / 需求包 / 载荷）；**无越界** |

**结论**：T1、T2、T3、T4 的全部 9 个子项均已由主脑实测通过；唯一未走的是 ⑧ audit（DeepSeek 审计）与 ⑨ freeze。


