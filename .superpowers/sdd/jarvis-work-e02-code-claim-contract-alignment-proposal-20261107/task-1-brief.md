## Task 1: 新隔离候选与离线准备

- 从a0d21eb新建隔离候选，不改旧候选或旧证据。写域限研究schema/可信卡片投影、generation和独立replay及必要测试。
- 先写RED：匹配同一证据ID但claim省略operation、只写近似名称/不合法前后边界、选择其他证据operation；证明当前schema接受而原writer拒绝。另有合法代码事实、非code事实、无效/过长operation、空卡片、跨请求和pending第三页用例。
- 最小实现配对契约。真实SDK mock transport必须核对format/strict/sampler/phase一致；错误claim在writer派发前拒绝且无文件/effect，合法三来源链路完成写入、ACK、SHA读回和独立重放。
- 对改写自报hash/native entity后的schema、operation映射、phase伪造做重放负例。保留所有原诊断与事实门；测试故障注入只能用于检验失败路径，不能进入产品路径。
- 最多6页48卡/5来源核对原32768/49152字节门、输出及次数预算；超限失败关闭，不静默截断约束。列出仍未通过或尚未覆盖的契约，不宣布实际研究成功。
- 运行受影响离线回归，提交/tag，重绑候选和输入哈希，必要独立准备审查；旧失败及原HTTP/junction排除保留。保护基线使用既有七角色强校验，任何再次漂移先只读核对，不控制服务。

