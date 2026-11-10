# E02 输出预算对齐候选受控入口准备

状态：待独立准备审查。

原单wo-ultimaagent-20261101-0021/T2；产品候选0421a54cab572be013c3f7ad562e86406bfe8e52。本轮承接用户call_4d19727901d9426786cc1f5fd01a3b64授权和同一精确计划Task2。N20的产品离线927及独审PASS已冻结，N21不改产品。实际用例、模型调用与结果复核分配均0；E02仍0/3，旧E01/E03信用不迁移，T2/Owner未通过。

复用N19的entry/bindings/adapter，全部函数与类AST一致，仅重绑路径、候选及摘要。完整源码76项，由N19完整75映射与N20完整76集合并生成，不退化为顶层源码子集；每项与冻结输入一致。输入1594项；check_inputs含额外三项入口绑定共1597项。原题四来源、corpus、模型摘要、预算、七保护基线与previous_plumbing不变。

当前共享阶段提示写明请求真实num_predict，并要求紧凑JSON、简短标题及精确原子事实，完整原题信息和引用仍须保留。原生format/schema、预算、来源覆盖、事实门、ACK不变；新产品是否改善当前8B真实交付尚无新实际证据。

五组harness+三组标准库得到346项新鲜去重通过：harness raw287、unique285；bindings16/entry34/boundary11。原90秒/最多2并行，源码快照/审计/JUnit一致；N20的927不重复计入本轮346。Python操作审计不等于系统抓包。

初次入口组为33通过/1错误：准备授权记录缺少旧direct-message接口的decision_id，触发KeyError。原entry-final错误、源码快照和旧运行观察均保留；补齐由原答复内容摘要生成的内部decision_id并明确非平台消息ID，原question_id/答复/授权范围及零额度不变，仅重绑entry常量摘要。原核心函数AST不变；重新运行受影响entry34（entry-review-green）并保存当前只读环境观察，其余七组输入字节未变，不重跑或重复计数。零额度准备消息不能升级为实跑授权的原负例现已通过。

N19现有v4观察器six_reads/ack_after_write联合检查保持：6次读取后第7POST length2048必须failed/未交付/无文件；写后第5POST length256必须needs_attention、保留已写入效果并未ACK。导出原字节、请求/响应SHA、generation/receipt_index、公开摘要、complete=false/END=false/credit0完整核对。原quoted_write/escaped_boundary/HTTP500等负例保留。未供应任何真实模型回答，未新增真实调用。

只读运行核对点2026-11-07T15:19:56.406092+00:00确认Ollama0.32.15、当前8B摘要、七保护身份和18799空闲；只代表该点。冻结候选HEAD/tag/clean、N20封存/输入、N19准备159/结果56/actualseal31及更早失败链、15项无关工作文件保全。

上一N19唯一实际72d7d71b-39a9-455a-b0b4-8823b3f24c00仍为FAIL_CONFIRMED：第7次原生响应done_reason=length、eval_count=max_tokens=2048，无research.md。完整响应正文未保存，不能推断具体内容耗费；本例必须由新单例真实回执检验，离线准备不授予验收信用。

仅qwen3-8b-uncensored；CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315、context16384/messages+strict32768/entity49152、阶段256/2048预算保持。原单例1/结果独审1/retry0和TTL<=120秒grant门不变。

无actual/release/controller-authority/native-preflight/controller-ledger。PASS后才能生成准备harness-approval、read_ready并验证无grant的read_release拒绝，run_once不调用。执行提案提供完整原题、四来源与唯一入口；须用户另行明确分配单例，才可调用模型。成功须文件、可信runtime、写入读回、ACK、事实/引用/原题覆盖、原时限、清理和结果独审均过。

closeout.py在封存前已统一通用准备指针、测试数、下一步与标签，保留last_actual及旧字段历史；当前登记尚处准备中，准备PASS和本地发布由后续独立回执确认。计划与报告使用LF，镜像字节一致；本地commit/tag及最终读回随后记录。此前远端push自动审批blocked by policy，本轮不重试或换通道。
