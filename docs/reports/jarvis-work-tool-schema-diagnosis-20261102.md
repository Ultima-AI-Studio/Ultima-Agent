# Qwen3 8B 工具契约可见性诊断

用户确认当前挂载模型为 Qwen3:8b。2026-11-02 的只读 `/health` 返回 `qwen3-8b-uncensored`，Ollama 标签也将它识别为 Qwen3 8.2B；与 richardyoung/qwen3-8b-abliterated 标签的 digest 相同。此处只对齐模型身份，不把不同标签当成官方标准权重的等价证明。14B 对照没有执行，生产默认配置没有变化。

## 确认的接线缺口

已安装 SDK `openjarvis/tools/_stubs.py:551-563` 的 build_tool_descriptions 只遍历最外层 properties；NativeReAct 在 `agents/native_react.py:233-254` 使用这个文本作为工具说明。

实际绑定报告工具后，经真实 SDK 渲染得到：

```text
Parameters:
  - path (string, required)
  - title (string, required)
  - sections (array, required)
```

声明字典中真实存在的 `sections.items`、`source_id` enum、`facts: array` 和字符串 items 没有展示给模型。当前工作提示也只列出这些字段名，没有补出嵌套类型。因此首个 `facts:string` 失败至少包含一个明确的产品适配缺口，不能据此直接断言 8B 模型能力不足或优先要求换 14B。

诊断只构造和渲染 ToolSpec，没有 execute、推理、网络、UI 或生产写入。原始证据在 `data/evidence/jarvis-work-capability/T2/schema-prompt-diagnosis/`。来源事实错误仍独立成立；补齐 schema 不会自动证明 OpenAI/TODO、错源归因或整个研究任务通过。

## 最小兼容方案

仅在 WorkResearchWriteTool 实例 description 中附上完整当前 JSON Schema，使用 SDK 已支持的字段；保留参数本身、来源、校验器、renderer、权限、模型和 vendor。测试捕获真实 NativeReAct 交给推理引擎的第一条 system message，确认 3/5 来源时嵌套类型和 enum 实际可见，而非只检查 schema 字典。

补丁仅涉及 work_tools.py、test_work_research.py。准备时未应用的补丁 SHA256 为 `633aa63821e4e3aa76db5b7209fdbd9b31dea615a0079de02894705f5a0d31dc`，前后内存渲染与未变证明一并保留。

## 控制器明确处置

项目工作流的两次修复是默认值。新证据说明这是原授权目标、原 8B、原权限内的兼容缺口，控制器限定一次修复例外，累计记为第 3 次，不重置原单、原次数或 blocked 检查点；不冒充 Owner 批准。详细范围见 `schema-prompt-diagnosis/controller-compatibility-ruling.md`。

依然先 RED/GREEN、冻结候选、fresh scoped 复核，再做原 8B 的单轮 E02。机械或语义失败立即停；只有真实通过后才能继续原三轮及前序/窗口门。未降低验收条件，也未开放 T3—T5。14B 提案后移且保持未批准、未执行。

## 已完成结果

候选610005e已按双文件原补丁完成RED2fail→GREEN2pass，151项回归与fresh代码复核通过。保持当前8B的唯一真实E02仍因非法JSON及无依据OpenAI实施断言失败；例外结束，未放行后续阶段，没有开启14B。见[真实验收报告](jarvis-work-schema-compatibility-result-20261102.md)。
