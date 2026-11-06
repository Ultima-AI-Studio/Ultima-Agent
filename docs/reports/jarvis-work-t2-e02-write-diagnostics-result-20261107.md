# E02诊断单例：定位固定文件目标不匹配，研究仍未通过

原工单wo-ultimaagent-20261101-0021 / T2。用户call_948abbc3ba2948a9b3441d57051d9b27授权的诊断补修、必要独审、单例研究及一次结果复核均已完成。本次FAIL，经独立复核FAIL_CONFIRMED；没有research.md，E02受控0/3，T2仍未通过，未重试。

## 已交付的诊断修复

候选6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696基于0a57d50，隔离工作区C:/Users/Administrator/.codex/worktrees/jarvis-e02-write-diagnostics/UltimaAgent。只改work_service.py与诊断测试：从可信ledger首个失败writer记录导出固定原因码、阶段、类型、长度与受限哈希。未知文本不导出；不从SDK/model tool_results取诊断。原status/error及END/事实/引用/文件核验门保持。

有效RED14失败/3通过，GREEN17；产品518项加harness/入口/输入/边界289项，共807项离线检查通过。两项本地HTTP/junction集成不在本离线范围、不计通过；首次Unicode用例预期纠正及两份RED证据保留。准备manifest 27b40bb96214db7480ea50e23926aaf6b72dcf429b768e13cf274cf5fb19671d（410成员），独审 de10c96571ea29e7bf7af3d42e1aabc282b62dac105c07443816b37a98d1df5d PASS。准备项目55da4d4738981fdaf989d5873ec45db2341ac2e3，镜像cea0ccddc5255f60122864020e932f1ed8e28398，tag ultimaagent-t2-e02-write-diagnostics-ready-20261107；已提交后读回才签发单例。

## 唯一实际结果与原因

run 08d8377b-e1d2-40ba-8b7e-e20e1c66dfbd；UTC 2026-11-06T18:49:07.8005002+00:00 至 2026-11-06T18:49:48.4177121+00:00，外层40.6132553秒、exit1。CLI1，受控search1/GET4成功，4份来源可用。应用native POST尝试5，真实原生总推理计数未测量、保持null。

产品status=failed，主错误仍为Unlinked or failed END，未报告完成。新诊断research_failure.reason_code=INVALID_TARGET、stage=research.write、error_type=ValueError；长度35、SHA256 3489c8b6f353eda283e79f6c369e22b7f4cc57cf3c1f5a91c093d511e7964d85与源码固定消息Research target must be research.md一致。它定位到work_tools.py::WorkResearchWriteTool.run中params.get('path')!='research.md'，发生在resolve_v3引用/事实解析之前。

实际传入path字节未导出，不能称其为绝对路径或猜测值；前轮91fb07e8的具体原因仍未知，不能追溯认定相同。没有研究文件/完整runtime packet，不能评价事实质量已经合格或笼统归因为8B能力不足。当前只证实本次文件目标拒绝。

只读源码另确认接口不一致：v3_writer_schema向模型声明path为任意非空、最长2048字符string，writer却只接受字面值research.md。阶段提示已说Write only research.md once。下一步最小修复是收紧现有JSON Schema path enum为[research.md]，与原writer目标一致；不放宽路径授权、不改写模型输出或原生证据。本轮未实施该改动，具体提案H:\UltimaAI\UltimaAgent\docs\plans\jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107.md。

## 清理、复核和信用边界

原cleanup PASS；后续只读核对七个保护身份native/CIM/parent/命令摘要相符，本例已登记原生身份均不再存在；18799无监听，11434仍PID5708。点观察不等于连续存活监测，不追溯提升任何旧失败。记录范围无UI、音频或生产服务操作；没有切换模型或使用14B。

结果manifest 831775760a93d02b39250f1044964dfa149ae79d01a43e898c8f1731cb34bf47（44成员），独立结果复核 8326d2cc8d5e43434f858ae4d7185379ead8ffd611038d7bc9aeeabf0d99b0da，FAIL_CONFIRMED。实际/结果复核额度均0。此前三次实际失败完整保留；该序列累计入口4、CLI3均来自各次登记，不将清理或离线通过算研究成功。旧候选269aca5的E01/E03信用不转移到新候选。

原时限与CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8保持。后续schema补修和新单例需新明确范围；当前序列已结束，原项目目标仍未完成。远端push仍受此前自动审批blocked by policy阻断，本轮仅本地commit/tag和UltimaDocs镜像，无重试或绕行。
