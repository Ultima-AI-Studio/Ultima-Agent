## 补充复核 · TypeScript 接收者在候选构造时丢失

**PROVED（静态源码推导）。** 对封存 S3 L71–74 的普通调用语句 `const result = await this.toolRegistry.execute(…);`，候选生成器与完整语句验证器对同一调用构造了不同的操作名。

1. 产品 `src/brain/work_research.py:223–234` 对 .ts 使用 TypeScriptLexer，保留非空白 token 的原始类型、拼写与行号。安装版 `pygments/lexers/javascript.py:140,156–175` 的 TS root 在专用规则后显式 inherit；该处的调用表达式不匹配前置的类型注解等规则。`pygments/lexer.py:609–641,711–720` 说明继承位置及按序匹配。JS root 在普通标识符规则前把 this、super 标为 Keyword，点是 Punctuation，成员名是 Name.Other（javascript.py:55–60,80–94,118）。`pygments/token.py:28–32,65–67` 说明 Keyword 不属于 Name。
2. work_research.py:392–400 从后接左括号的成员 execute 向左拼接，跨点只接受 Name。因此候选是 toolRegistry.execute，丢失 this。_js_statement_anchor（351–365）把这个拼写交给 _js_support。对上述完整语句，前一有效 token 是分号，const 赋值及 await 符合 header，末尾分号闭合；完整 header 的 callee 是 this.toolRegistry.execute。237–265,272–301 最终比较不等，无法为这条语句签发其真实操作的 code 卡。S3 L97 的 this.provider.generateText 同理。普通成员调用 super.method 在相同词法前提下也会丢失前缀；此处未提供 super 的历史实例。独立的 if 条件、复合表达式、可选链等还受完整语句规则限制，不能从这一步推断也会获卡。
3. 产品 reference_cards 在 work_research.py:410–438 生成候选后才做上限挑选。实验 preparation-r2/run_stage_prefix.py:137–138 复用相同 _js_tokens/_anchors，实际 S3 outcome.json 的 15 个批准 symbol 只有日志/计时。它记录原始正文与最终卡表，没有逐 token 轨迹或每个候选拒绝原因；以上逐步归因是对该精确语句的源码推导。S4 的 Python 卡 45 已有完整 self._executor.execute，仍得到 unused。该缺陷可解释特定 TS 操作为何不能作为直接锚点，不能据此推断弃用原因、修复后事实得分或 E02 文件交付结果。

**更小的判别。** 在通用结构提取之前，优先考虑一次另批的离线对照：冻结原 lexer 和原 S3、S4，其他选择、验证、48 卡及权限规则全不变，仅在隔离候选中允许 dotted callee 的最左段取词法上确为 Keyword 的 this/super。针对普通 JS/TS 成员、this/super 成员及变量接收者保留完整 token 与全量候选/最终卡表，验证所签见证的完整操作与原行、来源和哈希逐一一致；加入注释、字符串、类型声明、跨行断裂或非成员关键字等拒绝样本。已有 S4 和其他无关见证按原文坐标/种类/操作比较，另查排序插入后 ID 变化及旧协议重开兼容，不能用手工卡号作金标。只承认新规则为 S3 显示至少一个此前缺失的核心调用、负例零误签且无无关语义回归；否则停止，记录拒绝层。独立人工 rubric 只用于验后，禁止输入模型或作为产品特例。一批、30 分钟、0 POST、0 外部费用、无产品写入，不交付模型事实判分或 E02 文件。未实施、未导入或运行 lexer、未分配额度。根控制器的依赖清点仅在限定范围发现 lark 1.3.1，四个 TypeScript 编译器路径均未找到；这条判别不需要引入新 parser。

**UNKNOWN。** 接收者识别修正是否足以扩大最终发给模型的实用证据、是否同时改变其他卡的排序/选择、作者是否采用新卡并写出有依据的条件和替代路径。后两层仍须分别取得证据。source21 与 C HEAD 保留，原 R2 两文件哈希见补充 JSON。
