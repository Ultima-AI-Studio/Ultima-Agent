# E01 round1单例执行提案（未分配）

范围：当前候选269aca5、当前qwen3-8b-uncensored；一次独立隔离文件任务，把版本化三条材料整理为summary.md。一次真实工作CLI，失败不重试；完成后一次只读独立结果复核，检查三事实和无新增事实、实际写入、服务与外部读回、清理及最终声明。

准备manifest：a19bbdb66b68eca4d2d5d8642dba781dccb1659341d38d1cb881deb0a925518a。必须先有匹配的独立准备PASS、本地commit/tag和用户本次具体分配，才能创建release。当前实际与结果复核额度均0，未签发authority。

使用现有Ollama服务，不启动/重启/下载/升级服务或模型。新启动的仅为本轮独立Agent服务器和CLI，工作目录在本证据根actual/e01-round1；输出在其outputs/<服务生成UUID>/summary.md，运行库在runtime。保护7身份、KWS/语音和产品默认配置保持。无测试窗口、不抢焦点、无需暂停鼠标键盘；不操作音频或真实记忆。

执行入口仅为pinned Python -B运行code/acceptance_entry.py --preflight及--run；不得直接调用旧controller.execute或旧通用harness。预检为只读，验证源码、依赖、8B摘要/版本、保护身份和监听owner后保存proof；root依据新的用户分配签发单case/单CLI authority，60秒proof及120秒authority保持。服务准备后提交前重新检查；CLI300/SDK1800/controller315保持。过期或任何失败保留原证据、清理本轮owned身份并停止，不自动重试、不刷新旧授权延长时限。

实际机械通过仍不计事实PASS；原始terminal保持待独审，结果复核与root登记另存。准备/本次单例均不授予E01三轮整体PASS、E02、T2出口或Owner通过。

需要新分配的依据：用户最近的明确运行授权仅为一次E03负例及一次结果复核，已消费完成；E01会实际调用8B处理文件任务，属于下一例。此前持续推进授权覆盖目前的离线准备。

准备独审已PASS，回执SHA 7793da71e425ace74f65a330e951f46c52bf261e4acef0dc32bba5192f9751ff。208离线检查及89文件封存通过；最近只读环境观察为2026-11-06T05:19:53.9262616Z，不代替下一次fresh proof。实际和结果复核仍未分配。
