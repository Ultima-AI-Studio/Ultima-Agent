# Runtime dispatch order

- wo-ultimaagent-20261030-0003--voice-profile（已冻结 2026-10-30 tag wo-ultimaagent-20261030-0003-frozen-20261030）
- wo-ultimaagent-20261030-0006--t4-clear（已完成并入 0003 冻结门）
- wo-ultimaagent-20261030-0004--input-channel（已冻结 tag wo-ultimaagent-20261030-0004-frozen-20261030）
- wo-ultimaagent-20261030-0005--cv3-jarvis-voice（已冻结 2026-10-30 tag wo-ultimaagent-20261030-0005-frozen-20261030；三派 PID 21828 收尾，T0-T4 全绿 906/0；首派 11764 网络失败留证、二派 26236 T4 收尾 OOM 留证）
- wo-ultimaagent-20261030-0007--pseudo-streaming（派发中，2026-10-30 登记；首派 26832 受阻 T0 → 主脑裁定收敛 → 二派 7264 T4 硬件回放 OOM 留证 → 三派 17132 T0-T3 全绿、T4 物理耦合受阻留证（async-play 竞态 L26）→ Owner 拍板物理耦合+竞态修复进冻结门 → 四派 39480：A 竞态修复完成（_LOG_LOCK）、C 记录更新完成，T4 耦合标定 0 命中受阻——**主脑复核纠偏：根因为运行 daemon 23588 MME 采集退化（16:36 起环境电平恒 0 + CPU 满载，L25 同型），非物理距离** → 五派 5xxxx 修复重测中；源任务卡 voice-136-pseudo-streaming）
