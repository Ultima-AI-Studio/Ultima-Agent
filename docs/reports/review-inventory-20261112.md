# 复审报告：模块化梳理结论独立核查

- 复审人：Codex
- 时间：2026-11-12 22:32:51 +08:00
- 核查方式：先全文读取两份待审文档；随后以指定解释器 `tools\venv-openjarvis\Scripts\python.exe -B -X utf8` 做 AST 静态解析，以 `rg` 做文本与路径复核，以 Git 只读命令核对历史和工作区边界。AST 对 `src/**/*.py` 共解析 277 个文件、0 个语法错误；`unload()` 扩展到明确的第一方目录后解析 406 个 Python 文件、0 个错误。全程未导入产品模块、未运行产品入口、未执行测试。

核查快照：分支 `codex/voice-fsmn-new-path`，`HEAD=9737961744ce5c35dc71519d546e1cb9f7b85c45`。本报告核查的是当前工作区，不是仅核查 `HEAD`；这一点对未跟踪的 `execution/server/ultima_bus/` 很重要。

## 一、总览

| 组 | 结论数 | 成立 | 不成立 | 证据不足 |
|---|---:|---:|---:|---:|
| A 注册表 | 2 | 1 | 1 | 0 |
| B 命名拼接 | 4 | 0 | 3 | 1 |
| C 方案数据 | 6 | 4 | 2 | 0 |

## 二、逐条判定

### A1 四个自建注册表都有生产调用方

- 判定：成立
- 我验证的方式：

  ```powershell
  @'
  import ast, pathlib
  names={"GuardrailsRegistry","MemoryRegistry","OrchestrationRegistry","SkillRegistry"}
  files=["src/brain/guardrails/scanner.py","src/brain/memory/backend.py",
         "src/brain/orchestration/engine.py","src/brain/bootstrap.py",
         "src/brain/skills/dispatch.py","src/brain/skills/whitelist.py"]
  for f in files:
      t=ast.parse(pathlib.Path(f).read_text(encoding="utf-8-sig"), filename=f)
      for n in ast.walk(t):
          if isinstance(n,ast.ImportFrom):
              for a in n.names:
                  if (a.asname or a.name) in names:
                      print("IMPORT",f,n.lineno,n.level,n.module,a.name)
          if (isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
              and isinstance(n.func.value,ast.Name) and n.func.value.id in names):
              print("CALL",f,n.lineno,n.func.value.id,n.func.attr)
  '@ | tools\venv-openjarvis\Scripts\python.exe -B -X utf8 -

  rg -n "GuardrailsRegistry|MemoryRegistry|OrchestrationRegistry|SkillRegistry" `
    src/brain/guardrails/scanner.py src/brain/memory/backend.py `
    src/brain/orchestration/engine.py src/brain/bootstrap.py `
    src/brain/skills/dispatch.py src/brain/skills/whitelist.py
  ```

- 证据：AST 将包内相对导入解析到对应自建模块，且调用是语法树中的真实 `Call`，不是注释或字符串：

  | 类 | 导入 | 生产调用 |
  |---|---|---|
  | `GuardrailsRegistry` | `scanner.py:22 from .registry ...` | `NeMoScanner.__init__` 内 `:113 is_registered`、`:114 register` |
  | `MemoryRegistry` | `backend.py:24 from .registry ...` | `Mem0Backend.__init__` 内 `:88 is_registered`、`:89 register`；`snapshot():273 is_resident` |
  | `OrchestrationRegistry` | `engine.py:32 from .registry ...` | 构造器内 `:127 is_registered`、`:128 register`；`snapshot():321 is_resident` |
  | `SkillRegistry` | `dispatch.py:15`、`whitelist.py:17` 的 `.registry`；`bootstrap.py:247` 绝对导入 | `bootstrap.py:249 install_task_domain`、`:251 exists`；`dispatch.py:44/60/69`；`whitelist.py:74/93/150` |

  这些调用位于正常构造器、普通方法或生产函数中，未处于 `if False`、`TYPE_CHECKING` 或同一路径无条件 `return/raise` 之后。静态证据只能证明生产源码存在可达路径，不能证明某个现场进程已经触发了每一条路径。
- 与我看到的主脑结论差异：有。`inventory` 的更正结论正确；`plan v2` 仍称 guardrails/memory/orchestration 三个注册表“空转”，与当前源码直接冲突。另有行号小误差：`bootstrap.py:247` 是导入，实际调用在 `:249`。

### A2 生产代码零 `unload()`；8 处全部在测试

- 判定：不成立
- 我验证的方式：

  ```powershell
  rg -n --glob '*.py' --glob '!tools/**' --glob '!docs/research/sources/**' `
    "\.unload\s*\(" src execution tests tasks scripts

  @'
  # 本轮实际脚本对第一方 Python 文件 ast.walk；筛选 Call(Attribute(..., attr="unload"))
  # 同时输出文件、lineno、接收者表达式，并按 tests/test_*.py 分类。
  '@ | tools\venv-openjarvis\Scripts\python.exe -B -X utf8 -
  ```

