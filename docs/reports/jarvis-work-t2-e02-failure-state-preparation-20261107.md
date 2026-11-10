# E02 失败分支与选页诊断准备记录

原工单 wo-ultimaagent-20261101-0021 / T2。产品候选 22653fb77445bad4f5b9d9ae789cd35972dcc984，父候选 9e2716a6bc8dc1a51218257b89a581f968d8444a，tag ultimaagent-e02-failure-state-candidate-20261107。本阶段没有实际研究或模型调用；E02、T2仍未通过。

## 已实现与边界

产品新增 work_research_diagnostics.py；WorkService 在研究失败后追加一次可信摘要。原 ledger 的锁保护冻结，使用已验证的 secured envelope、实际 read START、staged views 和实际 transport 计数，区分 absent/action/unvalidated_response/final_before_write/write_without_ack/ack。失败后的 ack 分支仅表示已确认后发生其他拒绝，仍 complete=false、credit=0。

最终回复最多1000字符，私有包最多16384字节；只保存有限页坐标、七字段卡片的引用/种类/坐标投影、确认和可见状态、合格来源、原读取/POST计数及剩余时间。无原始消息历史、源码正文、网络实体、动态异常原文或密钥。所有私有内容先经过原 scanner 和严格封闭结构校验；public result 只含摘要、分支和计数。快照失败返回固定 UNAVAILABLE，不覆盖原错误。已冻结的快照不受晚到 ledger 变更影响。

验收导出器先保存 service-first-result，随后独占创建 trusted-failure-diagnostic.raw 及固定导出回执；原绑定、摘要和扫描再次校验。写入异常只产生有限失败回执，继续原 product error。诊断不可作为可信成功 packet、ACK、END 或验收信用。预算中的 write_admission_open 只表示剩余时间达到原55秒门槛，不是 sealed ledger 的可执行许可。

没有修改研究 writer/schema、事实检查、选页目录、模型阶段提示、SDK、原时限或调用配额。本次先获得证据，尚未实现任何猜测性的“读取到交付”改写。下一修复须使用本例证据并在另一冻结候选准备。

## 当前离线证据

verify_preparation.py 已对当前提交和保存快照读回 PASS，共965项唯一检查：产品631、harness275、绑定/入口/边界59。产品新增23项诊断测试，harness新增7项失败导出测试。harness五组原始计数79+140+19+32+7=277，扣除两个旧重复用例为275。原 HTTP/junction 两项排除明确保留，不计通过。全部选定JUnit无失败/错误/跳过，offline guard无违规，1562项输入绑定及9项无关工作文件保持，N9准备/结果证据和产品源字节保持。

RED和过程异常原位保留：最初10例为8FAIL/2PASS，扩展15例为12FAIL/3PASS；第一次实现9FAIL/6PASS暴露原canonical_v3不允许浮点值，改用与原运行协议一致的repr秒数字符串后15PASS；扩展并完成23PASS。无卡片测试使用真实空白首段来源，未修改不可变view。harness导出RED7FAIL后GREEN7PASS；最终提交重绑定后的五组均通过。所有这些运行均为离线MockTransport，无实际模型调用。

## 后续约束

计划独审 PASS_PLAN_ONLY。准备包封存后，由新的 root-independent reviewer 核对 exact manifest；只有 PASS_PREPARATION_ONLY 后才签发本根的一例诊断分配。该运行结束后第一结果封存并独立复核，再判断是否存在可证的最小衔接修复。最多另一新候选的一例补修后验证，不追加盲试。

保持当前社区8B、原题、原四来源、原预算和七保护身份。旧E01/E03在269aca5的通过不转移。本轮没有UI、音频、生产服务控制或模型下载。远端push此前被自动审批以blocked by policy拒绝，本轮不重试或换通道，仅本地提交/tag和文档镜像。


独立准备审查 PASS_PREPARATION_ONLY；准备 manifest SHA256 d90f3d2131ebf8ca35d9043d1e871751842448c1ff14fa0b980ab3168c467051，审查 SHA256 db487ea044129fb05b7f98ccd2c9d12e2b201be139a55a012754ad67a5556a49。封存成员 1058。新提交的只读七保护身份、原生版本和模型核对通过，实际入口未调用。
