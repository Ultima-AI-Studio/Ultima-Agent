# 任务卡：orb-w2-material

- **task_id**：orb-w2-material
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：毒液材质参数
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 材质参数实现

## goal

按方案 §4.2 毒液材质参数表实现：metallic 0.85-1.0、fresnelStrength 高、rimColor/sunColor 冷蓝灰/暖白、三层高频噪声（pow3/5/7）、环境反射（程序化 studio HDRI）、透明背景。禁止：不实现状态切换（W3）、不实现拉伸巡游（W5）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: metallic/fresnel/rim/sun 参数生效
- [ ] ACCEPT: 三层噪声（pow3/5/7）产生揉皱铝箔+湿度不均质感
- [ ] ACCEPT: 油亮反射 + 边缘光明显（深色桌面可见）

## dependsOn[]

- orb-w2-scene（场景就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\web\`（shader 代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w2-material\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（材质 shader 调参）

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
| U-01 材质 | metallic/fresnel/rim/sun | 参数生效 | 渲染截图 |
| U-02 噪声 | 三层高频噪声 pow3/5/7 | 揉皱铝箔质感 | 渲染截图 |
| U-03 反射 | 程序化 HDRI + 边缘光 | 油亮反射可见 | 深色桌面截图 |