- 证据：第一方明确范围共找到 14 个真实 `unload()` 调用：生产 1、测试 13。生产反例是 `execution/server/ultima_bus/cli.py:55` 的 `kernel.unload(args.module_id)`。原文列出的四个自建 Registry 调用确实恰好 8 个，且全部在测试：

  ```text
  guardrails/tests/test_guardrails_m2.py 147,154,159
  memory/tests/test_memory_m3.py 103
  orchestration/tests/test_orchestration_m4.py 151
  skills/tests/test_skills_p2.py 61,72
  brain/tests/test_integration_m5.py 131
  ```

  其余 6 个为：生产 CLI 1 个；`execution/server/tests/test_ultima_bus.py:139`、`test_guardrails_s3.py:318/321`、`test_credential_s3.py:196`、`test_audit_s3.py:230` 共 5 个测试调用。因此，“四个自建 Registry 的 `unload` 共 8 处且全在测试”成立，但题目中的全仓表述不成立。8 处里实际是 5 个驻留拒绝断言、2 个正常卸载、1 个缺失键返回 `False`，也不能笼统写成“8 处都验证拒绝卸载”。
- 与我看到的主脑结论差异：有。`inventory` 把局部统计写成了全局结论，漏掉了当前工作区中的插件总线 CLI 与 S3 总线测试。

### B1 自建注册表与底座注册表只有两处重名

- 判定：不成立
- 我验证的方式：

  ```powershell
  @'
  import ast, pathlib
  base = pathlib.Path("tools/venv-openjarvis/Lib/site-packages/openjarvis/core/registry.py")
  base_names = {n.name for n in ast.parse(base.read_text(encoding="utf-8-sig")).body
                if isinstance(n, ast.ClassDef)}
  for p in pathlib.Path("src").rglob("*.py"):
      for n in ast.walk(ast.parse(p.read_text(encoding="utf-8-sig"))):
          if isinstance(n, ast.ClassDef) and n.name.endswith("Registry") and n.name in base_names:
              print(p, n.lineno, n.name)
  '@ | tools\venv-openjarvis\Scripts\python.exe -B -X utf8 -
  ```

- 证据：交集为 3 个，不是 2 个：

  ```text
  src/brain/channel/channel_breadth.py:55 ChannelRegistry
  src/brain/memory/registry.py:18       MemoryRegistry
  src/brain/skills/registry.py:39       SkillRegistry
  ```

  底座文件有 17 个 `ClassDef`：`RegistryBase` 1 个 + 具体注册表 16 个。故“底座有 16 个具体 Registry”在排除基类时成立；`plan v2` 把 `RegistryBase` 也列进名单后实际列了 17 个名字。
- 与我看到的主脑结论差异：有。梳理漏掉了 `ChannelRegistry`；它并非测试桩，`ChannelDispatcher` 会实例化它。

### B2 `ultima-plugin-bus` 在 `src/` 下零实现，只有规格文档

