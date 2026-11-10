# E02 source13外层入口准备：固定检查入口与接口基线

原单wo-ultimaagent-20261101-0021，T2；候选269aca511d88412dbb9c15d23911138469a37aa2，仅当前qwen3-8b-uncensored。E01固定三轮3/3、E03三正例及一负例已通过。E02当前绑定包的557项离线检查和独立准备审查已PASS，本地检查点5e3ac704／镜像bc28b451，tag ultimaagent-t2-e02-source13-binding-prep-20261106；E02/T2实际能力门仍未通过。

外层入口计划已具体化，见docs/plans/jarvis-work-e02-source13-root-entry-plan-20261106.md。证据根data/evidence/jarvis-work-capability/T2/e02-source13-root-entry-20261106。Task1保存23份只读来源绑定，并完成一次原固定run_checks.py --contracts：557个唯一标识全部通过，零失败/错误/跳过，1461依赖和包文件前后无漂移，无重试。原始runner收据和JUnit已逐字/逐标识读回，见verification/fixed-runner-readback.json。这是与B较早named runner独立记账的新固定入口记录，未修改B原收据中“当时固定runner为0”的历史。

静态核对记录了六项接口：当前package_root和旧import_path首项需要显式派生绑定；venv调用角色与实际worker原生身份需要独立观察；保护集合必须使用当前7身份；两次readback和实际reader退出沿用同一275/310/315秒时钟；原生退出须先观察保留句柄已终止再读取退出码；历史metadata仍仅用于模拟transport，不能当作当前服务证明。

下一步Task2只在新E目录内联实现外层RootControls、worker/reader接线及必要只读退出观察适配，复用现有Owned和标准库机制，先行为RED再GREEN。原产品、SDK和B/profile字节冻结；不新增原生进程控制器。Task3完成整包独立准备审查与root处置后，才提出具体的一次零推理profile和一次结果复核申请。现在尚未提供外层代码、实际入口或运行authority。

本次原资料profile、产品CLI、模型、UI/音频、服务操作均0；没有刷新保护进程/11434状态。固定runner为已审查的模拟契约测试，它没有run-stage.py单独安装的Python审计hook；不据此宣称OS/native全局零活动。旧六轮修复、所有失败和耗尽额度原样保留。E02还需当前8B受控三轮与真实联网来源/事实/文件验收，T2、后续阶段和Owner不提前通过。

本地基线tag为ultimaagent-t2-e02-source13-root-entry-baseline-20261106；具体项目/镜像提交与精确读回见verification/task1-local-checkpoint.json。远端push此前被自动审批以blocked by policy拒绝，本次未重试或改通道；本地留档不等于远端同步。
