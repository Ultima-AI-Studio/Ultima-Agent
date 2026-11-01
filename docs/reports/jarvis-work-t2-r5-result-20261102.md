# T2 源码5代码门与真实工作门结果

2026-11-02，原工单 `wo-ultimaagent-20261101-0021`；源码候选 `b6ab85b54f638594ccd7adcd792362bd4ff0a8fe`。

**代码独审通过，T2真实工作验收失败。** 新鲜回归为217项唯一测试通过，保留旧195项与T1的60项；第4次源码复核发现的三项Important已修复。代码通过不代表模型任务达成。

当前 `qwen3-8b-uncensored`（8.2B、Q4_K_M）只运行获准的一轮原题E02。实际搜索成功，4份固定官方来源均HTTP200。仅一次推理和一次报告工具调用，报告在写入前被拒绝；没有已验证文件、成功文件写入或待定写入。CLI与验收程序均退出2。没有第二轮、14B对照、其他用例或后续阶段。

首次拒绝为README的L10–23超出内部8行上限。独立逐条审查实际12条结论后还发现：首条引文只是徽章/演示链接，三条code事实缺symbol，引用不存在的行号，并把明确写着OpenAIProvider尚未实现的源码说成支持OpenAI。因而只扩大行数不能产生合格成果；不能将这次失败扩大为所有8B模型都无能力的结论。

20项输入、模型摘要和4个受保护进程身份在运行前后保持一致；6个自有进程已退出，隔离锁仅经死主身份确认后清理。KWS与原运行服务未重启，生产源码和默认模型未切换。测试输入、失败记录和原单累计历史保留。

累计源码修复5/本轮控制器上限5已到。T2通过真实状态机EXECUTING→FAILED→BLOCKED收门，已有两次真实FAILED→QUEUED历史不改，其他45条队列记录不变。当前只进行本地只读架构裁定；不继续盲目重跑、不削弱事实验收、不自动开始第6次源码修复。T3—T5未放行，Owner冻结与发布未完成。

## 可读回证据

- 原始回执：`data/evidence/jarvis-work-capability/T2/20261102-b6ab85b/e02-round-1/receipt.json`，SHA256 `135f2896d857dccf16c969977eb797075831e2289057d53a76d1ff984145b7b6`。
- 独立真实门审查：`data/evidence/jarvis-work-capability/T2/review-live-b6ab85b/review.json`，SHA256 `43356b9dbe9a63ae437e6cdb3e319142c88e8e66689c58911e4e4ac12657837d`。
- 代码独审：`data/evidence/jarvis-work-capability/T2/review-r5-b6ab85b/`；覆盖回归和代码门证据：`fix-round-5/`。
- 控制器独立读回与队列收门：`data/evidence/jarvis-work-capability/T2/post-cap-diagnosis/`。

代码检查点tag `ultimaagent-work-t2-r5-code-pass-20261102`已推送并核验；真实FAIL检查点、镜像和远端状态另见本次checkpoint回执。不把任一检查点称为T2-frozen。
