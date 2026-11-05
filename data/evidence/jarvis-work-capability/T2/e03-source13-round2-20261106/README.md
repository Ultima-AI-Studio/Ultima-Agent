# source13 E03 round2 准备包

产品候选269aca5、社区8B与运行manifest保持。父包round1实际和独立结果已PASS，当前计正例1/3。本包仅准备第二轮；没有复制release、authority或actual，也没有签发新的实际或结果复核额度。

入口为code/acceptance_entry.py。`--verify`只核对本包与前轮收据；`--preflight`需要本包独立准备PASS并做只读现场准入；`--run`还需要新单例authority和未消费的actual/e03-round2。实际前后核对候选/模型/七保护身份，原夹具、持续提示、时限、清理和事实门保持。

前轮三个原始收据以相同字节放入inputs/prior-round1；inputs/predecessor-provenance.json记录来源路径与SHA。原terminal的PENDING不改写，事实PASS来自独立review；它们只作顺序前置，不得算作round2结果。authority.prior_reviews须精确绑定case、candidate与terminal/review/registration三项SHA。

离线验证：23项新反例RED20失败/3通过，修订后23通过；全量153通过，保留原130项功能/参数数量。guard无允许或拒绝的native I/O记录。这里只证明合成材料和fake native下的入口行为，不证明新现场成功。

code/controller.py与preparation-support/acceptance_adapter.py中的历史R路径及recovery入口仍是受各自旧门限制的非活动路径。当前只使用AcceptanceBackend与本包入口；controller、backend、夹具和adapter字节与已通过父包相同。新的guard仅将相同运行manifest的读取位置改为本包。

已有485/8产品测试未重跑：候选57项源码、7依赖和1346SDK文件哈希保持，原回执绑定仍在运行manifest内。默认SDK home生产兼容性、真实语义路由、整个系统的原生行为和新现场保护状态不由本包离线测试判定。

本包独立准备审查范围来自controller-offline-release.json；准备审查不授予实际运行。下一步新单例提案见verification/next-case-proposal.md。保留所有旧失败和Owner/冻结/远端门；此前push被自动审批拒绝，本轮不重试。
