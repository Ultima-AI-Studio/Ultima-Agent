# 验收证据

## Gate

- 判定：`PASS`
- 计数：`9 GREEN / 0 RED`
- 权威检查表：`logs/environment-check-2026-10-21.md`
- Gate 文件：`docs/reports/evidence/stage1-host-shell/T1-envcheck.md`

## acceptance[] 逐项核对

- PASS：九项均列出项名、版本/路径、真实运行证据与状态。
- PASS：九项全部 GREEN；没有把目录存在、进程启动或静态检查冒充运行通过。
- PASS：复检表已落盘；历史 3/6 失败表与三件套均保留。

## 关键证据

- WinUI x64 Release：0 warning / 0 error；WebView2 Runtime `155.0.4283.62` 真初始化、渲染、截图、WebMessage 往返。
- 模型：75/75 manifest 文件、3,653,036,664 bytes SHA-256 全匹配。
- TTS：2.88 秒、24 kHz、RMS `0.0500386767`、WAV SHA-256 `30597bab8f2ac365bae3ac7c50d334532f6903dfa3e3da71d0d27e323508b661`；网络守卫 0 次非 loopback 尝试。
- ASR：保存 WAV、SenseVoice、本机 CPU，`ASR_DECODE_COMPLETED` 且转写非空。
- 工具链：SDK `8.0.425`、项目 Python `3.13.13`，包装器均 exit 0。
- 管线/vault：当前真实派发事件与既有审计回执通过；DPAPI 只读解密/list 通过且凭证正文未输出。

## §8 自核

- 第 1 次自核：发现 TTS 成功日志含 ModelScope 元数据请求 403，未将其计为离线 PASS。
- 第 1 次自修：阻断 wetext 可选前端导入，调用 `text_frontend=False`，并安装非 loopback socket 守卫。
- 第 2 次自核：TTS exit 0、非静音音频、`blockedNetworkAttempts=[]`；九项证据闭合。
- 结论：T1 PASS，可进入 T2；仍待主脑独立验收，不自批 W1。


## Root 独立修复复验（2026-10-21，非 W1 批准）

Owner 阶段门拆分已写 environment-spec §7.1；九项原始证据仍保留。

最终报告：`logs/host-shell-reviewfix-20261021T065131/final-report.md`。旧执行端 Gate 为该次历史自检结果，不覆盖本段限制。
