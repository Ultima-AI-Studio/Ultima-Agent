# Codex 工单 · 插件总线直连检测修复（真实包名比对）

> 版本：v1.0 ｜ 状态：可开工 ｜ 适用工具：Codex
> 用法：按 T1→T3 顺序逐条执行，Gate PASS 后冻结再进下一条。
> 范围依据：`docs/specs/plugin-bus-spec.md` §5（插件间禁止直连）+ 缺陷登记四源：`execution/server/tests/test_ultima_bus.py` L205-221 KNOWN GAP 注释、`docs/references/lessons-log.md` L219、北极星清单 2026-11-12 记录、commit `a4a69e30`
> 前置：模块化处置②已完成（总线已入 HEAD，测试基线 **8 passed / 1 xfailed**，唯一 xfail 即本单要消的缺陷）。
> 依据 G-PLAN-001 说明：本单为**缺陷修复**，修复方案（比对键改为 manifest.entry 顶层包名）已随缺陷登记四源定稿落盘，工单内 §0 完整复述，不另建 plan 文档。

---

## 0. 现状校准（执行时以本节为准）

| # | 事实 | 出处 |
|---|---|---|
| 1 | 缺陷位置：`execution/server/ultima_bus/kernel.py` `_audit_imports()`（L607-652），比对键用**模块 ID**（如 `ultima.intent.test`），见 L641-645 的 `registered_ids` 循环 | kernel.py 实读 |
| 2 | 插件真实 Python 包名是 `plugin_<模块ID点换下划线>_<版本点换下划线>`（如 `plugin_ultima_intent_test_0_1_0`），来自 `manifest.entry` 的顶层段 | test_accept_4 注释 / manifest.py |
| 3 | 三组对照实验（2026-11-12）：`import plugin_ultima_intent_test_0_1_0`（真实包名）→ **未被拦（漏检）**；`import ultima.intent.test`（模块 ID 形态）→ 被拦；`import os` → 未被拦（合理） | probe_direct_import4.py，结论同载 test_accept_4 docstring |
| 4 | 审计事件名分布：`direct_call()` 路径发 `plugin.direct-connect.denied`（L455），`_audit_imports` 路径发 `plugin.direct-import.denied`（L648）。test_accept_4 末段断言的 `direct-connect` 事件由**第一段 direct_call** 产生，与本单修复**不冲突**，两处都不改名 | kernel.py 实读 |
| 5 | `test_accept_4` 现挂 `@unittest.expectedFailure`（L205）；修好后自动转 **unexpected success**，此时移除装饰器即为验收信号 | test 文件实读 |
| 6 | spec §5 只定义"插件间禁止直连=审计项"，未规定比对键实现；本单是让实现追上 spec，**不改 spec** | plugin-bus-spec.md L66-67/L303 |

**边界澄清（防越界修错方向）**：本缺陷与 L9 驻留裁决（pd-20261112 记录）**无关**——不动 `RESIDENT_DOMAINS`，不动 `registry.py`。

---

## 1. 范围冻结

### 本工单只做

1. 改 `execution/server/ultima_bus/kernel.py` 的 `_audit_imports()`：比对键从「模块 ID 单一形态」扩为「模块 ID + 真实包名双形态」
2. 改 `execution/server/tests/test_ultima_bus.py`：移除 `test_accept_4` 的 `@unittest.expectedFailure` 装饰器并更新其 docstring（去掉 KNOWN GAP 段）
3. 重跑三组对照实验复核

### 本工单不做（硬边界）

- 不改 `RESIDENT_DOMAINS`（L9 裁决是独立 ADR，等 Owner 拍板）
- 不改 `manifest.py`、`load()`、`unload()`、`boot_check()`（处置②已修好的部分，只回归不动）
- 不改 `docs/specs/plugin-bus-spec.md`
- 不改 `src/brain/memory/registry.py`
- 不新增审计事件类型、不动 `plugin.direct-connect.denied` / `plugin.dynamic-code.denied` 事件名
- 不动 `_audit_imports` 里动态导入（eval/exec/__import__/import_module）拦截段

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T1 | `execution/server/ultima_bus/kernel.py` | 真实包名形态 import 被拦；模块 ID 形态仍被拦；`import os` 与自引用仍放行 |
| T2 | `execution/server/tests/test_ultima_bus.py` | 装饰器移除后全套 pytest 无 xfail 无 unexpected success |
| T3 | 对照实验复核 + 总验收 | 三组实验结论反转正确；`git status` 只含两文件 |

---

## 3. 任务明细

### T1 · _audit_imports 建立包名→模块 ID 映射

**文件**：`execution/server/ultima_bus/kernel.py`

