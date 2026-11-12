# 落地文件清单

- report version: `S1/v0.4`
- phase: `T1-only`

## src/window

- NEW_FILE `src/window/__init__.py`
- NEW_FILE `src/window/a2ui_validator.py`
- NEW_FILE `src/window/component_directory.json`
- NEW_FILE `src/window/vendor/a2ui-v0.8/server_to_client.json`
- NEW_FILE `src/window/vendor/a2ui-v0.8/catalog_description_schema.json`
- NEW_FILE `src/window/vendor/a2ui-v0.8/standard_catalog_definition.json`
- NEW_FILE `src/window/vendor/a2ui-v0.8/LICENSE`
- NEW_FILE `src/window/vendor/a2ui-v0.8/provenance.json`
- NEW_FILE `src/window/tests/__init__.py`
- NEW_FILE `src/window/tests/test_a2ui_validator.py`
- NEW_FILE `src/window/tests/verify_guardrails.py`
- NEW_FILE `src/window/tests/fixtures/official_v08_row.json`
- NEW_FILE `src/window/tests/fixtures/README.md`

## specs

- MODIFY_FILE `docs/specs/component-dsl-schema.md`
- MODIFY_FILE `docs/specs/registry.md`

## task card and new evidence

- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/task.md`
- NEW_FILE `tasks/cards/s1-window-dsl-schema/completion.md`
- NEW_FILE `tasks/cards/s1-window-dsl-schema/landed-files.md`
- NEW_FILE `tasks/cards/s1-window-dsl-schema/acceptance-evidence.md`
- NEW_FILE `tasks/cards/s1-window-dsl-schema/evidence/20261021T135937+0800/red-test.txt`
- NEW_FILE `tasks/cards/s1-window-dsl-schema/evidence/20261021T135937+0800/green-test.txt`
- NEW_FILE `tasks/cards/s1-window-dsl-schema/evidence/20261021T135937+0800/guardrails-final.json`
- NEW_FILE `tasks/cards/s1-window-dsl-schema/evidence/20261021T135937+0800/upstream-pin.txt`
- NEW_FILE `tasks/cards/s1-window-dsl-schema/evidence/20261021T135937+0800/scope-audit.json`
- NEW_FILE `tasks/cards/s1-window-dsl-schema/evidence/20261021T135937+0800/execution-summary.json`

未修改 `src/brain/`、`tasks/queue_engine/`、生产 `tasks/tasks.json`、原工单/计划、
其他任务卡、其他 docs、logs、scripts、_shared、全局主表或 sync。

## 2026-10-24 T1 修复续行

- MODIFY_FILE `src/window/a2ui_validator.py`
- MODIFY_FILE `src/window/tests/test_a2ui_validator.py`
- MODIFY_FILE `docs/specs/component-dsl-schema.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/task.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/completion.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/landed-files.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/acceptance-evidence.md`
- NEW_EVIDENCE_DIR `tasks/cards/s1-window-dsl-schema/evidence/20261024T074717+0800/`

未重新下载或改写固定 vendor；未修改 `docs/specs/registry.md`，因为组件目录和注册状态
没有变化。禁写域保持只读。

## 2026-10-24 独立审查 I1/I2/I3 修复续行

- MODIFY_FILE `src/window/a2ui_validator.py`
- MODIFY_FILE `src/window/tests/test_a2ui_validator.py`
- MODIFY_FILE `docs/specs/component-dsl-schema.md`
- MODIFY_FILE `docs/specs/registry.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/task.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/completion.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/landed-files.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/acceptance-evidence.md`
- NEW_EVIDENCE_DIR `tasks/cards/s1-window-dsl-schema/evidence/20261024T080632+0800/`

未修改固定 vendor、`src/brain/`、`tasks/queue_engine/`、生产 `tasks/tasks.json`、
原工单/计划、其他任务卡、scripts、shared、sync、全局主表或旧审计证据。

## 2026-10-24 最新独立审查续行复核

- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/task.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/completion.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/landed-files.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/acceptance-evidence.md`
- NEW_EVIDENCE_DIR `tasks/cards/s1-window-dsl-schema/evidence/20261024T081115+0800/`

当前 I1/I2/I3 行为通过原测试与最新审查探针重放，故本轮未修改
`src/window/`、`docs/specs/component-dsl-schema.md` 或 `docs/specs/registry.md`。
未修改固定 vendor、旧证据、其他任务卡、原工单/计划、scripts、queue_engine、
brain、shared、sync、生产 `tasks/tasks.json` 或全局主表。

## 2026-10-24 Video 资源遗漏修复续行

- MODIFY_FILE `src/window/a2ui_validator.py`
- MODIFY_FILE `src/window/tests/test_a2ui_validator.py`
- MODIFY_FILE `docs/specs/component-dsl-schema.md`
- MODIFY_FILE `docs/specs/registry.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/task.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/completion.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/landed-files.md`
- MODIFY_FILE `tasks/cards/s1-window-dsl-schema/acceptance-evidence.md`
- NEW_EVIDENCE_DIR `tasks/cards/s1-window-dsl-schema/evidence/20261024T081918+0800/`

未修改固定 vendor、旧开发/审查证据、其他任务卡、原工单/计划、scripts、
queue_engine、brain、shared、sync、生产 `tasks/tasks.json` 或全局主表；未执行
GUI、播放、录音、麦克风、T2/T3、提交、tag 或 Owner 冻结。
