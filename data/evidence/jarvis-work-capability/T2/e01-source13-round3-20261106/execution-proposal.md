# E01 round3单例执行提案（未分配）

范围：当前候选269aca5、当前qwen3-8b-uncensored的一次独立文件摘要交付；一次工作CLI、失败不重试；随后一次只读独立结果复核。E01目前2/3，本提案只推进第3轮。

准备manifest：492c9e293eb118c1ee7767e4f6d0983016ddbaa34267fc8327f48f083209ea87（69文件）。独立准备review PASS，SHA：8a7d52e95ac5366bd7c5464d5d4ed415bfcb9c8dfb444e5a7516738a80ce9343。306项离线检查通过；本地commit/tag精确读回后才请求新分配。目前实际和结果复核额度均0，没有release或authority。

固定材料：项目代号是松林；交付形式是Markdown文档；截止日期是2026年11月8日。由当前8B整理三条摘要，通过真实SDK文件工具写入本轮outputs/<服务生成新UUID>/summary.md。独审检查事实完整且无新增事实、实际写入与读回、最终路径声明、清理及保护证据，不用关键词命中代替事实审查。

只使用现有Ollama0.32.15和当前8B摘要6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。新进程仅为本轮隔离Agent服务器与CLI；不启动/重启生产服务、不下载升级模型。工作目录为本证据根actual/e01-round3，独立runtime/outputs。无窗口和音频操作，无需暂停键鼠；7保护身份及KWS/语音保持。

入口：pinned Python -B运行code/acceptance_entry.py --preflight及--run，不直接调用旧通用harness。预检只读检查候选源码/依赖、模型摘要/版本、保护身份及监听owner；root根据新的用户分配签发单case/单CLI authority。proof最多60秒、authority最多120秒；准备服务器后提交前再次校验，CLI300/SDK1800/controller315不变。过期或失败保留证据并停止，清理本轮owned身份，不刷新旧授权或自动重试。

机械通过的原始terminal仍保留待独审；独审与root登记另存。此提案不自动授予E01整体、E02、T2出口或Owner通过。新鲜运行环境由未来准入再核对；此前保存的时点证据不能代替。

需要新分配的依据：用户最近明确授权的是“一次E01 round2并独立复核”，该一例和一次复核均已完成。持续推进授权覆盖本轮离线准备；本提案中的round3会新增实际模型调用和一次结果复核。
