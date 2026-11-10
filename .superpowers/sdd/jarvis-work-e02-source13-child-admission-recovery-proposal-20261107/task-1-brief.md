## Task 1: 子进程准入最小修复及离线验证

在新目录e02-source13-child-admission-20261107-r1保留原输入和运行源码复制基线；先用实际admit调用链的离线回归证明child触发额外进程快照，再拆分native-only子端核验与父端完整核验。覆盖7身份/parent/命令漂移、过期proof、clearance消费、未知后代与清理失败；原harness回归及入口检查必须通过。产品与共享P4/P1保持原字节。

