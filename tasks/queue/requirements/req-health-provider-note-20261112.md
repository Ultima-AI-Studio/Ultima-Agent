# 需求包 · 0049 `/health` 的 provider_note 与实际行为不一致

> 需求编号：REQ-20261112-0049
> 提出方：主脑（顾问角色，出需求与证据，不出实现细节）
> 执行方：DeepSeek 出方案与工单 → Codex 执行
> 本包用途：外脑无仓库读取能力（L1011），故本包自带全部实物证据，DeepSeek 不得凭空推断未列出的文件内容。

---

## 1. 目标

`GET /health` 的 `provider_note` 文案必须以**「实际能不能作答」**为准，而不是以「用户有没有显式配置」为准。
当前状态是：**系统正常作答，但 `/health` 对外宣称「将无法作答」。**这是一个对外承诺与实际能力相反的诚实性缺陷，优先级等同于主脑 Phase 1 的「谎称已动手」。

---

## 2. 现状证据（全部为 2026-11-12 实测，非推演）

### 2.1 实测 `/health` 返回值（服务在跑，pid 29668）

```json
{
  "ok": true,
  "model": "qwen3-8b-uncensored:latest",
  "agent": "native_react",
  "tools": ["calculator", "think", "ultima_memory", "ultima_dispatch", "ultima_dispatch_status"],
  "provider": "ollama-8b",
  "provider_model": "qwen3-8b-uncensored:latest",
  "provider_configured": false,
  "provider_note": "主脑未配置，/ask 将无法作答"
}
```

同一条链上 `/ask` **实际能正常作答**（Phase 1/2/3/3.5 全部活体验收都是在这条链上跑的）。

### 2.2 判定代码原文（`src/brain/agent_server.py` L1407-1421）

```python
def _health_payload() -> dict[str, Any]:
    ...
    model = str(_MAIN.get("model") or "")
    configured = bool(_MAIN.get("enabled") and str(_MAIN.get("endpoint") or "").strip())
    payload: dict[str, Any] = {
        "ok": True,
        "model": model,
        "agent": AGENT,
        "tools": ANSWER_TOOLS,
        "provider": str(_MAIN.get("impl") or ""),
        "provider_model": model,
        "provider_configured": configured,
    }
    if not configured:
        payload["provider_note"] = "主脑未配置，/ask 将无法作答"
    return payload
```

### 2.3 `main_settings()` 实测返回值（`src/brain/slot_adapter.py` L161-170）

```json
{
  "slot": "S-MAIN",
  "impl": "ollama-8b",
  "endpoint": "http://127.0.0.1:11434",
  "model": "qwen3-8b-uncensored:latest",
  "enabled": false
}
```

**关键事实：`endpoint` 与 `model` 都是完整可用的值，只有 `enabled` 是 `false`。**

因此 `configured = enabled and endpoint` = `false and true` = **`false`** —— 文案被 `enabled=false` 单独触发，而 `enabled` 恰恰不是 `/ask` 的判据。

### 2.4 `/ask` 真实调用路径（`src/brain/agent_server.py` 全文 Grep 结果）

- `require_main` 在 `agent_server.py` 中 **引用次数为 0**。
- `/ask` 侧四处分派（L718 / L1006 / L1159 / L1216）全部走 `provider_for(_MAIN).chat(...)`。
- `provider_for()` 只用 `impl` / `endpoint` / `model`，**从不检查 `enabled`**。

**结论：`/health` 的 `configured` 判据与 `/ask` 的真实判据是两套口径，且前者更严。**
`enabled=false` 的真实含义是「用户没有在配置里显式写 enabled=true」，不是「主脑不可用」——`main_settings()` 已经带出了完整的默认 endpoint 与 model。

### 2.5 现有测试锁住了错误文案（`src/brain/tests/test_provider_layer.py` L444-457）

```python
def test_agent_server_health_payload_marks_unconfigured_provider(monkeypatch):
    ...
    settings.update({"endpoint": "", "enabled": False})
    monkeypatch.setattr(agent_server, "_MAIN", settings, raising=False)
    payload = agent_server._health_payload()
    assert payload["ok"] is True
    assert payload["provider_configured"] is False
    assert payload["provider_note"] == "主脑未配置，/ask 将无法作答"
```

注意这个测试的构造方式：它把 `endpoint` **人为清空**（`{"endpoint": "", "enabled": False}`）才断言「无法作答」。
也就是说：**真正不可作答的情形是 `endpoint` 为空**，而不是 `enabled=false`。
线上真实情形是 `endpoint` 有值、`enabled=false`，与测试构造的情形**根本不是同一类**，但走的是同一句文案。
另一个测试 L431-441 在 `enabled=True` 且 endpoint 有值时断言 `"provider_note" not in payload` —— 也是对的。

