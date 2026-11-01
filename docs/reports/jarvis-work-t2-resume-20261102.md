# T2 用户续推与第4次修复设计门

2026-11-02，原单wo-ultimaagent-20261101-0021。用户要求继续，T2已恢复同一原单的架构复核。**设计r3独立评审PASS；产品源码和真实验收尚未通过。** 原3次失败、两个blocked检查点与固定验收条件保持，不将设计门当作T2技术门。

当前仍使用qwen3-8b-uncensored（Qwen3 8B系列），没有14B对照或生产模型切换。原brain/voice/turn进程与KWS不动，所有实现/测试留在C盘受管隔离工作区。下一次源码修复累计第4，控制器本次限定累计上限5，不重置工单或历史；Owner体验、冻结及发布另守原门。

补充设计：[结构化研究修复方案](../plans/jarvis-work-research-structured-plan-20261102.md)，SHA256 `7fe32a4bff35683d66d7900ea35d285a111209247ae5aec4edee14d9d2fa81bd`。只读SDK实际MockTransport证明JSON模式可经原NativeReAct/权限/遥测链传递且不泄漏到普通调用。已有Ollama/SDK与Pygments2.21.0可用，无需安装新依赖或重写Agent核心。JSON语法约束、原文局部语法证据和真实事实正确性分别验收。

方案修复原题中源码URL被中文标点/余文吞并的问题，实际读取指定的活跃UnifiedAgent；每条结论关联当前已读来源的可见行段。已有开源词法组件区分注释、字符串和调用，不能据此声称已证明全部语义、可达性或跨项目集成关系。独立审查仍逐条核对实际结论与主题。

独立设计r2返回3项Important，r3已全部解决：覆盖真实await/this多行调用；首次工具失败后阻止后续推理派发；文件写入分派/意图/结果分开记录，超时未决和部分写入诚实进入needs_attention，保留旧请求身份。没有新增持久恢复、后台轮询、取消/重放系统，T4仍未放行。

实施将先记录A/B失败测试再修复，覆盖回归与原8项隔离兼容后冻结单一候选，fresh代码审查后才另放真实8B E02。任何结果均保留。E01/E02/E03同候选各三轮、窗口负例和语义复核仍为T2出口条件；T3—T5未启动。

证据：data/evidence/jarvis-work-capability/T2/architecture-resume-20261102/、review-r4-plan/。设计检查点标签为ultimaagent-work-t2-r4-plan-pass-20261102，实际推送/远端解析以设计checkpoint回执为准。

## 已开始实施

设计检查点c6bcc3ca84d9fb46567b0895d8d12d5c78181e36、镜像a70c42b5b5e8f371f59e2ff41b0c470c9c5e641d及同名plan tag均已推送并核验远端。源码修复4现已按明确回执放行，基础源码仍等价610005e。执行端先做A/B RED/GREEN、覆盖和隔离兼容，随后等fresh代码审查，不自动启动真实模型验收。设计门不代替代码门或E02。

## 第4次源码候选与独立代码复核

30b6b14：195项测试通过，旧151及T1 60全部保留。但fresh代码复核REVISE，3项Important：方法声明误作调用、非标准换行导致证据行错位、回执多次取快照遗漏终态。真实8B/E02尚未运行。按既定累计上限5进入最后一次有界源码修复，原单/历史不重置，模型及验收不变。证据review-r4-30b6b14/，具体修复回执fix-round-5/controller-release.json。
