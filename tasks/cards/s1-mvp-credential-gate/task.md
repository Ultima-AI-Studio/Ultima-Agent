# 任务卡：s1-mvp-credential-gate

- **task_id**：s1-mvp-credential-gate
- **stage**：S1（阶段一 v1.0）
- **标题**：L8 凭证中心 + 受控执行（状态只报告/操作需授权/越界拦截）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 MVP 的安全边界（越界拦截 100%）

## goal

实现 L8 凭证中心 + 受控执行：状态只报告（只读安全）、操作需授权（写操作凭证门）、越界拦截（非授权操作拒绝 100%）。禁止：不绕过凭证门、不静默授权、不报告越界为成功（诚实边界 100%）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 状态只报告（读操作无副作用）
- [x] ACCEPT: 写操作需授权（凭证闭环测试）
- [x] ACCEPT: 越界拦截率 100%（越界用例全拒）
- [x] ACCEPT: 不假装成功（拒绝时如实反馈"未授权"）

## dependsOn[]

- s1-mvp-queue-adjust（T2 写操作）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\security\`（凭证中心）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-mvp-credential-gate\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- ultra（安全边界核心，跨技能：安全+架构，需评审背书）

## category + skill

- category: security · skill: eng.security（安全工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: 主脑直做验收（L8 凭证中心此前批次已落地，本卡补登记验收）；实现 src/brain/guardrails/credentials.py（DPAPI 加密，当前用户级，内存与磁盘不明文）
- stdoutText: 凭证闭环 + 越界用例 PASS（test_credential_s3.py 全绿；DPAPI 加解密 + 高危征询路径实测）
- evidence: src/brain/guardrails/tests/test_credential_s3.py + 凭证中心实现
- acceptance 逐项核对: 4/4 全绿（状态只报告/写授权/越界拦截 100%/诚实反馈）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| CG-01 状态只报告 | 读操作无副作用 | 只读安全 | 用例输出 |
| CG-02 凭证门 | 写操作需授权 | 凭证闭环 | 凭证测试 |
| CG-03 越界拦截 | 非授权操作拒绝 100% | 全拒 | 越界用例 |
| CG-04 诚实反馈 | 拒绝时如实反馈"未授权" | 不假装成功 | 场景实测 |
