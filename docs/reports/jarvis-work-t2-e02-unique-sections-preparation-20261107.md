# E02 唯一来源章节与诊断计时准备记录

产品候选2b42b3e19516154a26cbc895a3d9e69fabb07ab2，父候选22653fb77445bad4f5b9d9ae789cd35972dcc984；tag ultimaagent-e02-unique-sections-candidate-20261107。准备阶段无实际研究、模型推理、UI、音频或服务操作。当前E02/T2未通过。

## 依据与改动

N10诊断已确认六页读取、action分支和一次写入失败，原因码INVALID_SOURCE_SECTION，尚有约229秒；原始写入参数未保存，不能指出具体重复来源，也不能最终排除unknown分支。冻结源码确实存在phase允许重复来源而writer拒绝的契约不一致。该证据支持最小修复，不保证修复后的实跑或语义验收会通过。

1. v3_phase_writer_schema列出所有可见3至5来源子集，按source_id排序的定长tuple使每来源只出现一次；本地definitions共享每来源卡片，避免重复展开。来源、证据ID、operation正则、原事实数及长度限制保留；同来源多页可在一章内引用。
2. 生成和独立重放共用小型纯envelope helper，将本地definitions放在完整schema根，保持JSONPointer一致。研究提示仅说明一来源一章/同源多页放同章，不带题目答案或选页指令。重放先比较可信重建schema，再验证实例，拒绝在比较前解析篡改后的引用。
3. 回归发现诊断缺失后，固定259.1234567秒离线复现了时间字符串被PII手机号规则命中的问题。独审补充通过后，诊断kind升v2，改为有界整数微秒，使用精确分数向下取整；损失小于1微秒仅用于显示。原55秒准入、monotonic及所有运行时限不变，scanner和文本扫描保持。旧v1候选及证据不变。原随机失败具体小数没有保存，不作确定追溯归因。

resolve_v3/render_v3、_fact_evidence、通用v3_writer_schema、选页build_page、文件事务及调用预算保持。没有写后合并或改写模型稿件；不足依据仍允许明确拒绝。现有来源/代码契约测试适配共享定义的读取位置，仍执行原语义/篡改断言。重复章节在前置schema已被拒绝，原writer诊断测试因而与既有foreign/unissued测试一样改为resolver边界注入，保留writer独立拒绝及诊断断言；正常入口的提前拒绝由新增SDK负例覆盖。

## 当前验证

当前字节读回PASS_OFFLINE_UNIQUE_SOURCE_SECTIONS_PREPARATION_ONLY：998项唯一检查，产品664、harness275、接口59。新增来源章节21项，诊断扩展至31项；官方参考转换扩展为7项。harness五组原始277项扣除两个旧重复用例为275。原HTTP/junction两项排除保留，不计通过。源快照、JUnit、offline guard、1563输入及9项无关文件已核对；旧N10准备/结果和产品源码保持。

过程失败原位保存：来源约束初始10FAIL/10PASS到20PASS；新引用顺序负例1FAIL/20PASS后修正；完整回归中诊断22PASS/1FAIL；确定性计时RED1FAIL随后GREEN。一次旧writer诊断用例因重复章节已提前拒绝而失败，按上述边界注入调整后重验。最终采用当前字节的最新完整成功回执，不累计历史重复运行，也不把旧候选通过迁移到本候选。

本地官方参考转换器支持tuple及本地引用，转换allow_fetch=false；完整envelope3/4/5来源通过离线转换和原字节门，最大48卡片/长operation仍被原字节门拒绝。还从原语料重建了诊断所选六页，核对页卡数量及schema/phase/页面观察的体积；该尺寸记录明确不包含继承SDK系统提示及动作历史，不能冒充最终实际请求大小或本机二进制验证。真实入口仍独立执行原上下文和字节限制。

## 下一门

来源章节计划独审及诊断计时补充独审均PASS_PLAN_ONLY。封存当前manifest后须新的独立准备审查PASS_PREPARATION_ONLY，随后本地提交/tag/UltimaDocs读回及只读运行核对，再使用最新授权中剩余的一例补修后验证并独立复核。当前根尚未分配或调用实际例。只有文稿、逐事实及原题覆盖、可信packet/ACK、时限、清理和独审同时通过才可计新候选1/3；E02/T2不提前通过。

仅当前社区8B；原题四来源、七保护身份及预算不变。远端同步仍未完成：此前自动审批blocked by policy，本轮没有重试。


独立准备审查 PASS_PREPARATION_ONLY；准备 manifest SHA256 9f41184d3bc1399ac27c641a47ebf4f46094c80294a05d06434514e014f83d9f，审查 SHA256 707c115349379af46f889f6fe56931030f6525c3e08f48cf2916bc5ff5c48f48。封存成员 2501。新提交的只读七保护身份、原生版本和模型核对通过，实际入口未调用。
