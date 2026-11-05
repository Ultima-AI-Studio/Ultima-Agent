# 一次只读独立准备审查请求

范围：本包e03-round2-acceptance-package，全包manifest精确哈希及候选269aca511d88412dbb9c15d23911138469a37aa2。按controller-offline-release.json及原工作能力契约技术门执行，不是实际结果审查，也不是实际用例授权。

请按requesting-code-review模板审查已完成范围，先核对manifest、parent-manifest、entry.diff及progress.md的Ruling。原产品候选无变化；新增入口只做第二轮作用域、前轮独立PASS绑定，guard仅改运行manifest位置。检查实际调用图而不只看常量。

重点：
1. round1原terminal/review/registration及来源副本一致；同候选、正确轮次、机械/事实/窗口/文件/完成声明与哈希链必须同时成立，不能把原始PENDING改写为PASS或把旧候选通过计入。
2. round2本包独审、新authority、fresh proof、prior_reviews、一次消费和结果待独立事实门有效；旧round1 authority、缺失或错绑前轮应在native backend之前被拒绝。
3. 15/20/60/120秒和300/1800/315秒时限、一次CLI、七保护身份、两窗口、固定选区和原文、手动开始、持续提示及清理均保持。非活动历史入口没有获得新格式authority。
4. 阅读全部153项测试的相关断言、RED20/3与GREEN23、最终XML和guard回执。130项原功能/参数数量保持，但两份轮次相关测试材料有明确调整；不声称原测试文件全字节相同。
5. 核对候选57源码、7依赖、1346SDK及运行manifest；既有485/8回执未重跑，独立判断复用的局限。检查本包未含release或actual。

只许本地只读文件、SHA、JSON/XML、AST、git show/diff/HEAD读取。禁止运行被审代码、导入产品或native模块、测试、UI、键鼠、现场进程/服务查询、网络、模型、音频、写入、Git变更和再派子代理。不要尝试之前被拦的import probe或push。

返回完整JSON：reviewer=root-independent，scope=e03-round2-acceptance-package，manifest_sha256、candidate、verdict(PASS/NEEDS_FIXES)、strengths、findings(Critical/Important/Minor)、独立核对计数、逐项declined_to_judge及limits。PASS只表示本包准备满足原门，不授予用例、T2、Owner或整个目标完成。
