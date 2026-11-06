# 同候选E01回归的只读准备发现

本记录不是E01执行授权。当前E03负例仍在独立结果复核；只有原三正例和本负例按独审结果正式登记后，才把E03作为E01入口前置。

固定候选269aca5的版本化acceptance-cases.json已包含E01请求：把三条材料整理为摘要，保存到本轮可信目录的summary.md；三事实为松林、Markdown文档、2026年11月8日，无新增事实。文件路径由服务可信output_root及新request UUID确定，不能由模型扩大写域。须实际工具写入、服务重新读回、外部进程重新读回及独立事实复核。

现有代码已经有E01服务器/CLI/机械核验支路；下一步适配既有独立入口，不新增Agent框架或产品默认值。E01无需原生双窗口或手动开始按钮，必须禁止fixture/current-window/replace-selection/research选项；仍按原保护身份、当前8B和源代码/依赖绑定准入。

不能直接启动旧work_context_acceptance.py通用harness：其旧CLI等待900秒不符合当前已固定的300/1800/315秒边界。应复用已审的入口控制和现有CLI支路，在隔离服务就绪后、提交前重验同一个60秒proof/120秒authority，保持失败不重试和完整清理。

原契约要求核心模型任务在同一候选连续三轮；因此当前候选E01应按round1、round2、round3分别保留新证据，旧候选E01成功不能替代。每轮仅当前qwen3-8b-uncensored、一个真实CLI、独立事实结果复核；不引入14B。

准备顺序：先绑定本次E03结果独审与登记；再形成E01 round1离线计划和入口，验证拒绝未合格前置/扩大写域/过期准入、保留真实文件读回与清理；封存、独立准备审查、本地检查点后，才提交具体的E01单例分配。当前未创建E01实际目录、authority或调用模型，也未放行E02/T2/T3—T5/Owner。

只读依据：冻结候选docs/plans/jarvis-work-capability-delivery-plan-20261101.md第96行；src/brain/tests/fixtures/work_capability/acceptance-cases.json；src/brain/tests/work_context_acceptance.py及已封存controller.py现有E01支路。
