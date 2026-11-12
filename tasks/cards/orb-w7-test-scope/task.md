# 任务卡：orb-w7-test-scope

- **task_id**：orb-w7-test-scope
- **stage**：G-ORCH 编排层（v0.1）
- **标题**：pytest 作用域固定（排除历史备份目录）
- **创建**：2026-11-08 · 主脑过渡托底（DeepSeek 未接线，接线后交还外脑）
- **M1 声明**：已查能力注册表，仓库当前**无任何 pytest 配置文件**（`pyproject.toml`/`pytest.ini`/`setup.cfg`/`tox.ini` 均不存在），pytest 走默认根递归，`Topo Backup` 被收进导致 3,430 errors；本次只新增一个 `pytest.ini`，无新依赖

## goal

新增 `pytest.ini`，用 `testpaths` 圈定项目自有代码目录（`tests src scripts tasks execution`），让"全量"重新可用：既覆盖真实回归（1143 例），又不收进 `libs`/`legacy-topo`/`data`/`docs`/`tools` 等外部与历史源码。禁止：改任何既有测试文件、改 `addopts`、把外部目录收进作用域。

## acceptance[]

- [ ] ACCEPT: 新增 `pytest.ini`，`[pytest]` 段含 `testpaths = tests src scripts tasks execution`
- [ ] ACCEPT: `norecursedirs` 同时含 `"Topo Backup" .git node_modules venv-* tools/venv-* libs legacy-topo data docs artifacts research models dist logs reports`
- [ ] ACCEPT: 仓库根执行 `python.exe -m pytest -o addopts= -q`（不带位置参数），收集阶段 errors=0，收集总量约 1143
- [ ] ACCEPT: 回执给出实际 passed / failed / skipped 三项数字
- [ ] ACCEPT: 未修改任何 `test_*.py` 内容；`libs`/`legacy-topo`/`data`/`tools` 不在作用域内

## dependsOn[]

- 无

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\pytest.ini`
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w7-test-scope\`

## priority

- 88

## reasoningEffort

- high

## category + skill

- category: eng-orchestration · skill: eng.test（测试作用域与验收口径）

## receipt

- reviewReason: 待 Codex 执行后回填
- stdoutText: 待回填
- evidence: 待回填
- acceptance 逐项核对: 待回填

## retryCount

- 0

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| U-01 配置落盘 | `pytest.ini` 的 `norecursedirs` | 文件存在且键齐全 | 文件内容 |
| U-02 根目录实测 | 根目录全量跑一遍 | errors=0 且给出三项数字 | 命令输出 |
| U-03 不越界 | 不动测试文件、不设 testpaths | diff 仅含 pytest.ini | git diff 清单 |
