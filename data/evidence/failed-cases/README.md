# UltimaAgent 失败 case 归档约定

本目录保存可重复、已脱敏、可离线复测的真实失败输入。它不是自由格式日志池；
每个 case 使用独立目录，目录名固定为 `<failure-slug>-<YYYYMMDD>`。

## 必需内容

每个 case 目录至少包含：

- `case.json`：机器可读输入、失败阶段、实际观察、期望结果和复测命令。
- `README.md`：来源、为何判失败、修复或兜底语义、复测入口。

`case.json` 必需字段：

- `case_id`、`work_order`、`captured_at`、`failure_stage`
- `input`：重放所需的最小脱敏输入
- `model_output` 或等价失败载荷
- `actual`：真实门禁结果/错误签名
- `expected`：复测的唯一期望
- `retest.command` 与 `retest.test`

## 归档纪律

1. 只归档真实触发过的失败或被 gate 拒绝的载荷，禁止编造堆样例。
2. 去除 token、密钥、个人数据和绝对用户路径；保留足够的结构与错误签名。
3. case 一经引用即保持不可变；语义变化新建带日期/修订后缀的目录。
4. 复测必须离线运行，不调用外网或真实模型；写入使用临时目录。
5. 测试必须实际读取归档 case，避免 README 与回归入口漂移。

## 统一复测入口

在项目根目录执行：

```powershell
tools\venv-openjarvis\Scripts\python.exe -X utf8 -m unittest src.brain.tests.test_closed_loop_audit -v
```
