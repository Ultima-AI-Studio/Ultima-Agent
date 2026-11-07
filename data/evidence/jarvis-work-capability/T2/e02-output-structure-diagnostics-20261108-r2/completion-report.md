# E02 输出结构诊断离线准备

原单 wo-ultimaagent-20261101-0021 / T2；候选 `bf7f7a9cf0e4ba559c29daa388c00379d12d345a`，父 `47ac3a464ca15e01311d5739eda53b2a32d8783c`，原基线 `0421a54cab572be013c3f7ad562e86406bfe8e52`。本包仅补充失败诊断，E02/T2/Owner 均未通过，真实研究与结果复核额度为0。

已确认的缺口：原两例第7次HTTP200响应均因length被拒绝，eval_count=max_tokens=2048；旧包没有正文，不能据此认定JSON必定截断或定位到某个字段。既有程序已负责将事实结构绑定来源、生成Markdown并完成单次写入/读回/ACK；本轮没有更换这条交付链。

新增闭合v5保留同请求的实际flags/options、strict/sampler摘要、来源/引用数量；message字段与content/thinking类型/长度/SHA；完整content的严格JSON状态、受限错误位置及完整JSON的schema/结构统计。thinking和未知字段值不留正文。安全扫描后优先FULL，最终编码超出16KiB时保留带偏移的头尾/错误附近片段；不能容纳或诊断异常则保留原v4。原请求、schema、工具权限、length拒绝、写入/ACK和公共未交付回复保持。

离线结果：979项去重检查通过，其中975项产品检查、4项保存包/原导出器兼容；20组同源码字节，0失败/错误/跳过。仅沿用原delivery两项不适用排除。r1的27项初始RED、6项补充RED及NEEDS_FIXES均保留；本r2对PREP-STATE-01新增9项状态关联负例及1项解析器失败注入正例。首跑10项失败中9项确证校验缺口；另1项是测试错误假定1500层JSON必触发解析递归异常，实际能解析，已改为确定性失败注入。51项结构检查覆盖完整/残缺JSON、严格解析、类型混淆、实际raw_bytes绑定、片段编码膨胀、错误位置、原v4回退、畸形Unicode及16384恰好/超一字节边界；合成片段/大小及故障注入不是实际模型输出。

测试样例纠正：最初以JSON属性形式写的password未命中原开源扫描器的assignment规则。核对原规则后将样例改为它确实支持的password赋值表达式；扫描器和准入策略不改，不宣称新增了任意密钥识别能力。原131项native检查用途均保留，仅升级v5版本断言和legacy去扩展构造。旧failure共享helper没有修改。

保全：N19/N21实际失败清单、封存索引及准备包逐文件复验；1567项原依赖/输入摘要、15个无关改动保持。父候选仍冻结。前后核对点7个保护进程的PID/创建时间/路径均一致；没有测量连续存活或运行性能。

本轮actual/model/UI/audio/service操作均为0。当前8B、原题四来源、完整事实/引用/覆盖/文件要求，以及原调用、输出、时间和字节预算保持。旧E01/E03不计入新候选。独立准备审查已对本包给出PASS_PREPARATION_ONLY，下一步准备新入口；新真实研究仍需用户明确分配。旧push自动审批阻断保持，本轮不重试远端。

独立审查：H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-output-structure-diagnostics-20261108-r2\review\independent-preparation-review.json；manifest SHA256 79bc2c8e640af1a5e9e420234897f5f9f26984b7b611eabaac08fed539facb17；review SHA256 101a9b58f2832a2353a038fd75999198ecc835d3187c3fe5c1b2cb3b13602e28。本地提交/镜像状态由 publication-readback.json 单独证明。
