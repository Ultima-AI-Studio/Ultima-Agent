# 验收证据

## 失败证据保留（第 1 次自核）

- 命令：`H:\UltimaAI\UltimaAgent\tools\python31313\python.exe -m unittest -v tasks.tests.test_storage`
- 错误原文：`ModuleNotFoundError: No module named 'tasks'`；`Ran 1 test`；`FAILED (errors=1)`。
- 根因：项目隔离 Python 的路径配置不自动包含当前工作目录，测试模块尚未进入产品逻辑。
- 修复：测试入口按自身文件位置显式加入项目根；不更改全局环境或指定 Python。

## 通过证据（第 2 次自核）

- 命令：`H:\UltimaAI\UltimaAgent\tools\python31313\python.exe tasks\tests\test_storage.py -v`
- 结果：`Ran 6 tests in 0.179s`；`OK`。
- ST-01：临时库创建 `cards/queue/events/runs/archive` 五目录。
- ST-02/ST-03/ST-04：仅允许 11 个索引字段，额外 `goal` 被拒；真实索引为 `[]`，无正文。
- ST-05：连续追加两条事件，第二次写入后首段字节保持不变。
- ST-06：生成并核对 before/out/err/done/session/progress 六件套名称。
- ST-07：归档索引后任务卡正文仍存在，未删除文件本体。
- ST-08：默认阈值以 10,001 条触发，归档 1 条终态索引并保留 10,000 条。

判定：执行端自核通过；独立 W2 尚未执行。
