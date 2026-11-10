# E02子进程准入恢复：启动问题已跨过，模型元数据校验失败

原单wo-ultimaagent-20261101-0021 / T2；产品269aca511d88412dbb9c15d23911138469a37aa2与当前qwen3-8b-uncensored保持。用户call_42e3d2dd124f406cb3ccebd14a9b1c0f授权的最小补修、272项离线检查、独立准备审查、一次实跑和一次独立结果复核均已完成。结果FAIL，不重跑。

## 修复及实际进展

子进程准入已拆分为子端纯原生身份核验、父端完整native/CIM/parent/命令核验；原Owned未知后代与清理规则、产品/入口及实际时限均未改。独立准备PASS已记录于ready tag，272项包括原219用例、定点17项、身份/transport10项、入口26项；完整测试超时、fixture setup失败与有效RED均保留。

新运行81c77cfd-9339-48b8-bae1-f67ec7d05cb4，北京时间2026-11-07 01:37:47.5697909—01:38:10.9598243，耗时23.3875413秒，入口退出1。此次child-clearance已签发并唯一消费，原生成员与listener已核对，实际提交研究CLI一次。产品完成原受控search1与GET4，四来源均可用；这是受控资料流程，不是真实联网验收。

## 失败与证据边界

产品首结果status=failed，error=`Invalid native model metadata`。原始terminal FAIL，first_failure=`work: CLI nonzero; no retry`。没有research.md或交付artifact，因而没有可做逐事实引用复核的研究内容，E02信用仍0/3。

trusted-export记录application native POST attempts=0，actual native start count=null；trace中的inference_start只是业务阶段标记，不能宣称模型实际推理过。本轮尚不能评价8B研究质量。模型、默认配置与权重均未更换。

已保存的root preflight `/api/tags`中模型记录含`capabilities`；冻结产品`src/brain/work_research.py::checked_native_identity`只接受name/model/modified_at/size/digest/details，额外字段会触发同一错误。这构成可复核的静态兼容缺口。产品自己的metadata GET原始返回体未导出，因此不声称与root preflight逐字相同；具体比较见review/result-inputs/metadata-shape-readback.json。

清理PASS：四个已登记Python身份与两个仅观察conhost均已消失，18799关闭、日志关闭、无Owned歧义。运行前后七个保护身份与源文件pins相同；后续只读核对native/CIM/parent/命令摘要仍相同，11434为原Ollama PID5708。点观察不等于连续监测。root witness仍eligible=false，不用短耗时/清理PASS升级整体结果。

## 独立复核与落盘

独立结果报告H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-child-admission-20261107-r1\review\independent-result-review.json，SHA256 3de5f47bb2e79540e46e93677610f55be4122b640e6b6552afed0fee5ef1fef4，结论FAIL_CONFIRMED。结果manifest 054b73280f79fb0669161442b2ee7f8e2c4c1ca4502ad6d86ac6e0aec5a69108（45成员）；准备130成员、1544绑定输入、前轮190准备与27结果、再前172准备保留，9项无关工作区文件保持。结果登记H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-child-admission-20261107-r1\review\result-registration.json。前轮7530ef7f...的FAIL/清理FAIL绝未改写；两轮入口2、实际CLI累计1，不把前轮未提交当成功。

E01同候选3/3、E03三正一负PASS保持原归属；E02/T2、后续阶段及Owner均未通过。本轮实际与结果复核剩余额度均0。

下一步应在新产品隔离候选处理严格metadata字段兼容，具体提案H:\UltimaAI\UltimaAgent\docs\plans\jarvis-work-e02-source13-native-metadata-compat-proposal-20261107.md。不改本冻结产品或已封存harness，不剥除真实返回字段来制造通过，不放宽模型摘要/版本/未知字段校验。新候选不得自动借用旧候选E01/E03信用。

执行端为当前root，审查为独立上下文。无UI、音频或生产服务操作，仅原题四来源与本机当前8B；没有使用14B。远端push仍受先前自动审批blocked by policy阻断，本轮仅本地提交/tag与UltimaDocs逐字镜像，无重试绕行。
