# E02来源与证据schema对齐：新候选准备

原工单wo-ultimaagent-20261101-0021 / T2。用户call_33506a697ec545c6b2a396ff83086672已授权补修、必要独审、PASS后一例当前8B原题四来源研究及一次只读结果复核，失败不重试。候选a0d21ebf167c41a76410075f7a92f1680926213f，基于900b944，独立工作区C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-reference/UltimaAgent。

## 实现和范围

三个产品文件：work_navigation.v3_source_reference_map只投影本请求可信可见卡片，拒绝坏格式和ID碰撞；v3_writer_schema可选映射按source_id生成章节anyOf，各分支只给该来源的evidence_id enum。agent_server沿用已issued加当前confirmed未promoted view构造唯一report_schema，供native format和phase使用；work_research由已验证reads切片独立重建同一映射/schema/phase，不信任模型自报集合。静态工具注册继续通用schema，实际可写阶段强制配对。没有响应改写、提前promotion或增加模型轮次。

原research.md目标、resolve_v3归属/事实/重复来源、writer/END/ACK/外部读回门、字节/输出预算和清理时限均保留。现有诊断测试4处因新schema更早拒绝坏引用而需调整：有效输入进入writer后在测试resolver边界注入故障，继续检验真实resolver和最早错误留存；重复来源使用正确配对的ref。此故障注入只在测试，生产不改写参数。

新增29项测试覆盖同源合法/异源与未发行和外请求ID拒绝、空卡片/碰撞、多页合并、第三个confirmed pending页、三份来源前无writer选项、真实SDK mock format/strict/sampler一致、文件/ACK/SHA和runtime重放，以及修复全部自报hash与native entity后的schema/phase伪造拒绝。最大6页48卡、5来源schema小于32768字节，原token估算拒绝过大上下文；原transport回归保留strict/entity 32768/49152字节门，超限失败关闭，不宣称任意长真实上下文可装下。

有效产品RED初始28失败；后续混合键检查暴露TypeError并修复，重放负例改用真实prewrite包以跨过更早的嵌套一致性门。所有失败保留。最终566项产品回归通过：新29+目标19+诊断17+metadata43+研究178+navigation90+transport104+交付上下文86。原本地HTTP服务与cmd junction两个离线排除项不计通过，OS网络包未测量。

## 保护基线和验证范围

Ollama原PID5708已退出，现有PID11464于北京时间12:18:38启动；父进程24608、可执行文件、命令摘要、版本0.32.15、8B摘要相同，其余六个精确身份一致。用户说明没有主动关闭、重启或更新。应用日志记录启动与旧PID清理，启动来源未知。旧基线保留；只读建立新七身份基线，仅用于本候选，路径和SHA固定。native/CIM/parent/command/端口所有原检查仍执行；没有服务操作、终止或模型调用，不推断连续存活。

新基线负例有效RED14通过/2失败，修复后16通过，拒绝旧基线路径及同时替换PID和manifest摘要的伪造。首次bindings-red因候选重绑尚未完成产生2个正例错误，不算有效RED；入口首轮因尚未生成prepare_review.py而有1个依赖错误，保留后以完整包复测。原238 harness和入口26/边界11/绑定16最终总数为857，以封存readback为准。62来源、1557绑定输入。运行harness函数与共享P4/P1不变；只变候选/哈希/基线常量，bindings.validate增加固定基线SHA。

原生工作区operation6ba6a53b-e91b-4c90-9ab6-388a82ea2ed9已completed、registrationError=null。旧候选和旧失败均保留，旧269aca5 E01/E03信用不转移。本候选尚无真实研究、E01/E03或实际联网验证。

## Review Focus

按plan.md五项逐一审查来源配对、pending时序、本请求映射隔离、独立重放、字节/次数/事实门。另审查readonly身份变化记录和固定baseline绑定、原七角色保护力度、诊断fixture是否保留原覆盖、原时限/清理与单次权限，不能把离线成功或新服务存在当作实际研究通过。

当前actual authority尚未签发，E02/T2/Owner NOT_PASSED。远端push仍受此前自动审批blocked by policy阻断，不重试或绕行。

执行框架首次回归另有16个失败，均因documents()夹具保留更新保护基线前的输入manifest SHA，运行时在正确的候选/来源门提前拒绝。仅重绑该夹具常量，断言和运行函数不变，最终238项按新哈希复测；旧失败与旧哈希通过记录均保留且不计当前通过数。
