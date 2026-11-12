# 落地文件清单

- work order: `wo-s1-composite-window`
- phase: `T2-text-core-only`
- completion: `partial`

## src/window（仅新增）

- T2_NEW_FILE / REVIEW_REPAIR `src/window/result_to_a2ui.py`
- T2_NEW_FILE / REVIEW_REPAIR `src/window/offline_renderer.py`
- T2_NEW_FILE / REVIEW_REGRESSION `src/window/tests/test_text_core.py`
- T2_NEW_FILE / UNCHANGED_THIS_ROUND `src/window/samples/t2_text_core.json`

没有修改 T1 接受清单中的 `__init__.py`、validator、旧测试、fixtures、vendor、
component directory、两份规格或 T1 卡；新模块由调用方直接导入。

本轮修复仅包含：有界整数十进制转换、转换/渲染显式栈、空 `styles` 拒绝、
Unicode 标量检查及对应运行回归；没有新增组件、资源、action、主题或原生挂接。

## T2 卡与阶段证据

- MODIFY_FILE `tasks/cards/s1-window-composite-render/task.md`
- MODIFY_FILE `tasks/cards/s1-window-composite-render/completion.md`
- MODIFY_FILE `tasks/cards/s1-window-composite-render/acceptance-evidence.md`
- MODIFY_FILE `tasks/cards/s1-window-composite-render/landed-files.md`
- NEW_EVIDENCE_DIR `tasks/cards/s1-window-composite-render/evidence/20261024T085613+0800/`

新证据目录包含修复前基线、六项 RED、61 项全量窗口测试、四发现运行回归、
T1 原 91 探针重放、冻结 guardrail、保护源前后哈希、范围审计、Brain 空队列
A2UI 批次、静态 HTML、机器可读验证摘要与最终独立读回。

未修改 `brain/`、`queue_engine/`、`host-shell/`、`docs/`、`shared/`、`sync/`、
生产 `tasks/tasks.json`、原工单、任务计划、其他卡、Owner 批准、tag 或发布资产。
未启动 GUI/原生宿主，未使用音频、录音、麦克风、网络或公开 RPC。
