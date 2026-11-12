# s10-device-mcp 验收证据

- 验收人：主脑（豆包直做）
- 验收时间：2026-10-27
- 依据：jarvis-reverse-architecture C1/M28（MCP 设备接入标准层）；plugin-bus-spec §1.3（MCP=外部资源经适配器）

## 实现范围（档案层之上补 MCP 实操框架）

新建 `src/brain/iot/mcp_runtime.py`：
- `McpRuntime`：JSON-RPC 2.0 over stdio 子进程客户端（纯标准库）；initialize/list_tools/call_tool；
  逐行解析、非 JSON 行透传忽略、写入失败/无响应/超时/崩溃均确定性 McpError（不穿透异常）；
- `McpServerConfig`：server 配置（命令 + 工具需求映射）；
- 设备接线：call_tool 带 device_id 时经 DeviceRegistry 档案 + Controlability 过滤
  （read→readable / write→writable / control→controllable；末段匹配 + 自定义映射）；
- 冒烟桩 `run_fake_mcp_server`：纯 Python JSON-RPC stdio 服务（env/read、device/read、
  device/write、device/control），`make_fake_config` 生成启动配置；
- 无配置时 available=False，初始化如实返回"未接入"，调用报确定性错误。

## 验收项逐条

| 项 | 判定 | 证据 |
|---|---|---|
| ACCEPT-1 McpAdapter 全链冒烟 | 通过 | test_full_chain_smoke：initialize/list_tools/call_tool 全链 OK |
| ACCEPT-2 超时/崩溃/非法确定性错误 | 通过 | test_tool_failure_deterministic / test_crash_deterministic / test_unconfigured_reports_not_connected |
| ACCEPT-3 档案+可控性过滤（只暴露允许工具） | 通过 | test_device_gate_filters_tools / test_device_gate_unknown_device / test_device_gate_unknown_tool / test_unreachable_device_reported |
| ACCEPT-4 无配置如实报告未接入 | 通过 | test_unconfigured_reports_not_connected |
| ACCEPT-5 回执完整 | 通过 | 本文件 + receipt.json，ReceiptValidator 0 issues |

## 测试结果

- 新增：src/brain/iot/tests/test_mcp_runtime_s10.py — 10/10 通过
- 回归：test_device_profile_s3 + test_mcp_runtime_s10 — 13/13 通过

## 边界确认

- 不直连未授权设备；不可达设备如实报告（可控性=全 False）；控制类动作经闸门/征询占位；无真实 MCP server 不编造。
