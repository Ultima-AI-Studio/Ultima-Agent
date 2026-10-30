# Runtime dispatch order

- wo-ultimaagent-20261030-0003--voice-profile（已冻结 2026-10-30 tag wo-ultimaagent-20261030-0003-frozen-20261030）
- wo-ultimaagent-20261030-0006--t4-clear（已完成并入 0003 冻结门）
- wo-ultimaagent-20261030-0004--input-channel（已冻结 tag wo-ultimaagent-20261030-0004-frozen-20261030）
- wo-ultimaagent-20261030-0005--cv3-jarvis-voice（已冻结 2026-10-30 tag wo-ultimaagent-20261030-0005-frozen-20261030；三派 PID 21828 收尾，T0-T4 全绿 906/0；首派 11764 网络失败留证、二派 26236 T4 收尾 OOM 留证）
- wo-ultimaagent-20261030-0007--pseudo-streaming（派发中，2026-10-30 登记；首派 26832 受阻 T0（基线漂移）→ 主脑裁定收敛 → 二派 7264 T4 硬件回放 OOM 留证 → 三派 17132 现场续跑 T0-T3 全绿、T4 物理耦合受阻留证（async-play 日志竞态 L26 登记）→ Owner 拍板：物理耦合布置 + 竞态修复并进冻结门 → 四派 39480 收尾中（run_dir 20261030T163548039147Z）；双线程伪流式：采集∥识别，1s 重跑节流 + 说完终跑 + 异常回退；源任务卡 voice-136-pseudo-streaming）
