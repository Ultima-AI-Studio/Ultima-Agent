# E3 接入 CV3 音色技术规格（工单 0035 v2.0）

本文件只出规格，不含实现代码；本单只出规格、不写实现代码。

## 1. 形态结论

采用常驻预热 worker：独立进程运行在 `tools\venv-openjarvis\Scripts\python.exe`，由该进程持有 torch 与 CV3 模型；E3 主进程只经 IPC 传参，不 import torch。依据包括：`src/voice-next/README.md:5` 记录 CV3 冷启动联调等待数分钟，`src/voice-next/README.md:44` 明确实时入口不导入 Torch。

- 否决单次子进程：每次请求都触发数分钟冷启动，不可接受。
- 否决本地 HTTP 服务：引入端口占用、鉴权与探活依赖，但相对同机 IPC 没有足够收益。

## 2. IPC 协议

传输采用一问一答的本机命名管道；每个请求携带唯一 `request_id`，响应回传同一标识与返回码。正文为 UTF-8 JSON 帧，帧长必须受限，worker 只接受 E3 主进程创建的本机管道连接。

| 字段 | 必填 | 缺省 | 语义 |
|---|---|---|---|
| `text` | 是 | 无 | 待合成的非空文本。 |
| `path` | 是 | 无 | E3 指定的输出 wav 路径；worker 原子写入后返回。 |
| `voice_id` | 否 | `CV3` | 目标音色标识；本规格只定义 CV3。 |
| `sample_rate` | 否 | `None` | 不要求 worker 固定输出采样率；`None` 表示交由 `play()` 的 soxr 重采样。 |

## 3. 接口签名与兼容性

接口签名为 `synthesize(text, path, *, voice_id=None, sample_rate=None)`。

前两个位置参数与当前 `synthesize(text, path)` 一致；新增参数均为仅限关键字且有缺省值，因此现有调用点零改动。成功时仍返回可播放的 `path`，不得把采样率写死进 E3 代码逻辑。

## 4. 超时与返回码

| 返回码 | 名称 | 条件 |
|---|---|---|
| `0` | `CV3_OK` | wav 已原子落盘且通过基本格式校验。 |
| `10` | `BAD_REQUEST` | 缺少 `text`/`path`、文本为空或字段类型错误。 |
| `20` | `WORKER_NOT_READY` | 预热未完成或 worker 正在重启。 |
| `21` | `SYNTH_TIMEOUT` | 单次合成超过 30 秒上限。 |
| `22` | `WORKER_CRASHED` | 请求处理中 worker 进程异常退出。 |
| `23` | `MODEL_LOAD_FAILED` | CV3 模型或音色资源加载失败。 |
| `24` | `OUTPUT_INVALID` | 输出缺失、为空或不是可读 wav。 |
| `25` | `IPC_ERROR` | 管道连接、帧读取或响应校验失败。 |

启动预热上限为 300 秒；主进程发出请求后，IPC 建连上限为 2 秒、单次合成响应上限为 30 秒。超时必须取消当前请求并进入下述回收流程，禁止无限等待。

## 5. 失败语义

CV3 不可用时降级 SAPI 并上报：本轮照常出声，`data/voice-next/status.json` 的 `tts_backend` 写 `sapi_fallback`，并记录包含返回码、`request_id` 与 worker 状态的日志告警。禁止静默降级。

`BAD_REQUEST` 属调用错误，必须记录错误并拒绝把空文本送入 SAPI；其余不可用类返回码按上述规则降级。CV3 恢复并成功合成后，`tts_backend` 才可恢复为 `cv3`。

## 6. Worker 生命周期

- 预热时机：E3 启动即预热。依据是 README 已记录冷启动需等待数分钟；若延迟到首轮，首个用户回合会直接承受冷启动。
- 保活机制：主进程每 5 秒发送一次健康探针；连续 3 次未响应即把 worker 标为不可用，后续请求直接走可见降级。
- 超时回收：单次合成超过 30 秒后，先发取消；2 秒内未退出当前任务则终止 worker 进程树，清理未完成的临时 wav。
- kill 与重启：异常退出、超时强杀或模型加载失败后等待 5 秒再重启并重新预热；10 分钟内最多自动重启 3 次。超过上限后保持 SAPI 降级，每 60 秒只做一次恢复探测，进程退出时必须回收所属 worker。

