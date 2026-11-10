# round3 后现有 Ollama 服务单次恢复提案

原单 wo-ultimaagent-20261101-0021，候选269aca5，E03固定正例3/3、负例未通过。此提案仅恢复缺失的共享本机服务，不分配负例/E01/E02实际运行。

## 当前证据

2026-11-06 11:15:43北京时间，ollama.exe进程及11434监听均为空。前轮日志记录10:43:25关闭服务，发起者和原因未知。现有可执行文件及当前8B本地manifest已核对，不下载、不安装或更新。退出事件和旧PID15264保护基线永久保留。

- 可执行文件：`C:\Users\Administrator\AppData\Local\Programs\Ollama\ollama.exe`，SHA `0a9d42eabc59fdafde8d2d3e7964f6050b31a17b3e3795bfacb367c12df790f4`，36,575,624字节。
- 原生预期版本：`0.32.15`，文件VersionInfo为空；启动后必须用本机GET /api/version验证，当前不能宣称已验证版本。
- 当前模型：`qwen3-8b-uncensored`，manifest/digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`；目录 `C:\Users\Administrator\.ollama\models`。

## 拟执行操作（尚未执行）

1. 再查11434监听和ollama.exe，若已有实例则不启动第二个；按只读核对处理。核验可执行文件和当前模型manifest摘要，以及原保护基线中其他6个进程的精确身份。
2. 对单个子进程设置 `OLLAMA_HOST=127.0.0.1:11434`、`OLLAMA_MODELS=C:\Users\Administrator\.ollama\models`，不持久修改系统环境或产品配置。
3. 用 PowerShell `Start-Process -FilePath 'C:\Users\Administrator\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve' -WindowStyle Hidden -PassThru` 启动一次；工作目录为该exe目录，stdout/stderr分别重定向至本证据根的 `ollama-serve.stdout.log` / `ollama-serve.stderr.log`。不启动桌面升级器，不自动重试。
4. 最多30秒内只读检查该进程PID/FILETIME/exe/父进程/命令摘要、11434所有者、GET /api/version和GET /api/tags中当前别名/digest。不调用generate/chat，不加载或切换其他模型。任何不符保留失败，停止本轮恢复流程。
5. 若符合，另存新的7项保护身份观察，明确新Ollama身份与旧PID差异；旧基线和后续FAIL不覆盖。语音仅官方 `launch.py --status` 读取safe状态字段，不录音、不播放、不重启语音/Brain/ASR。后续负例准备需绑定新的基线再审查，服务恢复本身不等于验收通过。

授权边界：原T2阶段文件明确“无……生产服务操作”；上一份用户授权仅一次round3及一次只读结果复核，均已用完。由于共享Ollama关闭原因未知，本次恢复服务需要一次新的明确许可。这里请求的是上述一个服务启动与只读准入核对，不是模型替换或新用例授权。

Ruling: 不因已有正例PASS或负例零推理而省略环境核对，也不复用不存在的旧PID。代价是现场负例需等新身份记录完成；离线负例准备可继续。
