# E02元数据兼容单例：已到研究写入，写入失败

原工单wo-ultimaagent-20261101-0021 / T2。用户call_3471155e77c74b8db30c1278112c74d2授权的补修、790项离线检查、独立准备审查、一次当前8B实跑和一次只读独立结果复核已经完成。单例FAIL，不重试；E02受控0/3、T2未过。

## 已完成的修复

产品候选0a57d50f226df70542838c05fb8a21e025e19447（269aca5后继），仅既有work_research.checked_native_identity增加可省略且严格list[str]的capabilities；其余版本/名称/摘要/未知字段等检查不变。四个旧依赖按冻结哈希复制并入提交，旧候选不变。产品501项与harness/入口/边界/输入289项共790通过；准备manifest 04e876bb3c4a166e82343fc91501498f6b8636d9b2ee9b89b69c38960f98d3ea，690成员，独审 27700d7933506c63af031655955334dd7466d77e97c6ab4d19410396be45ae75 PASS。两个需要本地服务/子进程的旧集成测试未计通过；早期guard/DNS/timeout及fixture失败保留。

准备已本地提交/tag及镜像：项目b4e12a8223f3e8bdb3810972806f14fdd882e132，镜像ae6dfae26ecb4e5094620a15eb7e5d62f6c548de，tag ultimaagent-t2-e02-native-metadata-ready-20261107。执行前读回通过后只签发并消费一次分配，没有重复请求同一授权。

## 唯一实际结果

run 91fb07e8-91dd-4ffb-9389-fea9c02bf285；UTC 2026-11-06T18:18:24.2217476+00:00 至 2026-11-06T18:19:11.7404573+00:00，外层47.5130164秒，exit1。产品CLI提交1次，原受控search1、GET4全部成功，四份完整来源可用。旧Invalid native model metadata未再出现；记录了应用层native POST attempts=5，实际原生推理总次数仍null。业务trace有五组compose inference/tool事件；这些不能替代完整原生成功计数或完整证据包。

产品首结果status=failed，error=`Unlinked or failed END`，content=`本次任务未完成。`。tool_results明确包含ultima_work_research_write的success=false、error_type=ValueError。无research.md或artifact；trusted-export complete=false、END=false。因此没有可做逐事实/引用验收的研究交付，不评价8B事实质量已达标。

只读代码定位：work_tools.py::_CapabilityTool.execute保存错误类型，但具体异常文本只进入ToolResult；随后WorkLedger.confirm_end同时检查线程、permit/seq、staged、工具成功、agent、结果和metadata，失败统一记录Unlinked or failed END。当前输出折叠了compose事件细节，也未导出失败的完整runtime packet，因此不能判断原始write ValueError具体来自字段、引用、扫描、路径或其他规则。不能凭通用错误判定模型能力或直接放宽END门。

## 清理、复核与信用边界

原始cleanup PASS；新端口18799关闭，所有本例已登记原生身份消失，无新增清理歧义。后续只读核验七个保护身份的native/CIM/parent/命令摘要全部一致，11434仍为Ollama PID5708。点观察不是连续监控；root witness eligible=false与overall FAIL保持。

结果manifest 4af5d17fbd6dc56a41628744b437cc6739da4a21b00c6f11ceecbdfd4f11f8f0（44成员）；独立结果复核06161e7ad7047631f29605c5a871d2717f7115ff531c5aab90a78426def0f4cb，FAIL_CONFIRMED。报告H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-native-metadata-20261107-r1\review\independent-result-review.json。结果登记H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-native-metadata-20261107-r1\review\result-registration.json；当前实际/结果复核剩余均0。两次旧真实失败及其清理结论原样保留；此三轮入口累计3、CLI累计2，不把未提交或清理通过当成功。

旧候选269aca5的E01三轮与E03三正一负通过记录保持原归属，新候选没有这些现场回归信用。仅当前qwen3-8b-uncensored，未使用14B；没有UI、音频或生产服务操作。声线参考文件缺失提示是隔离服务导入时配置日志，不是播放/录音或修改语音服务的证据。

下一步具体方案：H:\UltimaAI\UltimaAgent\docs\plans\jarvis-work-e02-native-write-failure-diagnostics-proposal-20261107.md。优先补齐研究write首次拒绝原因的安全有限诊断，保持END/事实门，避免继续盲跑；本轮不修改该冻结候选，也不再调用模型。

远端push仍受此前自动审批blocked by policy阻断；本轮仅本地commit/tag和UltimaDocs逐字镜像，没有重试或绕行。

## 2026-11-07 后续只读勘误（不改原运行结论）

原文“具体异常文本只进入ToolResult”表述不准确。_CapabilityTool.execute同时将error字符串和error_type写入ledger记录；WorkService.submit_work在最终研究回执中仅保留error_type，裁剪掉error。现存落盘材料仍不能还原具体write拒绝原因。该纠正只说明丢失位置，FAIL/清理PASS/POST尝试5/null原生总数及独审结论不变。
