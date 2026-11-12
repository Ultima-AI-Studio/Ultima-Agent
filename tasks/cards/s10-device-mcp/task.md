# 任务卡：s10-device-mcp
- **task_id**：s10-device-mcp
- **标题**：设备实操（C 类 · MCP 适配器框架与冒烟）
- **优先级**：80（P1）
- **category**：core　**skill**：engineering
- **依赖**：s3-device-profile（M15 档案层/可控性三判定已建）
- **依据**：jarvis-reverse-architecture M28/C1（MCP 作为设备接入标准层）；plugin-bus-spec §1.3（MCP=外部资源，经适配器挂总线）；form-expansion-plan §4.3

## goal
设备实操落地（档案层之上补 MCP 接入实操框架，可测可冒烟，不依赖真实设备）：
1. MCP 客户端适配器框架 McpAdapter：JSON-RPC 2.0 over stdio 子进程（纯标准库，不引第三方）；
   initialize/list_tools/call_tool 三动作；stdout JSON-RPC 解析、stderr 透传、超时与崩溃处理；
2. 设备接线：MCP 工具经 DeviceRegistry 档案与可控性判定过滤——只暴露"可读/可写/可控制"允许的工具；
3. 冒烟：内置 FakeMcpServer（纯 Python JSON-RPC 桩，模拟设备只读/可写工具），
   验证 发现→档案→可控性→调用 全链；无真实 MCP server 时如实报告"未接入"不编造。
   
**禁止**：不直连未授权设备；不写文件到 fileDomain 外；不可达设备如实报告；控制类动作走闸门征询。

## acceptance[]
- [ ] ACCEPT-1：McpAdapter 启动/初始化/list_tools/call_tool 全链（FakeMcpServer 冒烟通过）
- [ ] ACCEPT-2：超时/崩溃/非法响应确定性错误（不穿透异常）
- [ ] ACCEPT-3：设备档案+可控性过滤：只暴露允许工具；不可控工具拒绝并留原因
- [ ] ACCEPT-4：无 server 配置时如实报告未接入；控制动作触发高危征询占位
- [ ] ACCEPT-5：回执完整（ReceiptValidator 0 issues + tasks.json COMPLETED）

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src/brain/iot + tests + tasks）
