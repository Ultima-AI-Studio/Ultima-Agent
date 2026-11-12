# 任务卡：s3-websearch-upgrade
- **task_id**：s3-websearch-upgrade
- **标题**：检索增强（多引擎编排 + 来源标记 + SSRF 防护）
- **优先级**：60（P2）
- **reasoningEffort**：low
- **category**：exec　**skill**：engineering
- **依赖**：s3-bus-kernel
- **登记核验**：已查注册表，ultima_web_search 已存在，本单为增强；依据 docs/research/agent-capability-notes-scaffold-20261026.md Agent-Reach §④、OpenJarvis §④

## goal
检索增强 M14：
1. 多引擎上游编排与结果结构化、来源标记；
2. 降级标记（引擎失败如实降级不假装成功）；
3. 出站 SSRF/白名单防护（内网保留地址与元数据地址防护、域名/协议白名单）。

**禁止**：
- 禁止访问内网/元数据地址；
- 禁止伪造检索结果来源；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：多引擎编排可用，结果带来源标记
- [ ] ACCEPT-2：引擎失败降级标记生效
- [ ] ACCEPT-3：SSRF 防护拦截内网/元数据请求
- [ ] ACCEPT-4：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：检索增强（P2） |
