# E02 原生响应解析兼容性后续工作

本文件记录下一工程步骤，不分配新模型调用、现场用例或服务操作。当前“诊断一次、按证据补修后验证一次”序列已执行完；本例结果待独立复核时形成此提案，正式状态以结果复核和结果报告为准。

## 已知事实与未知项

候选2b42b3e19516154a26cbc895a3d9e69fabb07ab2，单例be79869f-10e5-4c0d-96a9-144cd5967c12，119.564034秒后失败，product error为Research HTTP status。六页已confirmed，其中五页visible，S3最后一页尚未获得validated response后的visible确认；搜索1、GET4、应用POST7、已完成POST6。诊断剩余167775139微秒，原55秒准入仍开放；没有write、ACK或research.md。

原生服务既有日志的同时间段记录六次/api/chat为200，第七次为500；最后一代生成2048 tokens后出现unparsed peg-native output。截取中五个证据ID与本例匹配，与前例不匹配。日志已经只读截取并单独封存；它是时间和内容相关的补充证据，不是产品导出的请求绑定transport receipt。局部未解析内容不能用来拼接文稿、接受事实或补造成功回执。

现有事实支持把下一排查位置缩小到当前社区8B的原生结构化输出与响应解析接缝。尚不能确定是模板、原生解析器、具体schema构造还是组合行为造成；2048是本轮生成记录及既定输出上限，不证明增加上限就能解决。离线参考grammar转换成功，也不等于本机原生实现已验证。本轮未实际到达writer，来源唯一性补修仍只有离线验证证据。

## 按顺序推进

1. 先核对现有本地原生接口/模板与保留的请求构造代码。产品当前已经设置think=false、stream=false、temperature=0；不得把再次设置同值当成修复。按实际版本和路径区分参考转换器、本机原生执行和响应解析，不凭包名推断同一实现。
2. 补齐最小HTTP失败归因：从可信transport receipt保留generation、route种类、HTTP整数状态、已发送请求摘要及有界计数。状态来自实际HTTP返回，不从模型文本提取；正文只有经大小和扫描约束且确有必要才保存。原错误与失败终态保留，诊断不得生成ACK或验收信用。先用离线500/坏JSON/超限/扫描失败fixture验证，无模型调用。
3. 对源码或保留证据支持的接口差异再形成最小兼容方案，并在后继隔离候选验证。优先保持原官方接口和完整严格校验；若需调整采样格式投影，生成与重放必须一致，原来源唯一性、证据配对、operation及事实门继续执行。不能通过删除约束、截断内容、把不完整JSON补齐或代写答案来“交付”。
4. 独立准备审查通过并明确分配新的单例范围后，再考虑一次原题四来源的当前8B实测。当前文件不授权这次运行。事实、引用、任务覆盖、写入读回、ACK、时间与清理仍须分别验收。

## 保持的边界

只用当前qwen3-8b-uncensored及既有摘要，永不转14B。原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒、context16384、messages+schema32768/entity49152字节及retry0保持。当前候选与本轮结果冻结；后继修改使用新隔离候选。语音、主脑及Ollama生产服务保持，七保护身份继续核对。没有原题覆盖和合格文稿时E02/T2不通过，旧E01/E03信用不迁移。

证据入口：data/evidence/jarvis-work-capability/T2/e02-unique-sections-20261107-r1/review/result-inputs/result-manifest.json（SHA256 c00e597832d5b739043b75ee051ee46265a3d5c9b7c43505fa05e7722bd31bfd）及review/native-log-supplement/manifest.json（SHA256 9e542f61da51f16a4d5625650e2d2fa38a5c4d597cec4859612cf051e6295db0）。
