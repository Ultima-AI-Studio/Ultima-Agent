# 验收证据 · s3-behavior-layer（悬浮球与组合窗口行为层（M07/M08））

- **task_id**：s3-behavior-layer
- **状态**：COMPLETED
- **验收时间**：2026-10-27

## ACCEPT 清单
| 项 | 结果 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | 三态可视化：voice.thinking/listening/speaking + task.* + queue.* 全量映射，未知事件兜底 idle（test_three_state_mapping） |
| ACCEPT-2 | PASS | 记忆可视化：节点点亮/关联边/去重计数（test_memory_visualization） |
| ACCEPT-3 | PASS | 多场景组件树组装（header/chat|tasklist|envcard|article/footer）+ 既有场景回归不倒退（test_scene_composer） |
| ACCEPT-4 | PASS | 主题令牌全量对齐，glow 色与令牌一致（test_theme_tokens_aligned） |
| ACCEPT-5 | PASS | AR/VR 接口预留登记（xr.frame/gesture/space + 自定义注册，全部预留未实现）（test_xr_reserve） |
| ACCEPT-6 | PASS | 回执落盘经 ReceiptValidator 复核 0 issues；tasks.json 置 COMPLETED |

## 产出文件
- `src/brain/display/behavior.py`
- `src/brain/display/tests/test_behavior_layer_s3.py`（5/5 OK）
- `tasks/cards/s3-behavior-layer/acceptance-evidence.md`、`receipt.json`

## 边界未触碰
- 未推翻已冻结悬浮球/组合窗口对外行为；未向 fileDomain 之外写文件。
