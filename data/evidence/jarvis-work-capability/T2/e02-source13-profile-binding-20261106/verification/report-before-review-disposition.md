# E02 source13 原资料验证包绑定适配进展

原工单 wo-ultimaagent-20261101-0021；候选269aca511d88412dbb9c15d23911138469a37aa2，当前qwen3-8b-uncensored。E01固定三轮3/3、E03三正例和一负例已经正式通过。E02本轮完成现有原资料验证代码的候选绑定适配及557项离线契约检查；独立准备审查进行中，E02/T2及后续门未通过。

本轮复用原profile算法：只改当前候选常量和一处固定前置函数源码路径。原测试13个源码根及3处旧辅助源码引用适配后，全部原始顶层AST语句及540个用例标识保留，另增17个当前绑定检查。新adapter只提供7个已定义接口，通过当前57源码、7依赖、1346 SDK文件哈希后，使用固定历史模块的资料/导出/读回辅助函数及SDK来源校验。历史模块的旧运行定义不经新adapter公开或调用；此复用不是Python/操作系统隔离保证。

本轮证据根：data/evidence/jarvis-work-capability/T2/e02-source13-profile-binding-20261106。封存manifest129文件，SHA-256 ec15aa82ee9ef72ff366c33eb997307e8151a97957eaa6d3f8544dc555424382。当前profile-preparation/manifest.json绑定1461个输入；旧原包五文件保持原字节，旧六次修订、NOT_READY待独审状态及所有失败继续保留，没有以新目录重开旧第七轮。

实际离线记录如下：

| 阶段 | 检查结果 | 说明 |
|---|---|---|
| binding-red | 8/8预期行为失败，0错误 | 旧候选仍被接受及旧入口暴露，先于实现 |
| binding-focused-green | 17通过 | 当前绑定的新增行为 |
| binding-inventory | 收集557个唯一标识 | 保留原540；不是执行通过 |
| binding-full-green | 557项中79失败、8错误 | 保留原记录；源码路径、辅助代码位置及README命令遗漏 |
| binding-location-green | 138通过 | 原断言不变，纠正上述位置/说明 |
| binding-full-green2 | 557通过，0失败/错误/跳过 | 最终完整离线契约证据 |

各阶段输入/包前后哈希一致，Python审计守卫没有记录实际网络或子进程请求；不据此宣称OS/native全局零活动。原始固定run_checks.py实际调用仍为0，本轮完整检查由隔离run-stage.py执行相同557标识。测试中的模拟服务与transport不代表真实SDK原资料运行、8B理解、真实联网或产品交付。

当前未提供具体RootControls、worker/reader进程入口或运行authority，原资料实际调用、产品CLI、模型推理及UI/音频操作均0。下一步需在准备审查结论基础上准备外层入口，并明确原275/310/315秒时限、独立进程退出及两次读回的来源。旧入口固定保护5身份，当前基线为7身份，不能沿用旧身份/额度；原题774字节、四来源正文、人设、scanners、SDK写入/END/ACK/文件读回继续保留。

用户持续推进授权覆盖本轮有界离线准备；内联实施及一次整包准备独审，不包含新的实际用例或结果复核。当前reviewer为/root/review_e02_source13_profile_binding；报告返回后由root处置，不以“测试通过”预填独审、运行、E02或T2通过。

本地准备检查点tag为ultimaagent-t2-e02-source13-binding-review-20261106，具体提交与逐字读回见verification/preparation-local-checkpoint.json。远端push此前被自动审批以blocked by policy拒绝，本轮未重试或改通道，不能把本地留档写成远端同步。
