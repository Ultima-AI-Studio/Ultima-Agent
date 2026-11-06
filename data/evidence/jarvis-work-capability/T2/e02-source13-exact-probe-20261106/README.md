# 精确 urllib3 IPv6 探测候选

原单0021/T2，当前8B、产品候选269aca5与语音/生产服务保持。此目录为新隔离验证候选，继承已验证的SDK生产端JSON键序修正与审计证据记录；不改外部诊断包或历史运行。

唯一网络例外为固定urllib3.util.connection模块初始化调用_has_ipv6("::1")，源码SHA2633bbdb69731e5ccb5cf4e4afd65605d86c7979cc5633126f50c92d5ad74a74。校验实际模块函数code、调用帧和正在初始化状态；仅AF_INET6/SOCK_STREAM/protocol0的一个socket、同一个对象的精确位置参数绑定("::1",0)，并在关闭门核验已关闭。其他模块、运行期调用、额外参数、其他类型/协议/地址/端口、重复创建/绑定、connect/send/listen仍拒绝。原gethostname本机元数据与限定SSRF getaddrinfo规则保持。

新增18项精确规则/真实导入验证。原566项profile测试身份保留，其中两条旧宽泛例外测试的夹具按新约束调整；根入口仍为原89项。真实urllib3测试只运行本机能力探测，观察关闭前后状态；没有调用原profile/研究/模型/UI/音频/服务。旧RED与全部失败保留。

外部包的run c794f6fd虽有机械PASS、SDK写入及独立reader两次读回，但其准备审查为执行者自审、外层清单有8项漂移；新的独立交接审查结论NEEDS_FIXES/DIAGNOSTIC_ONLY。此候选不追认旧独立门，不以零推理替代真实8B研究或T2出口。

本准备包manifest只列稳定输入/源码/检查证据；后续review、root gate、release和结果以单独记录绑定，不重写准备manifest。无release/runs表示尚未分配实际用例。
