# KWS 唤醒词动态改词自动化验证阶段报告

工单：`wo-ultimaagent-20261031-0009`

## 执行边界与裁定

- 权威入口：`docs/INDEX.md`；任务工作流读取 `_shared` 唯一权威源。
- 原地执行：用户指定 `H:\UltimaAI\UltimaAgent`，且 `models/`、`data/` 是本单运行所需的未跟踪现网资产；只修改工单声明写域。
- 接口裁定：`voice_profile.apply_to_daemon()` 会按 profile 重写词表。为避免覆盖 CLI 的多词结果，本单采用其公开实现已确认的“原子替换 `keywords.txt` → mtime 触发跨进程热重载”机制，不改冻结接口与 daemon 逻辑。
- 既有工作树：冻结文件与基线文档在本单开始前已有用户改动；本单以 T0 哈希为零漂移比较基准，不回滚、不吸收这些改动。

## T0 环境盘点与工具链核验

Gate：**PASS**

| 检查项 | 结果 | 证据 |
|---|---|---|
| C1 sherpa-onnx 2.0.0 | PASS | `t0-env-probe.txt` |
| C2 官方 text2token/ppinyin | PASS | `t0-env-probe.txt` |
| C3 模型、tokens、现网词表 | PASS | `t0-env-probe.txt` |
| C4 HotReloadSpotter 与公开接口只读核验 | PASS | `t0-env-probe.txt` |
| C5 证据落盘 | PASS | `docs/reports/evidence/kws-reconfig/t0-env-probe.txt` |

保护基线 Git blob ID（由 `git hash-object` 计算）：baseline `90f2d1f5aa62a2ce270a95a5ac8f3c2c42eb3eb1`；voice_profile `4824709bb99123926575aa68689be5911f725ada`；daemon `68a24b6781bbc9885fcb09f9c97ffb362787adff`；tokens `1d0c44fce10a39ad38f4b7e73ba046cf95eb1552`。

## T1 CLI 实现

Gate：**PASS**

| 检查项 | 结果 | 证据 |
|---|---|---|
| 中文帮助与 `--add/--replace/--list/--validate` | PASS | `t1-cli-usage.txt` |
| 官方 text2token ppinyin，默认 `:2.0 #0.08` | PASS | `t1-cli-usage.txt` |
| 原子写、时间戳备份、raw 同步 | PASS | `t1-cli-usage.txt` |
| `voice_profile.apply_to_daemon` 公开接口写入 | PASS | 专项测试 + 真实 CLI 输出 |
| daemon 同 PID 热重载 | PASS | PID 14068，最终 11:28:34 日志 |
| JSON 输出含生效词表/备份/热重载/token 行 | PASS | `t1-cli-usage.txt` |

TDD：非音频专项最终 `16 passed, 3 deselected in 4.69s`。真实链路最终生效词为 6 个“贾维斯”变体、“查天气”和 ULTIMA；替换验证用“星期五”已移除。完整输出见 `docs/reports/evidence/kws-reconfig/t1-cli-usage.txt`。

## T2 自动化验证

Gate：**PASS**

| 检查项 | 结果 | 证据 |
|---|---|---|
| C1 本地 TTS“查天气”离线命中 | PASS | `t2-verify/new-word.{wav,json}` |
| C2 本地 TTS 自然语句中的“贾维斯”回归命中 | PASS | `t2-verify/retained-jarvis.{wav,json}` |
| C3 隔离词表 add 前命中、replace 后同一 WAV 不命中 | PASS | `t2-verify/replaced-word-{before,after}.json` |
| C4 空词/空格词/阈值 1.0 非零退出且零写入 | PASS | `t2-specialized-pytest.txt` |
| C5 venv-openjarvis 全量回归 | PASS | `786 passed, 36 warnings, 120 subtests passed` |

专项命令：`tools\venv-asr\Scripts\python.exe -m pytest scripts\test_kws_reconfig.py -q -s` → `19 passed in 29.69s`。

工程命令：`tools\venv-openjarvis\Scripts\python.exe -m pytest src -q` → 最终 fresh 运行 `786 passed, 36 warnings, 120 subtests passed in 266.28s`。36 条均为既有 nemoguardrails/pydantic 依赖警告，已如实记录，零失败、零错误。

实现期发现并闭合：整体替换若保留“贾维斯”，需保留公开 voice profile 中已验证的 6 个发音变体，并把本次 `--score/--threshold` 逐行应用；新词仍只接受官方 ppinyin 输出。替换语义测试使用隔离临时词表完成 add→命中→replace→同一 WAV 不命中的真实状态迁移。

## T3 收口与基线核对

Gate：待执行。

## 越界声明

截至 T2：未修改模型权重、ONNX、`tokens.txt`、KWS 全局参数、`voice_profile.py`、daemon 既有逻辑或 W6 UI；未杀死或重启守护进程。热重载前后 PID 均为 14068。T2 后保护哈希与 T0 完全一致。
