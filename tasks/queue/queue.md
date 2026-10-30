# Runtime dispatch order

- wo-ultimaagent-20261030-0003--voice-profile（已冻结 2026-10-30 tag wo-ultimaagent-20261030-0003-frozen-20261030）
- wo-ultimaagent-20261030-0006--t4-clear（已完成并入 0003 冻结门）
- wo-ultimaagent-20261030-0004--input-channel（已冻结 tag wo-ultimaagent-20261030-0004-frozen-20261030）
- wo-ultimaagent-20261030-0005--cv3-jarvis-voice（已冻结 2026-10-30 tag wo-ultimaagent-20261030-0005-frozen-20261030；三派 PID 21828 收尾，T0-T4 全绿 906/0；首派 11764 网络失败留证、二派 26236 T4 收尾 OOM 留证）
- wo-ultimaagent-20261030-0007--pseudo-streaming（派发中，2026-10-30 登记；首派 PID 26832 受阻 T0 留证（三处基线漂移）→ 主脑裁定收敛基线（门控 0.01/0.002、score 2.0、BEEP 1.2）→ 二派 PID 7264 现场 T4 硬件回放 OOM 崩溃留证（run_dir 20261030T153434538976Z）→ 三派 PID 17132 现场续跑（run_dir 20261030T160210121426Z）；双线程伪流式：采集∥识别，1s 重跑节流 + 说完终跑 + 异常回退；源任务卡 voice-136-pseudo-streaming）
