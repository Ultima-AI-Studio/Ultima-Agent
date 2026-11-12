# 完成语

- report version: `S1/v0.4`
- work order: `wo-s1-composite-window`
- task: `s1-window-composite-render`
- phase: `T2-text-core-only`
- status: `READY_FOR_REVIEW`
- completion: `partial — CR-01 转换核心 + CR-02 静态离线渲染核心`
- completed at: `2026-10-24T08:59:24+08:00`
- evidence: `evidence/20261024T085613+0800/`

本阶段仍只完成两个可独立验证的离线核心：有界 JSON 基本类型/文字结果被通用、
数据驱动地转换为真实 A2UI v0.8 扁平组件批次，并经已接受的 T1 最终校验；同一
批次在再次通过 T1 最终校验后，被限制为 `Text/Row/Column/List/Card` 的
literal/explicit 静态子集并生成安全 HTML。新模块直接导入，不修改受保护的
`src/window/__init__.py` 或全局组件目录，也未把 renderer 标为 active。

首轮独立复审 `audit-1` 的结论保持为 `REVISE`，未被本开发回执改写。本轮六项
针对性回归先真实 RED，再以最小修复 GREEN：整数大小判断不再泄漏 Python
`ValueError`；转换与 renderer 改用显式栈，在配置允许的 1050 层输入上不泄漏
`RecursionError`；空 `styles` 与非法 Unicode 标量显式拒绝。完整窗口套件
61/61 通过，其中原 T1 测试 35 项、新转换/渲染/安全/端到端测试 26 项；T1 原
91 案例重放为 91/91，输入变化 0。冻结 guardrail 确认 v0.3 10 项、v0.1 36 项、
生产 `tasks.json`、vendor pin 与旧 exit125/无 final 保持。

现有 Brain 的生产空队列文字入口被真实只读调用，结果经过转换、T1 校验、渲染
和 HTML 解析闭环；未创建产品任务，也没有把工程工单当作产品任务。未启动 GUI、
WebView2 或原生宿主，未播放/合成/录音/调用麦克风，未发网络请求或公开 RPC，
未修改 Owner 批准、tag、发布、冻结宿主、brain、queue_engine、shared 或 sync。

本文件只是第二开发轮 `READY_FOR_REVIEW`，不是独立 PASS，也不是完整 CR-01/CR-02、
整张 T2、工单⑤或 v0.4 完成声明。剩余门：
CR-01 完整域；CR-02 原生窗口挂接；CR-03 任务域 ≥90% 截图；CR-04 窗口+语音
双通道真机；T3 主题/悬浮球与语音四 IO；W5；Owner 审批与 v0.4 冻结。