## 7. 验收门槛

机检部分必须同时满足：目标 wav 存在、非空且可解析；日志中存在同一 `request_id` 的 CV3 生成成功记录；记录已加载模型与音色资源的 SHA256 指纹；`status.json` 的 `tts_backend` 为 `cv3`，且没有对应请求的降级告警。

人工部分由 Owner 听辨目标音色，确认确为预期 CV3 音色并判断自然度。该项不能纯机检：当前没有人工 gold 数据，也没有经过标定的说话人嵌入相似度阈值；仅凭 wav 存在或未标定相似度不能替代 Owner 验收。

本规格不代表 CV3 已接入 E3，也不代表目标音色已经验收。

## 8. 实现记录（2026-11-11，落地偏离对照）

本节记录实际落地与上文条款的差异。**上文未被实现的部分如实列出，不得视为已满足。**

**形态**：复用项目既有的 `src/brain/voice/daemon.py::VoiceDaemon`——行协议（stdin/stdout JSON lines、一问一答、就绪标记 `{loaded}`、`%TEMP%\ultima-voice-daemon-<name>.pid` 全局单实例锁），宿主为 `src/voice-next/turn_worker.py` 进程，daemon 名 `tts-voice-next`。**未**新建 §2 的命名管道，理由：该组件已存在且被既有 CV3 验收覆盖（906 tests / 0 failures），另造管道属重复实现，违背「能用成熟组件不自造」的项目纪律。

| 条款 | 设计 | 实际落地 | 状态 |
|---|---|---|---|
| §2 IPC | 本机命名管道 + `request_id` | `VoiceDaemon` 行协议 | 偏离（理由见上） |
| §3 签名 | `synthesize(text, path, *, voice_id, sample_rate)` | `synthesize_reply(text, out_wav, timeout=300)`，返回 dict（`engine`/`rate`/`seconds`/`device`） | 偏离 |
| §4 返回码 | 0 / 10 / 20–25 整数码 | `{"ok": bool, "error": str}` + `fallback_from` / `cv3_error` | 偏离（底层协议即如此） |
| §5 降级值 | `tts_backend = sapi_fallback` | `tts_backend ∈ {cv3, windows-sapi-fallback}`，切换时上报 `tts_backend_switch` 事件 | 字段名不同 |
| §6 健康探针 | 每 5s 探针、连续 3 次失联标记不可用 | **未实现** | 缺口 |
| §6 超时回收 | 30s 上限 + 取消 + 2s 未退则杀进程树 | 请求入参有 `timeout`，但底层 `readline()` 自身无超时；**未实现强杀** | 缺口 |
| §6 重启限制 | 10 分钟内最多重启 3 次 | 实现为**合成失败累计 3 次即停用 CV3 并回退 SAPI**（`_CV3_MAX_FAILURES`），非进程重启计数 | 近似 |

**风险声明（对应 §6 两个缺口）**：daemon 若「活着但不再应答」，`request()` 的 `readline()` 会阻塞到进程退出为止，该回合表现为超时且 worker 线程挂住。当前无看门狗，仅靠 `live.py` 的 `worker_timeout_seconds=90` 在外部观测。

**实测（2026-11-11 真机）**：`tts_backend=cv3`、`tts_cv3_ready=true`、`tts_warm_seconds=32.8`、`tts_prompts` 四项全 true；`data/voice-next/prompts/*.wav` 全部 **24000Hz / 单声道 / 16bit**（CV3 输出特征，`play()` 经 soxr 重采样到 44100 播放）；`cv3-prewarm.wav` 仅 0.16s——**首次推理截断**，故探针必须消耗掉首推（见 lessons-log L135）。

**§7 人工验收仍未达成**：目标音色是否即 Owner 期望者尚需听辨；零样本参考音频当前挂 `config/voice-profile.json` 的 `yangmi-ref`，**是否为目标音色未确认**。
