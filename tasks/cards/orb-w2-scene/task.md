# 任务卡：orb-w2-scene

- **task_id**：orb-w2-scene
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：Three.js 场景 + raymarching 球体
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 渲染场景实现

## goal

在 WebView2 画布中建立 Three.js 场景，实现 raymarching SDF sphere（球体 + 噪声形变）。参考 @crazygl/hero-liquid-metal-orb（Apache-2.0，保留版权声明）。禁止：不实现状态机（W3）、不实现交互（W4）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: Three.js 场景建立，WebGL2 渲染
- [ ] ACCEPT: raymarching SDF sphere 渲染正确
- [ ] ACCEPT: 噪声形变（deformAmount/boilSpeed）生效

## dependsOn[]

- orb-w1-webview2（画布就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\web\`（渲染代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w2-scene\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（raymarching shader）

## category + skill

- category: orb-render · skill: eng.webgl（WebGL 工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: 待回填
- stdoutText: 待回填
- evidence: 待回填
- acceptance 逐项核对: 待回填

## retryCount

- 0

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| U-01 场景 | Three.js 场景 + WebGL2 | 场景建立 | 渲染截图 |
| U-02 球体 | raymarching SDF sphere | 球体渲染正确 | 渲染截图 |
| U-03 形变 | 噪声形变生效 | 有机流动感 | 渲染截图 |
