# 任务卡：s2-combo-window

- **task_id**：s2-combo-window
- **标题**：组合窗口接入交付（#88，L4 编排 + L6 输出呈现）
- **优先级**：85（P0）
- **reasoningEffort**：medium
- **category**：ui　**skill**：ui
- **依赖**：无（独立于悬浮球原生窗口）
- **登记核验**：已查注册表，无重复组件；对齐能力清单 L4/L6 缺口与 #88 待办

## goal（做什么 / 禁止做什么）

**做什么**：把 14B 的回答以"组合窗口"形态交付——语音播报与组合窗口同时呈现（对齐 product-plan v2.3 §6 L4/L6）：

1. 复用既有 A2UI 组合窗口载体（`docs/reports/l4-a2-orb-live-acceptance-20261025.md` 记录的 WebView2 上壳 / 组合窗口项目），把 `agent_server` 的 `/ask` 回答（文本 + 工具结果）渲染进组合窗口：文本区 + 工具结果区（如任务列表、环境快照、检索来源）；
2. 组件树按 A2UI 声明式 DSL 组织，尺寸自适应内容（对齐 UI 积木规格，窗口不写死，由内容排版算出）；
3. 语音 daemon 播报与组合窗口更新同源（同一份 agent_server 回答，先播报再上屏或同时）；
4. 异常态：agent_server 不可达时窗口显示降级提示，不空白不报错。

**禁止**：
- 禁止改动悬浮球 Win32 原生窗口（orb-native 已收口 #84-86）；
- 禁止改动语音 daemon 唤醒词 / ASR / TTS 链路；
- 禁止引入付费/闭源组件；
- 禁止向 fileDomain 之外写文件。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT-1：组合窗口真实显示 14B 回答文本（纯对话场景）
- [ ] ACCEPT-2：工具调用场景——问"查一下任务状态"，窗口显示回答 + 任务状态结果区
- [ ] ACCEPT-3：环境快照场景——问"电脑什么配置"，窗口显示回答 + 硬件/磁盘结果
- [ ] ACCEPT-4：窗口尺寸随内容自适应，无滚动溢出/裁切
- [ ] ACCEPT-5：语音播报与窗口内容一致（同一来源，时间差 < 3 秒）
- [ ] ACCEPT-6：agent_server 停掉后问话，窗口显示降级提示且不崩溃
- [ ] ACCEPT-7：组件树按声明式 DSL 组织（源码可读，非硬编码布局）
- [ ] ACCEPT-8：回执完整——receipt 含 reviewReason / stdoutText / evidence / acceptance

## fileDomain[]

- `H:/UltimaAI/UltimaAgent`（含组合窗口载体所在子目录）

## receipt（完成时回执）

- reviewReason / stdoutText / evidence / acceptance 逐项核对

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-24 | 初版：#88 组合窗口接入交付 |
