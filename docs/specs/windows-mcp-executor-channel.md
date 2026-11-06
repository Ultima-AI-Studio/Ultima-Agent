# Windows-MCP 执行通道（受限实例）配置与真机验证

- 日期：2026-11-06
- 状态：受限实例可用，真机三项验收通过；**尚未接进执行层**
- 用途：给 UltimaAgent 的「执行」补一只操作桌面的手（开程序、点按钮、读窗口）

## 一、选型结论

- 采用仓库：`CursorTouch/Windows-MCP`（https://github.com/CursorTouch/Windows-MCP）
- 规模与资质：约 11,149 stars / 1,204 forks / 42 open issues；Python；MIT；默认分支 main
- 包版本：`windows-mcp 0.8.8`（`pyproject.toml` 实测），要求 Python >= 3.14
- 服务自报版本：`server_info.name=windows-mcp`、`server_info.version=4.1.6`（与包版本不一致，原因未查）
- 定位：**它是手，不是脑**。只负责「做得动」，不负责「该做什么」「算不算成功」。看不懂画面、不会自主决策。

### 被否决的候选（仅作对比，不采用）

skales、py-gpt、invisible_playwright_mcp、axuse、Interceptor、domdomeg/computer-use-mcp、openchatx-mcp、moling、nuphus-mcp。

### 官方自述限制

- 无法精确选中段落内部分文字
- `Type` 适合填文本框，不适合在 IDE 里写代码
- 不能用来玩视频游戏

## 二、受限实例配置（已落地，可复现）

### 环境（独立，不碰现有 venv）

| 项 | 值 |
|---|---|
| 试验目录 | `H:\UltimaAI\_shared\tools\windows-mcp-test` |
| 解释器 | `H:\UltimaAI\_shared\tools\windows-mcp-test\.venv\Scripts\python.exe` |
| Python | 3.14.6（uv 自动下载 `cpython-3.14-windows-x86_64-none`） |
| 安装 | `uv pip install --python <venv python> windows-mcp mcp` |

**禁止污染**：`H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe`（3.13）、`venv-voice-next`。
系统无 3.14（`py -0` 只有 3.12 默认与 3.11.15），必须走 venv 自带解释器。

### 启动命令

```
<venv python> -m windows_mcp serve --tools "Snapshot,Screenshot,App,Click,Type,Wait,WaitFor,Shortcut,Scroll,Move"
```

环境变量（探针侧注入，**尚未持久化**）：

- `ANONYMIZED_TELEMETRY=false`（遥测默认开，必须关）
- `WINDOWS_MCP_DISABLE_FLASH=1`

### 生效工具（11 个）

`App, Click, ControlStatus, Move, Screenshot, Scroll, Shortcut, Snapshot, Type, Wait, WaitFor`

**未暴露**（白名单外，实测确认）：PowerShell、Registry、FileSystem、Process、Clipboard、Scrape、Notification、MultiSelect、MultiEdit、DisplayInventory。
`ControlStatus` 由服务自动保留，不在白名单里也会出现。

### 关键工具参数（实测 schema）

- `App`：`mode` 枚举 `launch / launch_executable / resize / switch`；`name`、`window_loc`、`window_size`、`executable`、`args`、`cwd`；无必填
- `Snapshot`：`use_vision`（默认 false）、`use_dom`、`use_annotation`（默认 true）、`display`、`region`
- `Screenshot`：`use_annotation`（默认 false）、`display`、`region`；不返回 UI 树，返回图片 + 光标 + 窗口摘要
- `Click`：`loc=[x,y]` 或 `label`；`button` 左/右/中；`clicks`：0=悬停 / 1=单击 / 2=双击
- `Type`：必填 `text`；可选 `label`、`clear`、`caret_position`（start/idle/end）、`press_enter`
- `Wait`：必填 `duration`（整数秒）

## 三、真机验证证据（2026-11-06 实测）

| 验收项 | 结果 | 实测证据 |
|---|---|---|
| 打开程序 | 通过 | `App(launch_executable, C:\Windows\System32\calc.exe)` → `{"pid": 34680, ...}` |
| 读到窗口标题 | 通过 | 窗口列表出现 `计算器  Normal 502×810  handle 4984680` |
| 点按钮 | 通过 | 按坐标点 `7 → + → 8 → =`，界面显示 `7 + 8 = 15` |

补充实测数据：

