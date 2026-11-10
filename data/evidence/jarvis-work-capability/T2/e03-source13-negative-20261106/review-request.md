# 一次全包只读独立准备审查

原工单wo-ultimaagent-20261101-0021；依据持续目标内controller-offline-release.json及既定executing-plans最终独审。仅本包e03-negative准备，不复用耗尽的正例或结果复核权限。候选269aca5、固定当前8B、三轮实际独审PASS、原60/120秒准入、手动15秒开始及20秒fixture上限。

阅读plan.md、progress.md全部Ruling、原工作能力契约R04/R05/R08与E03，再审查manifest所有文件、parent56项、九前轮原件、恢复观察及输入补充。重点核对原源码work_context.py:165及test_focus_loss_reobserves_bound_edit允许焦点丢失后重新观察原HWND；旧Case.negative一律拒绝焦点与契约不符，RED已实际暴露。新场景用真实产品validate_work_target只读重新观察原绑定目标，不调用焦点替换；选区变化用真实replace_selection拒写，admission失败或任意ValueError不能冒充目标拒绝。Native代理只审计真实observe，并对任何意外replace硬拒绝/记录；mutation_sends与native_write_attempts及output必须全空。

重点复核：恢复快照原件不改；负例输入补created_utc是FILETIME纯派生，7核心身份没变，旧round3环境FAIL保留。三轮task/time/hash/cumulative绑定真实原件，coherent反例覆盖原PREP-M1。255离线测试及I/O guard，57源码/7依赖/1346SDK与485/8历史绑定。所有旧测试计数保留但正例CLI断言适配为零CLI，不等于重新做产品485/8回归。测试代码实际提取Case.negative并加载冻结WorkContextProvider，只有native I/O替身。

只读本地文件/JSON/XML/AST/hash及必要Git检查。不执行或导入产品/测试/native代码，不查现场进程或服务，不操作UI/键鼠，不网络/模型/音频，不写文件、不Git变更、不子代理。不要重新审正例事实。只给准备包结论，不授予实际负例/结果复核/E01/E02/T2/Owner/完整目标完成。

返回完整JSON，reviewer=root-independent，agent_identity，scope=e03-negative-acceptance-package，candidate，package_root，manifest_sha256，candidate_runtime_manifest_sha256，verdict，assessment，findings按Critical/Important/Minor含file:line，独立核验计数，每项declined_to_judge与limits。所有Considered-but-out-of-scope必须逐项列明，root逐项裁定。结论仅最终回复返回，由root原样保存；不得写文件。
