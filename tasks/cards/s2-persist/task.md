# 任务卡：s2-persist

- **task_id**：s2-persist
- **标题**：智能体服务器常驻（开机自启 + 看门狗）
- **优先级**：80（P1）
- **reasoningEffort**：low
- **category**：host　**skill**：infra
- **依赖**：无
- **登记核验**：已查注册表，无重复组件；对齐 #87 遗留事项③（重启后需手动拉起）

## goal（做什么 / 禁止做什么）

**做什么**：解决"重启电脑后 agent_server 需手动拉起"问题，实现常驻：

1. 复用并验证 `scripts/start-agent-server.ps1`（已可用，tools=5）；
2. 注册开机自启：用 Windows 计划任务（schtasks，登录时运行，Hidden 不弹窗）或启动文件夹方式，开机后自动拉起 agent_server；
3. 看门狗：一个轻量进程（或计划任务周期触发），检测 8756 端口无监听时自动调用启动脚本拉起；连续拉起失败 3 次停止并留日志（防死循环）；
4. 全程零弹窗（对齐 codex-task-queue-spec §5 零弹窗纪律：任何窗口闪一下都不行）；
5. 日志留痕：自启/看门狗每次动作写 `data/logs/`。

**禁止**：
- 禁止改动语音 daemon / 悬浮球进程管理；
- 禁止安装第三方服务/守护软件；
- 禁止修改系统级配置（注册表/服务）之外的任何系统设置；
- 禁止向 fileDomain 之外写文件。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT-1：计划任务或启动项已注册，配置为登录时运行、Hidden、无弹窗
- [ ] ACCEPT-2：手动停掉 agent_server 后，看门狗在 60 秒内自动拉起，health 恢复 ok
- [ ] ACCEPT-3：连续拉起失败 3 次后看门狗停止重试并留日志（不无限循环）
- [ ] ACCEPT-4：注册后重启电脑模拟验证（或等效验证：注销/登录后 agent_server 自动可用）——若无法真机重启，提供已执行的等效验证证据并如实标注
- [ ] ACCEPT-5：全流程运行期窗口枚举计数 0（无任何窗口闪现）
- [ ] ACCEPT-6：日志完整（自启/拉起/失败记录）
- [ ] ACCEPT-7：回执完整——receipt 含 reviewReason / stdoutText / evidence / acceptance

## fileDomain[]

- `H:/UltimaAI/UltimaAgent`（scripts / src / data）

## receipt（完成时回执）

- reviewReason / stdoutText / evidence / acceptance 逐项核对

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-24 | 初版：服务器常驻（#87 遗留③） |
