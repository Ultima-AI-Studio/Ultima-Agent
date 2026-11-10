# grounded=false 兜底失败样例

- Case：`grounded-false-fallback-20261108`
- 工单：`wo-ultimaagent-20261108-0026`
- 失败阶段：结构化回答真实性门
- 真实失败：模型输出声称任务完成，但 `tool_results=[]` 且
  `grounded=false`；真实 `ReplyVerifier` 返回 `grounded_required`，该回答不得
  直接交付。
- 期望兜底：允许一次同类离线重答后仍未 grounded，则返回固定可靠性兜底文案，
  `degraded=true`，不泄露未证实结论。

复测入口：

```powershell
tools\venv-openjarvis\Scripts\python.exe -X utf8 -m unittest src.brain.tests.test_closed_loop_audit.TestClosedLoopAudit.test_grounded_false_archived_case_falls_back_offline -v
```

测试从 `case.json` 读取真实失败载荷，并只在外部模型请求边界注入固定返回；
护栏、结构化校验和兜底状态机使用生产代码，且不访问外网或真实模型。
