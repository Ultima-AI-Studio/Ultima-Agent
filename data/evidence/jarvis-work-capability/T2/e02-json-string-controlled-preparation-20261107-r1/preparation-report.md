# E02 JSON 字符串候选受控入口：待独立准备审查

原单 wo-ultimaagent-20261101-0021/T2；冻结产品 6d758d9c3961f156a062e349ec4a949e2ee7a9a9。本轮只将新候选接入既有受控入口，actual/model/result-review 分配均为0，E02仍0/3，T2/Owner未通过。

entry、bindings、adapter的全部函数/类AST与N15相同，只重绑路径、候选和摘要。完整源码74项由旧73项映射与N16顶层37项并集产生，逐项匹配N16 current-inputs及磁盘。输入1579项，check_inputs含三项入口绑定共1582项。题目、四来源、当前8B、原预算、保护身份和previous_plumbing保持。

两项新增检查均先安装adapter.install_trusted_exports，然后调用真实SDK MockTransport。quoted_write使用测试源码实际含有的中文/引号/反斜杠代码事实，经sampler、原strict、工具写入/哈希读回/ACK，读取导出的trusted-runtime.raw并严格重放；核对strict与sampler不同及实际HTTP实体和每项哈希。escaped_boundary原始字符串语法可接纳Unicode转义，但解码后操作名边界非法，原strict拒绝；无research.md、完整runtime或END，公开明确未交付，私有失败包与真实构造请求摘要对应。它们是离线协议检查，不能充当真实8B的语义交付。

最终344项去重PASS：harness五组raw 285、unique 283；标准库bindings16/entry34/boundary11。原90秒/审计守卫/分片选择器保持，JUnit无失败错误跳过，源码及快照一致。首次新增正例误把原始反斜杠与Markdown转义文本比较，1项断言失败；产品已成功写入。首次五组回执完整保留并逐文件哈希核验。修正该测试后重跑五组最终harness字节，三组标准库源码不变故未重复运行。首次失败不是产品RED；N16的781项产品/参考历史基线未重跑、未累计。

只读检查点2026-11-07T11:48:40.026690+00:00确认七保护身份、Ollama0.32.15、当前8B摘要与18799空闲。此结果不代表连续存活。N16准备956成员/输入1576、N15准备189/实际结果56/旧输入1575、九个无关文件及候选HEAD/tag/clean均核对保全，历史5e6ea89c-8e47-43a6-9480-7a11d72cabf5的FAIL_CONFIRMED保持。

本根没有actual/release/controller-authority/native-preflight/controller-ledger。当前持续目标的direct-user-decision明确actual0/review0，不能作为grant。原actual1/review1/retry0、120秒新鲜度与排他消费门保持。整包独审后harness-approval只代表准备；read_ready及无grant拒绝读回不运行run_once。

原生GBNF二进制、实际8B研究、原题覆盖和事实交付未验证，旧候选E01/E03信用不迁移。下一步整包独审、本地项目/UltimaDocs提交/tag/readback完成后，按execution-proposal请求明确一例及一次独立结果复核。无UI/音频/生产服务操作，失败不重试。远端push此前自动审批blocked by policy，本轮不重试。

closeout.py、publish.py、refresh_queue.py仅为预备控制面脚本，审查前未执行，不能作为已完成发布的证明。Windows原生ledger及所有旧证据保留。
