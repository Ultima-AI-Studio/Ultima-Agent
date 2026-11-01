# 中文持续流 KWS 新路径离线验证报告（2026-11-01）

工单：wo-ultimaagent-20261101-0019。
状态：离线技术门独立审计 PASS；待真人与真实采集验证，未生产切换，未进行真人/远场验收。

## 路线

使用 WeKws 固定版本的官方 KeyWordSpotter 持续流接口，而非 FunASR 整句 AutoModel KWS 接口。
源码 commit 6a45aeb994dd81c0969ff877a5a7c46d60ed0c86；WeNet tokenizer commit 1a94771df418325fd335b0b53776f83d74a8111d。
模型为配套 thuduj12/kws_wenwen_fsmn_ctc；权重 SHA256 d3d89b5dde08c2926d46a97eab6f7179a87b1946ccebd16c02e77042ea8389fe。
源码与模型均核实 Apache License 2.0。官方词表转换在独立派生配置内完成，不更改下载原件。

## 当前可用入口

src/voice-next/bootstrap.ps1：固定源码、模型、依赖的新环境安装；不启动语音服务。
src/voice-next/stream_runner.py：16kHz 单声道 PCM16 WAV 按300ms逐包输入官方运行时，JSON证据输出；每个文件前后 reset_all。
新环境 tools/venv-voice-next。无麦克风/播放接口，不导入旧 daemon、不修改旧参数。
测试词“你好问问”、固定阈值0.5仅用于本轮离线验证，未取代用户“幂幂”配置。

## 实测

- 新环境接口测试：5 passed。覆盖帧不重复消费、文件结束前事件、格式拒绝、异常复位、空文件拒绝。
- SAPI 合成“你好问问”同一 WAV 重复3轮：每轮1次命中；事件在5.68秒文件输入到2.4秒时产生，不依赖EOF。
- 合成其他问题5.35秒：0次命中；合成静音30秒：0次命中。
- 同进程重放，CPU双线程：各轮RTF约0.022–0.024，每300ms包中位处理约6ms。首次独立进程冒烟RTF为0.844，冷启动/库初始化不得忽略，实际产品应常驻预热。
- 这些合成样本只证明接口、缓存、逐包触发和处理能力；不构成真实召回/误报率证据。
- 旧路径快照19文件独立回读：0漂移。

## 证据

- data/evidence/voice-next/plan-review.json：独立计划评审PASS及exact digest。
- data/evidence/voice-next/offline-batch-probe.json：分轮事件、样本哈希、处理耗时与null质量指标。
- data/evidence/voice-next/smoke-positive.json：首次独立进程冒烟。
- data/evidence/voice-next/legacy-readback.json：旧路径回读。
- src/voice-next/requirements.lock.txt：47项精确依赖。
- config/voice-next/model.lock.json：8个上游文件修订和哈希。

## 未完成的产品门

真人固定词/相似词/自然背景声、不同距离下的唤醒评测；麦克风连续采集与唤醒事件接入；ASR迁移；Owner验收与运行入口切换。
以上未完成，不能宣称达到小爱L05C或已经修复用户真实唤醒问题。

## 回执边界

链路：0019；执行端：当前Codex聊天内联，新分支codex/voice-fsmn-new-path。
根因结论：原FSMN推荐缺少可运行的持续流接口证据；改用WeKws配套官方运行时已取得离线即时事件证据。
越界：未改旧daemon、KWS基线、voice-profile/keywords、ASR、TTS、主脑；未录音、播放、上传私人音频或停止进程。
环境：Windows/Python3.13.16，torch2.8.0+cpu，官方网络下载；所有依赖仅安装新环境。

## 下一步

先将此独立KWS入口接到正确的麦克风持续采集，明确只显示一个生效词；进行真人和自然背景声验证，达标再接交互。KWS入口稳定后再接官方流式ASR，不同时变更全部引擎。

## 独立审计与版本保全

独立审计 /root/audit_wekws_proof 为 PASS，无 Critical/Important 问题；独立复跑5项测试与真实模型重放均通过。模型缓存[1,128,11,4]、特征缓存[4,80]、波形残留最多320采样；文件前后全量复位为空。详见 data/evidence/voice-next/independent-audit.json。
旧基线tag已推送GitHub，远端peeled commit=e5c72cc34ad22339625fe777f819a726bd8538f4；只在命令内清空通用与GitHub专用代理，没有修改全局配置。新路径仅建立离线技术检查点，不打产品frozen标签。