- 判定：不成立
- 我验证的方式：

  ```powershell
  rg -n -i -uuu --glob '!*.pyc' 'plugin_bus|PluginBus|插件总线' src
  rg -n 'class BusKernel|def (load|unload|switch|rollback)|kernel\.unload|add_parser' `
    execution/server/ultima_bus
  rg -n 'ultima-plugin-bus' docs/specs/registry.md
  & 'C:\Program Files\Git\cmd\git.exe' status --short -- execution/server/ultima_bus ultima_bus
  & 'C:\Program Files\Git\cmd\git.exe' ls-tree -r --name-only HEAD -- execution/server/ultima_bus ultima_bus
  ```

- 证据：三个指定字面模式在 `src/` 内容和路径中确实零命中；但这个搜索没有覆盖实际实现名 `ultima_bus`。当前工作区存在 `execution/server/ultima_bus/` 的 10 个文件和根包门面 `ultima_bus/` 的 2 个文件：`kernel.py:61 class BusKernel`，`:200 load`、`:242 unload`、`:258 switch`、`:317 rollback`；`cli.py:14` 构造参数解析器，`:23` 注册 `unload`，`:55` 调用 `kernel.unload`。`docs/specs/registry.md:55` 也登记为“s3-bus-kernel 已实现，待独立评审”。

  边界：这 12 个文件当前均为未跟踪文件，`git ls-tree HEAD` 无输出；所以它们存在于用户要求核查的当前工作区，但尚不属于当前 `HEAD`。本轮没有运行总线，也没有确认其验收状态。
- 与我看到的主脑结论差异：有。窄字面搜索结果成立，但“只有规格文档／无 CLI”的推论错误；实现落点本来就由规格指定在 `execution/server/ultima_bus/`，不在 `src/`。

### B3 六个外部拼接来源的引用次数

- 判定：证据不足
- 我验证的方式：

  ```powershell
  @'
  from pathlib import Path
  terms = ["openjarvis","mem0","LangGraph","NeMo","A2UI","Pipecat"]
  texts = [p.read_text(encoding="utf-8-sig") for p in Path("src").rglob("*.py")]
  print("case", {x:sum(s.count(x) for s in texts) for x in terms})
  print("ci", {x:sum(s.lower().count(x.lower()) for s in texts) for x in terms})
  # 本轮另用 AST 统计 Import/ImportFrom 的准确模块根命中。
  '@ | tools\venv-openjarvis\Scripts\python.exe -B -X utf8 -
  ```

- 证据：文档未定义大小写、子串/完整词、行数/出现次数、是否只算 `.py`、是否含测试/注释/字符串。当前 277 个 `.py` 的统一口径结果如下：

  | 口径 | openjarvis | mem0 | LangGraph | NeMo | A2UI | Pipecat |
  |---|---:|---:|---:|---:|---:|---:|
  | 文档声称 | 139 | 103 | 80 | 46 | 22 | 11 |
  | 原样大小写子串次数 | 125 | 63 | 45 | 46 | 22 | 8 |
  | 忽略大小写子串次数 | 142 | 103 | 80 | 67 | 135 | 11 |
  | AST 外部导入语句数 | 69 | 6 | 3 | 3 | 0 | 0 |

  `103/80/11` 可由忽略大小写的 Python 文本子串口径复现，`46/22` 又恰好由保留大小写口径复现，`139` 在上述统一口径均不能复现。临时自校脚本 `C:\Users\Administrator\AppData\Local\Temp\selfcheck_inventory.py` 也没有计算这六项。缺少原始统一算法和快照，无法确认这组历史数字；这些文本提及数也不等于运行依赖数。
- 与我看到的主脑结论差异：有。不能把未定义口径的“名字出现次数”称为精确“引用次数”，更不能由此直接量化拼接或耦合。

### B4 L1/L3/L5/L7 各只对应一个散文件，因此没有目录不是漏归位

- 判定：不成立
- 我验证的方式：

  ```powershell
  rg -n -C 2 '^\| L(1|3|5|7) \|' docs/specs/registry.md
  rg -n 'l7-interaction-loop|l7-orb-bridge|l7-voice-entry' docs/specs/registry.md
  (Get-Content src/brain/intent.py).Count
  (Get-Content src/brain/queue_source.py).Count
  (Get-Content src/brain/environment.py).Count
  (Get-Content src/brain/reporter.py).Count
  (Get-Content src/brain/interaction.py).Count
  ```

- 证据：权威表写的是：L1=`intent.py`；L3=`queue_source.py + environment.py`；L5=`reporter.py`；L7=`interaction.py + cli.py --loop`。因此 L3 和 L7 在权威表中已经不是单文件。`registry.md:50/51/54` 还登记了 L7 的 `interaction_orb.py`、`voice_loop.py` 及宿主侧落点；当前还有 `environment_upgrade.py` 作为环境能力扩展。核心文件行数 155/182/358/111/929 可复现，但不能把核心落点数等同于整层实现文件数。

  `registry.md` 只登记“实际落点”，没有记录“之所以没有目录是因为单文件”这一因果解释。“一个文件放不进目录”在工程上也不成立；是否建包应由公开边界、依赖方向、扩展计划和迁移成本决定，而不是由文件数机械决定。
- 与我看到的主脑结论差异：有。`inventory:187` 自己写“每层一个”后，下一行又列出 L3 两个文件；“两套坐标无映射”也与它引用的权威落点表矛盾。

### C1 只有 4 组共 130 行可搬，约占 `agent_server.py` 7.7%

- 判定：不成立
- 我验证的方式：

  ```powershell
  @'
  import ast, pathlib
  p=pathlib.Path("src/brain/agent_server.py")
  s=p.read_text(encoding="utf-8-sig"); t=ast.parse(s)
  nodes={}
  for n in t.body:
      if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): nodes[n.name]=n
      elif isinstance(n,(ast.Assign,ast.AnnAssign)):
          ts=n.targets if isinstance(n,ast.Assign) else [n.target]
          for x in ts:
              if isinstance(x,ast.Name): nodes[x.id]=n
  groups={
    "risk":["_RISK_PATTERNS","_RISK_REFUSAL","_risk_gate"],
    "no_tool":["_NO_TOOL_PATTERNS","_NO_TOOL_REPLY","_no_tool_gate"],
    "content":["_CLARIFY_TEMPLATES","_GROUNDED_TAG","_FUTURE_PROMISE_PATTERN",
               "_PUSHBACK_PATTERN","_PUSHBACK_REPLY","_SERVILE_TAIL_PATTERN","_clean_content"],
    "catalog":["TOOLS","ANSWER_TOOLS"],
    "prompts":["_QUERY_SYSTEM","STRUCTURED_REPLY_TIMEOUT_SECONDS",
               "STRUCTURED_FALLBACK_REPLY","STRUCTURED_REPLY_SYSTEM_PROMPT"]}
  total=0
  for g,xs in groups.items():
      n=sum(nodes[x].end_lineno-nodes[x].lineno+1 for x in xs)
      total+=n; print(g,n)
  print("physical",len(s.splitlines()),"total",total,"pct",100*total/len(s.splitlines()))
  '@ | tools\venv-openjarvis\Scripts\python.exe -B -X utf8 -
  ```

- 证据：物理行数为 1692。按方案所选节点的 AST 跨度可精确复现：risk 17、no_tool 12、content 66、catalog 20、prompts 15，总计 130；`130/1692=7.6832%`，一位小数为 7.7%。但原文说“4 组”，实际列了 5 个目标模块/组。并且“只有这些可搬”不是由行数分析证明的；迁移还会新增 import/re-export，不能承诺文件净减恰好 130 行。`content=66` 也依赖特定的分组选择，其中包含 5 行 `_CLARIFY_TEMPLATES`。
- 与我看到的主脑结论差异：有。130 和 7.7% 的算术子结论成立，但“4 组”错误，“只有”是证据未支持的排他判断，所以整条不通过。

### C2 `_health_payload`/`get_jarvis` 不能搬；测试有 7 处模块级 `setattr`

- 判定：不成立
- 我验证的方式：

  ```powershell
  @'
  import ast, pathlib, collections
  hits=[]
  for p in pathlib.Path("src").rglob("*.py"):
      t=ast.parse(p.read_text(encoding="utf-8-sig"))
      for n in ast.walk(t):
          if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr=="setattr" and isinstance(n.func.value, ast.Name)
              and n.func.value.id=="monkeypatch" and len(n.args)>=2
              and isinstance(n.args[0], ast.Name) and n.args[0].id=="agent_server"):
              hits.append((p, n.lineno, ast.literal_eval(n.args[1])))
  print(len(hits), collections.Counter(x[2] for x in hits))
  '@ | tools\venv-openjarvis\Scripts\python.exe -B -X utf8 -
  ```

- 证据：实际是 16 个 `monkeypatch.setattr(agent_server, ...)` 调用、8 种符号，不是 7 处：

  ```text
  EVENT_BUS 3；_MAIN 7；SSE_PING_SECONDS 1；ask_once 1；
  _jars 1；_ensure_tools_registered 1；Jarvis 1；get_jarvis 1
  ```

  位置为 `test_agent_server_sse.py:20/115/131`、`test_prompt_boundary_p0.py:120`、`test_provider_layer.py:211/253/273/274/275/276/430/452/476/499`、`test_mainbrain_rules_prompt.py:36/37`。方案漏了 `ask_once`，且 `_MAIN` 是 7 次而非 9 次。

  `_health_payload` 函数本身 34 行（1407–1440），`get_jarvis` 本身 22 行（401–422）；所谓 56/48 是把若干模块级依赖选择性相加的“节点组”，不是 Python 词法闭包，也不是完整独立导入闭包。

  关键推论只在“直接把函数定义搬到新模块，再从 `agent_server` re-export 同一个函数对象”这一实现下成立：函数的 `__globals__` 仍指向定义模块，patch `agent_server._MAIN` 不会改变新模块的 `_MAIN`。本轮用两个 `ModuleType` 的最小实验得到 `reexport_reads=1`、`globals_is_new_module=True`，而旧模块的 `X` 已 patch 为 99。这个风险真实存在；但可用薄包装、显式参数注入或共享状态对象保留 patch 契约，所以不能推出“永远不能搬”。
- 与我看到的主脑结论差异：有。风险方向正确，处数、符号集和“绝对不可搬”结论均错误。

### C3 `agent_server.py` 近 30 天改了 28 次

- 判定：成立
- 我验证的方式：

  ```powershell
  $git='C:\Program Files\Git\cmd\git.exe'
  $rows=& $git log --since='2026-10-13T22:20:56+08:00' `
    --until='2026-11-12T22:20:56+08:00' --date=iso-strict `
    --format='%H|%ad|%s' -- src/brain/agent_server.py
  $rows.Count
  ```

- 证据：输出 `28`。最新一条为 `1bd9a2b1`（2026-11-12 18:38:24+08），窗口内最早一条为 `397d0c6d`（2026-10-28 18:18:51+08）。这是 `HEAD` 可达、按提交计数、路径受影响的 Git 历史；不是 28 个独立职责变更，也不含未提交改动。
- 与我看到的主脑结论差异：无。数字可复现；但它只能说明文件变更频繁，不能单独证明某种拆分方案正确。

### C4 `TOOLS` 11 个，其中 9 个自建装饰器注册 + 2 个底座工具

- 判定：成立
- 我验证的方式：

  ```powershell
  rg -n 'ToolRegistry\.register' src/brain/agent_tools_ultima.py `
    tools/venv-openjarvis/Lib/site-packages/openjarvis/tools/calculator.py `
    tools/venv-openjarvis/Lib/site-packages/openjarvis/tools/think.py
  rg -n '^TOOLS\s*=|^ANSWER_TOOLS\s*=' src/brain/agent_server.py
  ```

- 证据：AST 读得 `TOOLS` 精确 11 项，`ANSWER_TOOLS` 精确 5 项。自建装饰器在 96/206/239/264/305/377/486/796/873，工具名与 `TOOLS` 中九个 `ultima_*` 名称一致；底座 `calculator.py:114` 和 `think.py:12` 分别注册 `calculator`、`think`。集合恰好对应 11 项。
- 与我看到的主脑结论差异：无。边界是静态声明匹配，不等于本轮已启动进程并读取运行时注册表；声明式校验还必须尊重 `_ensure_tools_registered()` 的注册时序。

### C5 `test_agent_tools_extend.py:63-64` 是子集断言

- 判定：成立
- 我验证的方式：

  ```powershell
  $l=Get-Content src/brain/tests/test_agent_tools_extend.py
  61..64 | ForEach-Object { '{0}: {1}' -f $_,$l[$_-1] }
  rg -n 'issubset\(agent_server\.(TOOLS|ANSWER_TOOLS)' src -g '*test*.py'
  ```

- 证据：63、64 行分别为：

  ```python
  self.assertTrue(EXPECTED_EXTENDED_TOOLS.issubset(agent_server.TOOLS))
  self.assertTrue(ORIGINAL_ULTIMA_TOOLS.issubset(agent_server.TOOLS))
  ```

  它们不是等值断言。
- 与我看到的主脑结论差异：事实本身无差异。但“不是等值断言”不等于“注册表化安全”：这两条测试不会发现额外工具泄漏、顺序/重复、`ANSWER_TOOLS` 名单错误或禁用工具进入应答侧。

### C6 22 个散文件入度及 `agent_server.py` 18 个引用全部来自测试

- 判定：成立
- 我验证的方式：

  ```powershell
  @'
  import ast, pathlib, importlib.util, collections
  root=pathlib.Path("src")
  stems="interaction agent_server prompt_boundary environment agent_tools_ultima environment_upgrade capability intent bootstrap slot_adapter queue_source reporter voice_loop weather mainbrain_proposal agent_client memory_write_boundary orchestrator interaction_orb interface_route sentinel cli".split()
  targets={"src.brain."+x:x for x in stems}
  symbols=collections.Counter(); sites=collections.defaultdict(set); sources=collections.defaultdict(set)
  def canon(m):
      if m.startswith("brain."): return "src."+m
      if m in stems: return "src.brain."+m
      return m
  for p in root.rglob("*.py"):
      module=p.with_suffix("").as_posix().replace("/",".")
      package=module.rsplit(".",1)[0]
      t=ast.parse(p.read_text(encoding="utf-8-sig"),filename=str(p))
      for n in ast.walk(t):
          hits=[]
          if isinstance(n,ast.Import):
              hits=[canon(a.name) for a in n.names if canon(a.name) in targets]
          elif isinstance(n,ast.ImportFrom):
              m=(importlib.util.resolve_name("."*n.level+(n.module or ""),package)
                 if n.level else (n.module or "")); m=canon(m)
              if m in targets: hits=[m for a in n.names]
              else:
                  hits=[canon((m+"."+a.name).strip(".")) for a in n.names
                        if canon((m+"."+a.name).strip(".")) in targets]
          for m in hits:
              k=targets[m]; symbols[k]+=1; sites[k].add((p.as_posix(),n.lineno)); sources[k].add(p.as_posix())
  for k in stems: print(k,symbols[k],len(sites[k]),len(sources[k]))
  '@ | tools\venv-openjarvis\Scripts\python.exe -B -X utf8 -
  ```

- 证据：22 个方案数字全部可复现，0 个 AST 解析错误。关键三种统计单位如下：

  | 文件 | 方案值=导入符号数 | 导入语句处数 | 独立来源文件数 |
  |---|---:|---:|---:|
  | interaction.py | 20 | 9 | 9 |
  | agent_server.py | 18 | 18 | 12 |
  | prompt_boundary.py | 15 | 3 | 3 |
  | environment.py | 12 | 7 | 6 |
  | agent_tools_ultima.py | 11 | 6 | 3 |
  | environment_upgrade.py | 9 | 3 | 3 |
  | capability.py | 8 | 2 | 2 |
  | intent.py | 8 | 4 | 3 |
  | bootstrap.py | 7 | 7 | 2 |
  | slot_adapter.py | 7 | 7 | 7 |
  | queue_source.py | 6 | 3 | 3 |
  | reporter.py | 5 | 5 | 5 |
  | voice_loop.py | 4 | 4 | 3 |
  | weather.py | 3 | 2 | 2 |
  | mainbrain_proposal.py | 3 | 3 | 2 |
  | agent_client.py | 3 | 2 | 2 |
  | memory_write_boundary.py | 3 | 3 | 2 |
  | orchestrator.py | 2 | 2 | 1 |
  | interaction_orb.py | 2 | 2 | 2 |
  | interface_route.py | 1 | 1 | 1 |
  | sentinel.py | 0 | 0 | 0 |
  | cli.py | 0 | 0 | 0 |

  `agent_server` 的 18 个静态导入符号/语句来自 12 个文件，全部是测试；扩展 `rg` 到工作树第一方 `.py` 也未找到生产 import。`interaction` 的 20 则是生产 5 个导入符号/3 文件 + 测试 15 个导入符号/6 文件。

  必须更正术语：这些数字是“被导入符号/alias 出现数”，不是图论入度；标准入度应按来源节点去重。范围也是 `src/**/*.py`，不是全工作树。动态 `importlib`、字符串模块名、子进程入口和非 Python 调用不在该指标内。
- 与我看到的主脑结论差异：数值和“agent_server 全是测试 import”无差异；“18 个引用方”“20 个引用方”和“全仓入度”这些叫法不准确，实际分别只有 12、9 个来源文件，且统计范围是 `src`。

## 三、主脑结论中我认为有问题的地方

1. **同日两份文档的核心前提互相冲突。** `inventory:30-65` 已更正为四个自建注册表有生产调用；`plan v2:13/46-58/191-204/286-297` 仍以“三个空转”为核心病灶并建议接上或删除。当前源码支持前者，不支持后者。
2. **“生产零 unload／只有 8 处”把局部统计冒充全局统计。** `execution/server/ultima_bus/cli.py:55` 是明确生产反例，第一方范围总计 14 个调用。
3. **重名统计漏了 `ChannelRegistry`。** 当前 `src` 与底座同名类交集是 3 个；“只有 Skill/Memory 两处”不完整。
4. **插件总线搜索模式和规格落点不一致。** 规格规定落点是 `execution/server/ultima_bus/`，却只在 `src/` 搜 `plugin_bus/PluginBus/插件总线` 后推出全仓无实现。当前工作区已有内核、CLI 和根包门面。
5. **六个“引用次数”没有统一、可复现的口径。** 同一张表至少表现出大小写口径混用，且文本提及不应称为外部依赖引用。
6. **L 层归位论证把“权威核心落点”误当成“整层全部实现”。** L3、L7 在权威表本来就不是单文件；“一个文件放不进目录”是工程判断，不是证据结论。
7. **C1 的组数自相矛盾。** 文本称 4 组，却列 5 个模块；130 行只是所选 AST 节点跨度的算术和，不是净删行数或唯一可搬集合。
8. **monkeypatch 统计错误。** 实际 16 个调用、8 种符号、`_MAIN` 7 次，并遗漏 `ask_once`。直接搬函数的 patch 风险成立，但“一个都不能搬”过强。
9. **C6 把导入符号数命名为入度。** 这会把 `from module import A,B,C` 算成 3，而依赖图只有一条来源边，容易夸大耦合。
10. **`inventory` 文档自身有拼接残留。** `inventory:300-304` 在“命名混乱清单”标题下出现孤立的 plugin-bus/删除表格行，`:308-315` 又重复“第七节”，`:319` 再次出现同名附录。这不是代码事实错误，但会妨碍后续把它当权威底稿。

## 四、主脑未覆盖但我发现的重要事实

1. **插件总线实现存在，但未进入当前 HEAD。** `git status` 显示 `?? execution/server/ultima_bus/` 与 `?? ultima_bus/`，`git ls-tree HEAD` 无对应文件。工作区审查必须承认实现存在；提交/发布审查则必须同时指出它尚未纳入版本历史。
2. **`docs/specs/registry.md:55` 已把 `ultima-plugin-bus` 登记为“已实现，待独立评审”。** 这与两份待审文档的“只有规格”说法不一致，也说明 registry 权威表比模块化方案新或至少包含了方案未吸收的状态。
3. **插件总线的驻留保护与四个 `src.brain.*Registry` 不是同一调用链。** 当前 `BusKernel.unload()` 自己检查总线注册状态；生产 CLI 并不调用四个自建 Registry 的 `unload()`。后续要先定义谁是驻留真源，不能简单以“已有 CLI”宣称两套机制已经接通。
4. **`openjarvis.core.registry` 是 16 个具体注册表加 1 个基类。** 以后应分别写“16 个具体 Registry”或“17 个 Registry 类定义（含 RegistryBase）”，避免重复产生数量争议。
5. **0052 的队列状态与实际派发结果需要分开看。** `queue-status.json:1853-1859` 仍是 `executing`，但 note 明写 Codex 派发因 401/token 失效而失败，需要重新登录后重派；因此模块化方案不能把“executing”当作正在修改 `agent_server.py` 的充分证据，也不能假定其 commit 即将落地。
6. **文件时间顺序解释了部分矛盾但不能豁免。** `plan v2` 工作区时间为 22:02，`inventory` 为 22:11；后者做了注册表更正，前者未同步。进入 Owner 评审前必须先把两者重新对齐。

## 五、对方案可行性的独立意见

### 分批顺序

对当前的 `2.5 → 0 → 1 → 2 → 3 → 4`，我的结论是：**不能按现文执行**。

1. **第 2.5 批必须撤回并重写。** 它建立在“三个注册表空转”这一错误前提上，不能把“接上或删除”作为强制二选一，更不能在基线前删除当前有生产调用的代码。可以在第 0 批前做一个纯文档/架构决策批：明确自建 Registry、OpenJarvis Registry、`BusKernel` 三者的职责与唯一真源；任何代码迁移必须放到新鲜基线之后。
2. **第 0 批应当成为所有代码改动的第一门。** 先确认 0052 是完成、终止还是重新派发；记录 HEAD、目标文件哈希和目标测试基线。当前计划写死“580 passed / 1 failed”只能作为历史快照，验收应比对失败身份和行为，不应阻止新增必要测试导致 passed 数变化。
3. **第 1 批有条件可行。** risk/no_tool/content/prompts 的无状态提取切口总体合理；需要保持字节级提示词、兼容 re-export，并对实际依赖闭包加测试。`catalog` 不能在导入时过早解析注册表；当前九个自建工具由延迟 `_ensure_tools_registered()` 触发，校验时序必须显式设计。130 是搬迁节点跨度，不是承诺净减行数。
4. **第 2 批有价值，但应在注册完成后显式校验。** 推荐“catalog 只声明两个精确白名单；bootstrap/ensure 完成注册后调用 validate/resolve”。测试应断言 11 和 5 的精确集合及禁止集合，而不只是长度或子集。
5. **重写后的 Registry/Bus 批次不必阻塞第 1、2 批的目录布局。** 现文没有证明 `gates/`、`tools/catalog.py` 的位置依赖三个驻留 Registry 的去留。如果 Owner 决定统一驻留机制，应单独设计适配/迁移及回滚测试，再插入第 2 批之后或作为独立工单。
6. **第 3 批顺序基本可行，但属于中风险 API 迁移。** 先移出两个 wakeword 函数能消掉 `voice-next → brain.interaction` 的跨域边；随后再拆主链。需注意“20”是 9 个来源文件中的 20 个符号，不是 20 个调用方；对私有常量长期 re-export 只能作为过渡兼容层。
7. **第 4 批应保持可选并重新逐文件评估。** 标题称“15 个入度 2–3”，但自己的 E 表包含 11、12、15 等值，分类前提错误。物理移动 `weather.py/interface_route.py` 本身不会让代码改走 LLM；真正的行为约束应由接口和端到端测试保证。

建议顺序为：**文档/职责对齐（不改代码） → 0 → 1 → 2 → 独立的 Registry/Bus 统一工单（若 Owner 选择） → 3 → 4（可选）**。

### 六条机械判据

1. **“单一入口：相对导入 `level>0` 即违规”不可采用。** 正常包内依赖也会被误报；A1 的 `.registry` 正是这类合法相对导入。应先定义每个包的公开入口与允许边，再检查是否绕过入口，同时覆盖绝对导入。
2. **“无反向依赖：图无环”可作为必要检查，但不充分。** 一条违反层级方向的边完全可能不成环；应补允许依赖矩阵、强连通分量和动态导入清单。
3. **“外部读取的大写列表字面量即违规”不可采用。** 安全白名单可以合理地是常量；改成元组仍是字面量却能绕过正则。真正应检查的是注册完成后的解析路径、精确允许集合和 fail-fast 行为。
4. **“含 main 的文件生产入度必须为 0”只能作为本项目入口约定，不能当普适模块化判据。** 一个 CLI 模块可以同时提供稳定、可测试 API；应区分 `main()`、业务 API 和进程启动关系。
5. **“registry.py 有至少一个外部调用方”目标合理，但现有判据不足。** 一个 import 不等于调用或生产使用，装饰器/动态加载也可能没有直接调用。机检至少要区分注册、查询、卸载，区分生产/测试，并正确处理相对导入、别名、try/条件导入和动态入口。
6. **“私有函数前缀族 ≥3 即多职责”只能作人工审阅提示，不能固化为阻断门。** 它漏掉类方法和公开函数，也会把同一职责的不同动词误判为多领域；“降到 ≤2”没有经验或行为证据支撑。

## 六、复审声明

- 检查范围：`docs/reports/inventory-ultimaagent-l0-l10-20261112.md`、`docs/plans/plan-ultimaagent-modularization-20261112.md`、`docs/plans/product-plan.md`、`docs/specs/registry.md`、`docs/specs/plugin-bus-spec.md`；`src/**/*.py`；四个自建 Registry 及其调用方；`src/brain/agent_server.py`、相关测试；外部底座 `openjarvis/core/registry.py`、`openjarvis/tools/calculator.py`、`think.py`；当前工作区 `execution/server/ultima_bus/` 与 `ultima_bus/`；`agent_server.py` 的 Git 路径历史；0052 当前队列登记。
- 未检查项：未执行 pytest、未启动 `agent_server` 或插件总线、未验证运行时注册表内容、未做动态/反射导入穷尽证明、未审计插件总线全部行为与安全正确性、未核查所有非 Python 调用方、未复现六组件计数的原始未知脚本、未对约 450 个工作区改动做通用代码审计。
- 结论不超过检查范围。

REVIEW_DONE 12/12