**写什么**：
1. 在 `_audit_imports()` 开头（`registered_ids` 构建处）同步构建映射 `package_map: dict[str, str]`：遍历 `self.registry.records` 每个模块**所有已装版本**的 `manifest["entry"]`，取顶层包名 `entry.split(".")[0]` 作键，值为其 `module_id`。
2. 比对循环改为双键判定，对每个 imported 名 `target`：
   - 取顶层段 `top = target.split(".")[0]`，查 `package_map`；命中且映射值 ≠ 自身 → 记入 `forbidden`（命中子模块形态如 `plugin_x_y_z.main` 时同样要拦：顶层段命中即可）
   - 保留现有模块 ID 形态比对（L641-645 逻辑不删，向后兼容两种写法都拦）
3. 自引用放行规则同步扩展：自身模块 ID 前缀之外，**自身各版本的顶层包名**也放行（当前正在注册的 `manifest.entry.split(".")[0]`）。
4. `plugin.direct-import.denied` 审计事件的 payload 增加一个 `"package": <命中的顶层包名>` 字段（事件名与既有字段不变）。

**验收（Gate T1）**：
- `tools\venv-openjarvis\Scripts\python.exe -X utf8 -m pytest execution/server/tests/test_ultima_bus.py -q` 中 test_accept_4 显示 **unexpected success**（此时尚未移除装饰器，属预期中间态）
- 负样本：`import plugin_ultima_intent_test_0_1_0` 形态在 load 时抛 `PermissionDenied`
- 正样本：`import os` 放行；插件自引用（自身包名/自身模块 ID）放行；`import ultima.intent.test` 模块 ID 形态仍被拦
- 动态导入拦截回归不受影响（test_accept_4 第二段 dynamic eval 仍拒）
- `python -c "import ast;ast.parse(open('execution/server/ultima_bus/kernel.py',encoding='utf-8').read())"` 退出码 0
- `RESIDENT_DOMAINS` 所在行（L53 附近）`git diff` 无变化

**禁止**：不得为省事只做包名比对删掉模块 ID 比对（两种写法都要拦）；不得把 `import os` 等标准库也纳入拦截；不得改 `_audit_imports` 之外的任何方法。

---

### T2 · 测试转绿

**文件**：`execution/server/tests/test_ultima_bus.py`

**写什么**：
1. 移除 `test_accept_4_direct_connection_and_undeclared_scope_are_audited` 的 `@unittest.expectedFailure`（L205）。
2. docstring 更新：删除 KNOWN GAP 整段，改为一行：「直连检测双键比对（模块 ID + manifest.entry 顶层包名），2026-11-13 由 wo-ultimaagent-20261113-0053 修复，三组对照实验证据见 git 历史 a4a69e30 提交说明」。
3. 测试体**不改**（三段断言原样保留，转绿的只能是实现，不是断言）。

**验收（Gate T2）**：
- `tools\venv-openjarvis\Scripts\python.exe -X utf8 -m pytest execution/server/tests/test_ultima_bus.py -q` 退出码 0，输出 **9 passed / 0 xfailed / 0 unexpected success**
- `Select-String -Pattern "expectedFailure"` 在本文件命中 0
- 测试文件 `git diff` 仅涉及装饰器行与 docstring 段

**禁止**：不得为转绿弱化或改写任何 assert 断言；不得删除测试段落。

---

### T3 · 对照实验复核 + 总验收

**写什么**：
1. 重跑三组对照实验（可重写等价脚本，放 `data/` 下临时目录，遵守路径域校验），记录结论。
2. 确认工作区干净。

**验收（Gate T3 / 总验收）**：
1. 三组实验结论：真实包名 → **被拦**（与 2026-11-12 相反）；模块 ID 形态 → 仍被拦；`import os` → 仍放行
2. `git status --short` 仅 `execution/server/ultima_bus/kernel.py` 与 `execution/server/tests/test_ultima_bus.py` 两文件
3. 反向断言：`git diff` 中 `RESIDENT_DOMAINS` / `plugin-bus-spec.md` / `src/brain/memory/registry.py` 零改动
4. 回执自述：越界声明（无/列明）、每 T 证据（命令输出粘贴）、改动文件清单

---

## 4. 开源替代排查（DoR 第 6 项，G-OSS-001）

不适用：本单为既有自研代码的缺陷修复（比对键修正），无新模块、无新依赖引入，不存在"自研 vs 开源"选择。

---

## 5. 给编码代理的任务粘贴模板

```
T1 _audit_imports 包名映射：已完成，Gate 全绿（附 unexpected success 输出 + AST 过）
T2 测试转绿：已完成，Gate 全绿（附 9 passed / 0 xfailed 输出）
T3 对照实验复核：已完成，三组结论反转正确（附实验输出 + git status）
总验收：pytest 9 passed / 0 xfailed；git status 仅 2 文件；反向断言 3/3
```
