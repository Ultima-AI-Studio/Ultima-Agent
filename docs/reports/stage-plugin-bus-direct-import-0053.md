# 插件总线直连检测修复阶段报告

T1 → T3 已按序完成。`_audit_imports()` 现在同时识别模块 ID 与所有已安装版本 `manifest.entry` 的顶层包名，自引用的模块 ID/包名均放行；既有 `plugin.direct-import.denied` 事件增加 `package` payload 字段，动态导入拦截和 `plugin.direct-connect.denied` 均未改动。

## Gate 结果

- T1：修复后、装饰器移除前，pytest 得到工单要求的 `Unexpected success`；AST 解析退出码 0；`RESIDENT_DOMAINS` diff 命中 0。原始输出见 `evidence/plugin-bus-direct-import-0053/gate-t1.txt`。
- T2：仅移除 `@unittest.expectedFailure` 并更新 docstring；最终专用解释器运行得到 `9 passed in 23.86s`，无 xfailed、无 unexpected success。原始输出见 `evidence/plugin-bus-direct-import-0053/pytest.txt`。
- T3：真实包名与模块 ID 形态均被拒，`import os` 放行；相对最新 v1.1 run 的 tracked-only 派发基线，差分恰为两个获准代码文件。原始输出见 `contrast-output.txt` 与 `baseline-diff.txt`。

## 回执

链路号/工单号: wo-ultimaagent-20261113-0053

执行端: Codex

完成状态: 已完成

根因结论: `_audit_imports()` 只以模块 ID 比对静态 import，而插件运行时使用 `manifest.entry` 顶层真实包名，因此真实包名未命中旧比较键并形成绕过。

产出路径: `execution/server/ultima_bus/kernel.py`; `execution/server/tests/test_ultima_bus.py`; `docs/reports/stage-plugin-bus-direct-import-0053.md`; `docs/reports/evidence/plugin-bus-direct-import-0053/`; `docs/reports/evidence/plugin-bus-direct-import-0053/contrast_experiment.py`; `docs/reports/evidence/plugin-bus-direct-import-0053/gate-t1.txt`; `docs/reports/evidence/plugin-bus-direct-import-0053/pytest.txt`; `docs/reports/evidence/plugin-bus-direct-import-0053/contrast-output.txt`; `docs/reports/evidence/plugin-bus-direct-import-0053/baseline-diff.txt`; `docs/reports/evidence/plugin-bus-direct-import-0053/reverse-assertions.txt`

验收证据: pytest `9 passed in 23.86s`（0 xfailed / 0 unexpected success）；对照实验 `real package -> DENIED`, `module ID -> DENIED`, `os -> ALLOWED`, `CONTRAST_RESULT=PASS`；反向断言 `RESIDENT_DOMAINS_DIFF_MATCHES=0`, `SPEC_DIFF_EXIT=0`, `REGISTRY_DIFF_EXIT=0`；派发基线差分仅 `execution/server/ultima_bus/kernel.py` 与 `execution/server/tests/test_ultima_bus.py`。

越界声明: 无

环境声明: 本机为真实开发机，所有测试与对照实验均在实际开发环境执行，无模拟器声明。

开源替代排查: N/A；本单为纯缺陷修复，无新模块，未引入任何第三方依赖。
