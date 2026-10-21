# 验收证据

- 命令：`H:\UltimaAI\UltimaAgent\tools\python31313\python.exe tasks\tests\test_dispatcher.py -v`
- 结果：`Ran 8 tests in 2.025s`；`OK`。
- DI-01：已有普通执行中任务时，候选保持排队并追加等待事件。
- DI-02：同并行组允许第 2 个任务；已有 2 个执行中任务时第 3 个保持排队。
- DI-03：派发进程、执行会话、活跃 run 三探针分别拦截；探针抛错时按忙处理；真实重复派发只产生一组六件套。
- DI-04：真实指定 Python 子进程使用 `CREATE_NO_WINDOW | DETACHED_PROCESS`、`shell=False`；约 10ms 轮询可见顶层窗口，全程捕获数 0。真实锁持有子进程同样捕获数 0。
- DI-05：`.pause-dispatch` 存在时不派发，返回只读审计原因。
- DI-06：不存在的父 PID 触发 `mode=read-only`、`action=graceful-exit` 失联标记。
- 锁竞争：独立隐藏进程持有 OS 文件锁，派发器实际竞争失败并 fail-closed，不创建运行六件套。

判定：执行端自核通过；独立 W2 尚未执行。