**即：现有两个测试各自都对，缺的是「endpoint 有值但 enabled=false」这一类的覆盖。**

### 2.6 相关既有约定

- 0043 北极星条目已登记该待办：「provider_configured=false 时提示『主脑未配置，/ask 将无法作答』，但零配置走内置默认仍能正常作答，文案会误导用户。该文案属『未配置须显式回应』的落点，需在 Phase 4 安装向导确定『未配置』语义后一并校准。」
- 0043 遗留项同样记录了同一处。

---

## 3. 铁律（不可违反）

1. **不得改变 `/ask` 的任何行为**。本单只修 `/health` 的文案与判据，`provider_for()` 与四处分派一个字节不动。
2. **不得删除既有测试的断言强度**。L444-457 那条「endpoint 为空 → 无法作答」必须继续成立；允许按其真实语义重命名/重写断言文本，但不许为了让新逻辑过而把它改成宽松断言。
3. **不得引入第二个「是否可用」的判据源**。判定必须在 `_health_payload()` 内单点计算，不许在别处另建一个函数再被两处调用（避免 L159 同族的双源漂移）。
4. **文案必须能区分三种状态，且每种状态都要能被测试断言**：
   - A. 显式配置可用（`enabled=true` 且 endpoint 有值）
   - B. 未显式配置但走默认可用（`enabled=false`，但 `impl`/`endpoint`/`model` 齐备）
   - C. 真不可用（`impl` 或 `endpoint` 或 `model` 任一为空）
5. **不得用「大概能连上」代替判定**。判定只基于配置字段是否齐备，**不发起网络探测**（`/health` 必须是纯本地零延迟，0043 已定的口径：关闭端口探测 463.8ms < 500ms）。
6. **`provider_configured` 字段本身要保留**（外部可能有消费者），但它的语义必须写清；如果保留原来含义会造成误读，改为返回两个字段而不是篡改原字段含义。

---

## 4. 要什么

1. `_health_payload()` 的判定改为基于「可作答性三要素」：`impl` 非空、`endpoint` 非空、`model` 非空。三者齐备即「可作答」，与 `enabled` 解耦。
2. `provider_note` 的三种文案（措辞可自定，但语义必须如下）：
   - A：不带 note（保持现状，不写多余字段）。
   - B：必须明确「未显式配置，当前使用内置默认」并给出实际的 impl / model，**禁止出现「无法作答」字样**。
   - C：保留「无法作答」语义，且必须指出缺的是哪一项（impl / endpoint / model）。
3. 新增或改造测试，让 A / B / C 三态各有一条断言；**特别要新增「endpoint 有值但 enabled=false」这一条**，这条是线上真实情形，现在完全没有覆盖。
4. 同步更新 L444-457 那条测试的构造与断言，使其语义正确（它测的是 C 态，不是「未配置」态），但断言强度不得降低。

---

## 5. 不做什么（Non-goals）

1. 不改 `/ask` 的判据、不改 `provider_for()`、不改 `require_main()`。
2. 不改 `main_settings()` / `slot_adapter.py`（`enabled` 的语义属配置层，本单不动）。
3. 不做网络探测、不引入任何 IO。
4. 不动 Phase 4 安装向导的「未配置」语义定义（那是另一张单）。
5. 不改 `/health` 的其它字段（`ok` / `model` / `agent` / `tools` / `provider` / `provider_model`）。
6. 不为此新增配置文件或配置项。

---

## 6. 验收（必须可命令验证）

1. `GET /health` 在**当前线上配置**（`enabled=false`、`endpoint=http://127.0.0.1:11434`、`model=qwen3-8b-uncensored:latest`）下，**不得出现「无法作答」字样**，且 note 必须含实际 impl 与 model。
2. 构造 C 态（impl / endpoint / model 任一为空）时，note 必须指出缺失项，且不含任何「可用」的暗示。
3. `src/brain/tests/test_provider_layer.py` 三种状态各至少一条断言，全绿。
4. `src/brain/tests` + `src/brain/orchestration/tests` 全量 **不低于 577 passed / 1 failed**（唯一失败仍是 ollama 不在 PATH 的环境噪声），且**不得新增失败**。
5. 基线对照：`git worktree add` 到本单开工前的 HEAD，跑同一组测试，本单改动后失败数必须 **≤ 基线失败数**。
6. `/ask` 行为零变化：改动前后各打一条固定探针（建议用 Phase 1 的 C1/C2 原文），输出与耗时区间一致。
7. 改动文件清单必须与「写什么」一一对应；越界声明明确写「无」。
