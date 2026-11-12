# s4-a2ui-renderer 验收证据

- 日期：2026-10-27（Asia/Shanghai）
- 结论：COMPLETED
- 实现：控件/Ultima 组件安全 active 渲染器 `src/window/active_renderer.py`（M08 残余，对齐 product-alignment-20261027 N4）
- 冻结组件：未修改冻结组件；复用 a2ui_validator（_catalog/_validate_schema/_validate_resource_reference/validate_batch）与 offline_renderer（RenderError/RenderLimits）真实实例

## 实际命令与结果

1. `python -m unittest src.window.tests.test_a2ui_renderer_s4 -v`
   - `Ran 8 tests` → `OK`（ACCEPT-1/1b/2/3a/3b/3c/3d/6）
2. 回归 `python -m unittest src.window.tests.test_a2ui_validator src.window.tests.test_text_core src.window.tests.test_combo_a2ui src.window.tests.test_combo_orchestrator`
   - 除 `test_text_core.TextCoreEndToEndTests.test_real_brain_empty_production_queue_text_closes_the_offline_loop` 1 条外全绿（67/68）
   - 该 1 条失败为**预存在环境性失败**：断言"任务库为空共 0 个任务"，而 tasks/tasks.json 现 29 条（s4 批次推进所致，与本工单代码无关，未触碰其链路）
3. 全部测试数据落 tempfile / 内存批次，未污染真实库

## ACCEPT-1~6

| ID | 结果 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | 控件五件 renderer 可用：Button（action 事件回调化收集，无回调渲染 disabled）/ Slider / TextField / Modal（details 折叠）/ AudioPlayer（禁用占位） |
| ACCEPT-2 | PASS | Ultima 七件 renderer 可用：UltimaWindow/UltimaSwitch/UltimaProgress/UltimaListCard/UltimaOrb/UltimaSensorCard/UltimaStatusTag 全量渲染 |
| ACCEPT-3 | PASS | 非法输入拒绝：未知组件→ActiveRenderError；越权 action 仅回调化不执行；远程 URL asset→拒绝（受控本地引用）；任意 style 属性→schema additionalProperties 拒绝 |
| ACCEPT-4 | PASS | 既有回归不倒退：三个文件 42 条全绿 + test_text_core 25/26（1 条环境性失败与队列状态相关，非本工单引入） |
| ACCEPT-5 | PASS | docs/specs/registry.md 组件状态回填：控件 5 + Ultima 7 标记 renderer active（落点 active_renderer.py），静态 5 标 active（offline_renderer.py），Video/Image renderer 保持未实现 |
| ACCEPT-6 | PASS | 回执完整（receipt.json + ReceiptValidator 复核 0 issues + tasks.json 置 COMPLETED） |

## 关键实现约束

- action 事件回调化：Button.action → self.actions 收集（drain_actions 消费），不执行真实副作用；未挂 on_action 回调时按钮 disabled；
- AudioPlayer 仅接受受控本地引用（asset:local 正则，复用 _validate_resource_reference），渲染 `<audio disabled data-asset>` 占位，CSP media-src 'none' 不放宽；
- 无任意样式注入：props 全量过组件目录 schema（additionalProperties:false），仅渲染白名单属性；
- 组件图提取自建（允许共享引用，与静态子集的树约束分离），可达性由 validate_batch 保证；
- 输出文档 CSP 全禁脚本/资源/连接/字体，零 JS。