- 整屏快照体量：基线 25,859 字符；启动计算器后 29,465 字符；均 0 张图（`use_vision=False`）
- 显示器布局：`DISPLAY3 (0,0)-(3840,2160) primary`；`DISPLAY2 (3840,0)-(6400,1440)`；`DISPLAY1 (6400,0)-(8960,1440)`
- 区域截图坐标换算：`region=[0,0,900,1300]` 返回图片 747×1080，缩放比 1.204，点击坐标按此反算
- 验证脚本：`step1_snapshot.py` / `step4_retry.py` / `step6_screenshot.py` / `step8_calcshot.py` / `step9_click.py` / `step10_click2.py`
- 证据图：`calc-region.png`（点前显示 0）、`calc-after.png`（点后显示 15）

## 四、四个已踩的坑与规避

### 坑 1：人在用电脑时，动作被直接拒绝（不是排队）

- 现象：返回 `{"code": "USER_CONTROL", "status": {"state": "user", "generation": 2, "wait_seconds": 9.998}}`，`App` / `Click` 均被挡
- 根因：控制权门控生效——人在操作时 AI 让路，需空闲约 10 秒才放行
- 规避：调用层写「被拒 → 等 2 秒重试 → 最多 10 次」，全部失败才判失败并上报；不要一次被拒就当任务失败
- 备注：这是**正面特性**，不是缺陷；但无人值守场景必须有重试策略

### 坑 2：切窗口被 Windows 拒绝

- 现象：`App(mode=switch)` → `Failed to bring window to top: (5, 'SetForegroundWindow', '拒绝访问。')`，工具报 `Failed to bring ... to the foreground within 1 second`
- 根因：Windows 前台锁定策略，非前台进程不能强行抢焦点
- 规避：不要依赖 `switch`。改为**点击目标窗口可见区域激活**，或直接按坐标点击（仅当目标窗口未被遮挡）

### 坑 3：UI 树默认 500 元素上限

- 现象：`[Tree] Capture truncated at 500 elements (limit=500)`
- 根因：聊天类大窗口元素极多，把预算吃光，其他窗口读不到按钮
- 规避：`WINDOWS_MCP_MAX_TREE_ELEMENTS` 调高；或配 `WINDOWS_MCP_EXCLUDE_PROCESSES` 排除干扰进程；紧急场景用 `region` 缩小范围 + `Screenshot` 按坐标点

### 坑 4：部分窗口读不到界面

- 现象：13 个窗口报 `UIA_E_ELEMENTNOTAVAILABLE (-2147220991)`，日志 `[Tree] 13 window(s) failed to capture`
- 根因：部分应用（Electron 类）不吐 UI 元素
- 规避：`WINDOWS_MCP_UIA_CONNECTION_TIMEOUT_MS`（默认 2000）/ `WINDOWS_MCP_UIA_TRANSACTION_TIMEOUT_MS`（默认 5000）按需调；这类窗口只能截图看，必须配排除名单

### 文档与实现不一致（已实测确认）

- README 宣称的三档门控 `relaxed/balanced/strict`、`--control-policy`、`--no-control`：**本机 0.8.8 CLI 均不存在**
- `serve --help` 实际参数：`--transport / --host / --port / --debug / --config / --auth-key / --allow-insecure-remote / --ip-allowlist / --tools / --exclude-tools / --cors-origins / --ssl-certfile / --ssl-keyfile / --oauth-client-id / --oauth-client-secret / --stateless-http`
- 结论：门控行为只能靠默认策略 + 调用侧重试，不能靠参数绕过

### SDK 字段名坑（写客户端必踩）

MCP Python SDK 字段是 **snake_case**：`init.server_info`、`tool.input_schema`、`ImageContent.mime_type`。写 camelCase 直接 `AttributeError`。

## 五、接法建议

1. **形态**：后台常驻一个受限实例，主脑经 MCP 调用；不嵌入现有执行通道进程
2. **权限**：默认只开安全工具（截图 / 快照 / 点击 / 输入 / 启动程序 / 滚动 / 快捷键）；PowerShell 与注册表默认关
3. **重试**：被 `USER_CONTROL` 拒绝时等 2 秒重试，上限 10 次；仍失败则挂起任务并告知用户
4. **不依赖切前台**：用点击激活目标窗口
5. **审计**：每个动作记动作名、参数、结果码
6. **环境**：独立 venv（Python 3.14），不碰 `venv-openjarvis`
7. **常驻**：`windows-mcp install` 会建每用户计划任务 `windows-mcp-server`，**会改变系统状态，需用户明确同意后再装**

## 六、尚未完成

- 未写 `~/.windows-mcp/config.toml`；遥测关闭只作用于探针进程，未持久化
- 未配置 `WINDOWS_MCP_EXCLUDE_PROCESSES`、UIA 两个超时、`WINDOWS_MCP_SCREENSHOT_SCALE`、`WINDOWS_MCP_MAX_TREE_ELEMENTS`
- 13 个 UIA 失败窗口未治理
- 未安装开机自启（计划任务）
- 未接进 UltimaAgent 执行层，具体形态未定
