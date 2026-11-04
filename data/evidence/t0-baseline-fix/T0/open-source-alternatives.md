# G-OPEN-001｜SoXR 环境依赖开源替代排查

本表在修改依赖环境前完成。结论是：本单不新增产品依赖，也不替换重采样实现；`src/voice-next/requirements-live.lock.txt` 已固定 `soxr==1.1.0`，`tools/venv-voice-next` 已安装同版。红灯来自完整工程门指定的 `tools/venv-openjarvis` 未同步这项既有测试运行依赖。

| 方案 | 开源许可证 | 流式状态 | 当前环境 | 结论 |
|---|---|---|---|---|
| `python-soxr==1.1.0` | LGPL-2.1-or-later | 原生 `ResampleStream`，与现有 `live.py` API 完全一致 | voice-next 锁文件与隔离 venv 已采用；openjarvis venv 缺失 | 采用既有锁定版本，只修测试环境漂移，不改产品实现 |
| `scipy.signal.resample_poly` | BSD-3-Clause | 需自行维护跨块滤波状态或改成整段处理 | openjarvis venv 未安装 SciPy | 不采用；新增重量依赖且会改变实时跨块语义 |
| `resampy` | ISC | 主要面向整段数组，现有接口不兼容 `ResampleStream` | 未安装 | 不采用；需要重写实时状态管理，扩大本单范围 |
| 测试 fake/mock | 项目内测试代码 | 可伪造构造器，但不执行真实 native stream | 无需安装 | 不采用；无法真实证明断流后建立新 resampler，违反验收口径 |

官方来源：

- python-soxr 项目、流式 API 与许可证：https://github.com/dofuuz/python-soxr
- SciPy 项目与 BSD-3-Clause：https://github.com/scipy/scipy
- resampy 项目与 ISC：https://github.com/bmcfee/resampy

