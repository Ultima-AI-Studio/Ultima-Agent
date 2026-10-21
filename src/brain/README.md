# 任务状态文字闭环

本目录实现 `S1/v0.3` 的文字场景：明确的“查任务状态”请求经过意图解析后，只读 `tasks.queue_engine.QueueStorage` 的当前索引，再生成中文聚合汇报。它不播放声音、不录音、不调用麦克风，也不实现语音能力。

## 模块边界

- `intent.py`：离线、确定性的窄规则识别。覆盖本场景的礼貌问法、中文标点和显式请求；否定、引用命令、陈述、空输入保持静默。它不是通用自然语言分类器。
- `queue_source.py`：先确认 `tasks.json` 存在，再通过 brain 层只读适配器调用冻结队列引擎的 `QueueStorage.load_tasks()` 读取和验证索引。适配器只覆写会创建目录的 `ensure_layout()`，不修改冻结引擎；读取前后目录树与文件字节保持不变。当前状态只来自索引，不把历史失败事件混入当前异常。任务标题只允许从任务库 `cards/<task_id>/task.md` 读取。
- `reporter.py`：仅在意图明确命中后读取队列。失败和冻结优先；其他任务聚合，不逐条列出。下钻 ID 只接受队列引擎同口径的安全 task_id。
- `cli.py`：文字 CLI。正常查询退出码为 `0`；状态读取失败、未知或非法下钻 ID 退出码为 `2`；未命中不输出内容且退出码为 `0`。

缺失、损坏或字段非法的任务库统一明确返回“状态读取失败”，不会伪装为空队列。生产 `tasks/tasks.json` 为空时则如实报告 0 个任务，且不会写入示范数据。

## 可复跑命令

在项目根目录执行，固定使用项目内 Python：

```text
H:\UltimaAI\UltimaAgent\tools\python31313\python.exe -X utf8 src\brain\tests\test_intent.py -v
H:\UltimaAI\UltimaAgent\tools\python31313\python.exe -X utf8 src\brain\tests\test_queue_source.py -v
H:\UltimaAI\UltimaAgent\tools\python31313\python.exe -X utf8 src\brain\tests\test_reporter.py -v
H:\UltimaAI\UltimaAgent\tools\python31313\python.exe -X utf8 -m unittest discover -s src\brain\tests -p test_*.py -v
H:\UltimaAI\UltimaAgent\tools\python31313\python.exe -X utf8 src\brain\cli.py "查任务状态"
H:\UltimaAI\UltimaAgent\tools\python31313\python.exe -X utf8 src\brain\cli.py --task-id TASK_ID "查任务状态"
```

测试中的 20/1 场景使用隔离临时任务库，通过真实 `QueuePlanner.enqueue()` 建卡，并用真实 `StateMachine.transition()` 合法迁移 19 项到已完成、1 项到失败；统计与汇报再由生产读取模块生成。
