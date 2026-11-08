# E02 证据优先与来源读取候选：单例结果和独立复核

原工单 wo-ultimaagent-20261101-0021 / T2；冻结候选 43da3f014a763b8ea3963872a8f1ce8ebea77531。本例确已生成 research.md、完成写入读回与 ACK；独立结果 **FAIL_CONFIRMED**：事实与引用及完整原题覆盖未通过。9 条陈述仅第7–9条得到所选锚点直接支持。E02仍0/3，T2/Owner未通过；保留实际产物，不误报“未生成文件”。

## 本次实际完成情况

用户 call_7004c6eafaca48e3a6f19dd87f59d024 明确分配一例研究与一次独立结果复核，retry0；run d0109d12-520f-4f92-88a3-938e69905ba2。北京时间 2026-11-08T14:30:52.520898+08:00 至 2026-11-08T14:31:59.628018+08:00，外层耗时 67.108126 秒。固定当前 qwen3-8b-uncensored，原题、四来源和原预算保持。仅调用原入口一次、CLI一次、search1/GET4、inspect5；应用原生POST7且完成7。服务端实际生成启动总数未测量，保持null。

第6次 writer 正常 stop，601/2048 tokens；第7次 ACK stop，39/256 tokens。七次均正常 stop。本例9个事实对象均实际先输出 evidence_id，再输出 claim；这是本例响应证据，不代表自然语言事实已经正确或稳定性已经通过。

实际文件写入和接受副作用各1；product status=succeeded。tool_results 中两条 research_write 成功行是不同层级的记录，不能计为两次物理写入。可信runtime、文件字节读回、ACK的逐项判断见独审。

- [实际 research.md（事实验收未通过）](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-source-grounding-controlled-preparation-20261108-r1/actual/E02-controlled-1/outputs/1391bd35-6744-48d5-b57f-04e1b6f00d7f/research.md)，1735字节，3节9条陈述；SHA256 974feebdd606d0670185108a2b964a810b412ab5702696287b5253a3341c57df。
- [独立逐事实复核](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-source-grounding-controlled-preparation-20261108-r1/review/independent-result-review.md)，JSON SHA256 80bb3c0a9469afec33191662f72c0f0f6cf392e38b3f8379899f81ca6ccf7b0a。
- [原始结果清单](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-source-grounding-controlled-preparation-20261108-r1/review/result-inputs/result-manifest.json)，66成员，SHA256 87e267c51e8fb9397258ab0e9dfd26db828ff74fcdbd173ce78bffea6842a66f。

## 已确证的内容缺口

1、2、4使用的标题或局部声明不能直接支持所写的更广泛事实。第3条还将Whisper/Parakeet转录模型与LLM混淆。第5条把TODO内容扩展成当前provider支持状态，未读到同一来源48–51行已构造GeminiProvider的实现。第6条把console.log与锚点之外的Logger.info合成一条陈述。只有第7–9条的日志或计时局部陈述与所选锚点匹配。引用不通过不等于每条事实在所有资料中均为假，具体标准是该陈述能否由它选择的锚点直接支持。

页面顺序为S1三页（26–49、50–73、74–97）、S2一页（20–43）、S3一页（25–48）。S4已GET但inspect0。第6次请求仍提供仅可选择S4的inspect分支，同时允许write；模型在还有一次读取机会时提前写入。三来源资格已满足，原题要求的架构关系、工具执行路径和现有开源底座接入没有完整回答；日志和产品宣传不能替代这些内容。

## 原时限、清理与保全

CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315秒，context16384、messages+schema32768/entity49152字节、输出2048及较小阶段上限保持。未重试、换模型或扩预算，无UI、音频和生产服务操作。

原terminal的PENDING_ROOT_INDEPENDENT_REVIEW及timing_eligibility=UNOBSERVED_NEVER_TIMED_PASS不改写。root witness eligible=true；独审根据绑定本run的时钟、terminal/seal摘要和观察事件核对原时限，不能只由67秒外层耗时推出TIMED_PASS。清理PASS，本例身份在保存的收尾观察中消失、隔离端口关闭；七个保护身份在保存的核对点相符，未证明连续存活或报告时实时状态。

179准备成员、79产品源pin、1606输入及旧失败保持；1022产品相关与350入口离线检查是此前准备证据，本次没有重跑或转为实际信用。一个非输入tracker HTML按已独审的动态观察例外保留，其他14个无关文件严格核对。本次一例与一次结果复核已消费，剩余0。

## 下一步与归档

[后续提案](H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-e02-write-eligibility-and-evidence-scope-proposal-20261108.md)先审查写入资格与任务证据覆盖的衔接，再审查逐证据原子事实表达。提案未实施、未独审，不产生修复或下一单例授权。当前8B、原预算和完整原题验收保持，不以字段顺序或重复提示代替语义证据。

[根controller只读补充分析](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-source-grounding-controlled-preparation-20261108-r1/verification/result-source-analysis.json)独立署名，不冒充原66成员结果manifest或独审。结果报告与后续提案镜像至UltimaDocs，本地commit/tag及Git/disk读回由result-publication-readback.json、result-final-readback.json证明。

全局汇总刷新本轮因另一工单0026使用生成器不接受的completed状态失败；本工单canonical登记照常更新，13:31旧汇总明确标为非新鲜，没有改其他工单或弱化生成器。独立补充审查允许继续本地归档，不等于汇总刷新成功。远端push此前被自动审批以blocked by policy拒绝，本轮没有重试或换通道。
