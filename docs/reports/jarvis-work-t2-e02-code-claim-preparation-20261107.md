# E02代码事实契约对齐准备

原工单wo-ultimaagent-20261101-0021 / T2。用户call_99e734b15417466b92af3e8e85fdc3ea已授权补修、必要独审、PASS后一例当前8B原题四来源研究和一次结果复核；失败不重试。候选1ecd75d061fd20e78c790c506cac76847f8e63bf，基于冻结a0d21eb，隔离工作区C:/Users/Administrator/.codex/worktrees/jarvis-e02-code-claim/UltimaAgent。

先完成contract-inventory.md：结构和可信卡片、文字规则、来源去重、AST/词法证据、END/ACK/SHA/两次读回、语义事实复核分别列明。实现只触及三个产品文件及一个新测试文件：新增v3_phase_writer_schema从已确认可见卡片派生operation约束；生成和独立runtime重放均调用它。卡片按同源同operation分组，evidence_id枚举保留；代码claim使用受支持的锚点、字符类、分组与分支表达原精确边界，operation按原格式/200字符规则拒绝非法值。非code原规则保留，无生成后补字或响应改写，无新增模型轮次。

28项新产品测试包括原schema接受/原writer拒绝的RED、同源其他operation/近似名称/前后边界/无效operation、空页、完整SDK mock第三pending页、format/strict/sampler/phase一致、文件/ACK/SHA、修复全部自报hash和native entity后的重放拒绝，以及原writer仍拒绝被篡改事实。初始RED26失败1通过（既有phase拒绝）；第一次两个缺失pattern以StopIteration暴露，第二次改为明确断言。所有记录保留。

另3项离线转换检查使用官方llama.cpp b10488参考转换器；Ollama v0.32.15源码固定此标签。抓取字节经Git blob hash核验，保留MIT许可证；最初主机DNS失败所留空文件未执行。Python格式器会拆分相邻字符串字面量，初次两条格式断言失败，修正仅相邻字面量表示检查后3项通过。最大6页48卡/5来源完整保留；48个不同200字符操作名的完整契约会越过原32768字节门，应拒绝，不扩大原49152实体上限。已保存官方转换GBNF与体积记录；这不等于已验证本机原生采样行为。

最终产品与参考转换检查597项，原执行框架238项、绑定16、入口26、边界11，总计888项，以封存readback为准。原本地HTTP服务/junction两个离线排除项不计通过；无OS抓包断言。原事实、源去重、writer、END、ACK、外部读回、时间和次数门不变。来源63份，绑定输入1559份。

保护基线直接复用N7已审查的七身份：H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source-reference-schema-20261107-r1\inputs\protected-baseline.json，SHA1b7e945e9ce52e44b8b384fc5e3911b77b7da4d80beeba615f341bf3e923fce5。本轮准备只读核对七个native/CIM/parent/command身份一致，不重新定义基线、不推断连续存活。原Ollama启动来源未知的结论保留；无UI、音频或服务操作。实际前仍执行原新鲜身份核验。

旧候选/旧失败全保留；旧269aca5 E01/E03信用不转移。当前E02/T2/Owner NOT_PASSED，尚未签发单例authority。远端push受此前自动审批blocked by policy阻断，不重试或绕行。

审查重点：可信可见卡片、code证据与operation一一绑定、边界表达等价、非code不改、独立重放、原预算与事实门；同时核对保留未编码的正文/语义条件和未验证原生采样的明确限制。

## 独立准备审查结果

PASS_PREPARATION_ONLY；manifest b3ed0d8550943db83a0044f291e7990885959618865ea25adcfde16229858f28（832成员），review SHA256 2ea1e8a39e497e59d8af26cb63817d2a478d72cfa176706bf60c2ac64d869df9。888项离线检查、1559绑定输入与63来源读回；实际入口尚未调用，按既有完整授权继续一例。
