# 验收证据

## 失败测试

- 命令：`H:\UltimaAI\UltimaAgent\tools\python31313\python.exe -X utf8 src\brain\tests\test_reporter.py -v`
- 预期失败：`ModuleNotFoundError: No module named 'src.brain.reporter'`，见 `logs/aggregate-report-test-2026-10-21-failing.txt`。

## 开发自检通过

- 同命令最终结果：`Ran 6 tests`，`OK`，见 `logs/aggregate-report-test-2026-10-21.md`。
- 20/1 真实场景输出先写“当前共 20 个任务，有 1 个异常”，再写唯一失败详情，最后将其余 19 项聚合省略；输出原文已落盘。
- 正常 ID 与失败 ID 均可明确下钻；未知 ID 返回未找到；含斜杠、反斜杠、盘符或绝对路径的 ID 在读取队列前即拒绝。
- 未命中意图不读取队列、输出为空、不中断。
- 缺失存储明确“状态读取失败”，不冒充 0 个任务。
- CLI 由 `spawn_hidden` 零窗口拉起，正常查询退出码 0。

## 综合与冻结基线

- 文字闭环联合测试：13/13 通过，见 `logs/text-loop-all-tests-2026-10-21.txt`。
- 冻结队列引擎：首次完整回归 61/62，单项定向复跑通过，第二次完整回归 62/62；失败及恢复日志均保留，冻结源码未修改。
- v0.1：tag 解引用提交为 `43ce13021f16f191bb36615ebb6c68465bf201fa`；source-manifest 36/36；生产 `tasks.json` 哈希不变，见 `logs/frozen-baseline-verification-20261021.json`。

判定：开发自检通过；独立 W4 尚未执行，不创建 tag、不作 Owner 签字。
