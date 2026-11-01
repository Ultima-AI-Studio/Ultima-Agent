# 当前 Qwen3 8B schema 接线的单次兼容修复裁定

原单 wo-ultimaagent-20261101-0021，2026-11-02。原 T2 两轮修复、失败候选10fec03、blocked检查点afbbe3e及全部原始输出均保留。本裁定不重置原单或次数，也不代签 Owner 验收。

## 新证据与范围判断

用户补充当前模型为 Qwen3:8b。只读健康检查确认 UltimaAgent 配置仍为 qwen3-8b-uncensored（Qwen3 8B变体），14B未加载、未对照、未切换。

新的只读实际渲染证明：已安装SDK build_tool_descriptions只输出顶层参数，NativeReAct最终只收到path/string、title/string、sections/array。已声明的sections.items、facts/array、字符串items和来源ID enum没有进入模型的工具文本。现有自然任务提示同样未注明facts的类型。因而首个facts:string错误存在明确的产品接线缺口，不能直接用于推断当前8B能力不足。

项目工作流§4规定“同一阶段进入有界修复（默认上限2次）”。控制器此前按默认值停门并准备了模型对照；新证据表明最小下一步仍是原模型、原权限、原目标内的SDK兼容修复，非新增模型策略。基于用户既有“按顺序推进”的授权，控制器对该默认计数作一次明确、有限的兼容例外，人工处置本停点；不将它伪装成自动续跑或Owner批准。

## 唯一获准变更

- 应用已准备补丁633aa63821e4e3aa76db5b7209fdbd9b31dea615a0079de02894705f5a0d31dc，仅改src/brain/work_tools.py与src/brain/tests/test_work_research.py。
- WorkResearchWriteTool实例description增加完整当前JSON Schema，用SDK现有字段传递；参数、验证器、来源目录、文件/窗口权限、renderer、vendor、模型、依赖都不改。
- 新回归捕获真实NativeReAct提交给推理引擎的第一条system message，验证3/5来源的嵌套类型和enum实际可见；不能只检查schema字典。
- 先只上测试并记录RED，再上四行适配并GREEN；覆盖相关现有门与原8项隔离兼容，提交冻结候选，fresh scoped审查后才能真实验证。
- 不纳入提案中可选TODO文案，不添加题目答案或事后改产物。来源事实错误仍独立失败，schema可见不代表T2通过。

## 边界与计数

这是原T2累计第3次修复（默认2 + 本次单独兼容例外1），不是新单的第1次，也不改变前两次结论。此次最多一套两文件补丁，禁止扩大为提示词循环、模型比较或另一套Agent。实际E02先单轮，机械或语义失败即停；不重复采样求成功。通过后才放行同候选原有E01/E02/E03三轮和负例门。

本次不执行14B提案、不改变生产默认、不启动T3—T5、不动原服务/KWS、不安装依赖或修改vendor。最终Owner冻结与发布门保留。控制器承担这次默认计数例外的责任，所有授权来源和累计次数公开记录。
