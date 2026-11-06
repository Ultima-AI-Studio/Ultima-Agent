from pathlib import Path
import json
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
N=T/'e02-source13-native-metadata-20261107-r1'
candidate=json.loads((N/'inputs/candidate-transition.json').read_bytes())['candidate']
query=json.loads((T/'source6-native-reference/controlled-corpus-inputs/corpus.json').read_bytes())['query']
report=f'''# E02原生metadata严格兼容：新候选准备

原工单wo-ultimaagent-20261101-0021 / T2。用户call_3471155e77c74b8db30c1278112c74d2已授权最小产品补修、必要独立准备审查，审查PASS后单例当前8B研究及一次只读独立结果复核。失败不重试；本文件不是运行分配。

新候选{candidate}，基于269aca511d88412dbb9c15d23911138469a37aa2；托管工作区C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-metadata/UltimaAgent。旧候选与两次真实失败7530ef7f...及81c77cfd...不变。旧E01三轮与E03三正一负的信用仍属旧候选；新候选没有这些实际回归信用。

## 产品最小修复与依据

唯一已存在产品源文件变更为work_research.checked_native_identity：capabilities允许省略；出现时必须为list且每个成员严格为str。未知模型字段、重复JSON键、错误字段类型、版本0.32.15、当前8B名称/摘要、重复目标和本地manifest绑定全部保持。没有剥除真实模型字段、替换回答或改动模型/默认配置。既有字段大小边界保持；不擅自为新字段增加语义枚举或将其用作工具授权。

测试资料来自上一例保存的root native metadata GET解析结果，fixture只保存version/tags语义值；保留原root proof文件和SHA，不称其为产品自身GET的原始HTTP字节。保存结果包含六个模型的capabilities数组；这里只读模型清单，不运行其中14B。安装的ollama/_types.py ListResponse未声明capabilities，ShowResponse声明Optional[List[str]]；该补修的直接依据是已保存原生响应，而非声称ListResponse规范已包括它。

新工作区四个旧运行依赖不在原Git提交中：Jarvis persona、agent_tools_ultima.py及两份旧测试。已按原57文件清单从冻结工作区逐字复制并加入新候选，使此候选可还原；四文件SHA与旧运行一致，不是新增实现。新清单59来源文件，1547输入绑定，原SDK/解释器/模型manifest/语料/保护基线完整。

## 离线验证与失败保留

保存响应有效RED：6失败37通过，包括原生capabilities被拒；首次缺少persona导致collection失败不计RED。产品GREEN501：metadata43、原研究178（68+110）、navigation90、transport104、交付/上下文86。原test_http_work_legacy_and_cli会建立本地HTTP服务，test_reparse_rejected会启动junction命令，两项未在本离线范围执行，不计通过。CLI参数与原work transport单元覆盖仍通过。

测试守卫沿用已接受的冷导入审计，离线SSRF改用原Python实现、合成DNS并保持localhost→127.0.0.1，避免Rust DNS绕过Python audit；不改变真实产品/actual harness的SSRF或native transport。首次guard缺少Python fallback、DNS fixture与localhost语义冲突、研究整组90秒超时以及错误diagnostic断言均完整保留，不算通过。初次Rust路径OS包未测量，保持null，不宣称从未发DNS。后续每组独立90秒、无模型调用；没有延长实际时限。

辅助harness保留上一轮父/子准入拆分，只重绑候选和新增candidate_environment把共享P1返回的旧PYTHONPATH指向新候选。P4/P1源文件和Owned/cleanup/transport保持。新环境测试RED（缺失helper）→GREEN；旧authority测试fixture首次仍绑定旧candidate导致11失败，已仅更换该fixture身份/hash，拒绝断言未变。全部原236 harness案例保留；输入14、入口26、边界11，在最终readback列举成功回执，总788项。最终数量以封存readback为准。

## Review Focus

1. capabilities类型/unknown keys/版本/摘要/重复模型拒绝是否保持，旧字段行为是否越界。
2. root GET解析结果与产品GET原始体的归因边界是否如实，旧失败是否保留。
3. 新候选所有导入/子进程cwd/PYTHONPATH/59来源与1547输入绑定是否完整，四依赖是否逐字一致；新候选不得借用旧E01/E03信用。
4. 共享P4/P1、父端完整身份和子端原生准入、原生transport、原275/310/315秒、七保护身份、未知后代cleanup是否保留。
5. 单例与结果独审只条件释放一次，原题/四来源/8B不变，事实与文件验收不能由离线通过替代。

当前实际运行与模型调用0。尚无新候选research.md或事实质量信用。E02/T2仍NOT_PASSED。用户已授权的整条链在准备PASS后直接推进，无需重复询问。
'''
proposal=f'''# 已授权的原生metadata兼容候选单例

原工单wo-ultimaagent-20261101-0021 / T2；新候选{candidate}。用户call_3471155e77c74b8db30c1278112c74d2授权“补修、独审，通过后单例研究并复核”。本提案绑定该完整范围；仅准备独审PASS、本地checkpoint/tag与镜像读回后，签发一次TTL120秒分配。实际例1、结果独审1、retry0。

只用qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题：{query}

四份完整控制语料保持corpus SHA256 9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002。浏览器search/GET仅原受控fixture，模型通过原SDK/HTTPX真实调用，不能替换回答或删除metadata字段。原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8，service260/client300/rootwork275/cleanup310/seal315秒。原正常SSRF分支可能对raw.githubusercontent.com作受限DNS。

唯一入口：
```powershell
& 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Scripts\\python.exe' -I -B -X utf8 '{N/'code/entry.py'}'
```

由封存root wrapper创建一次release并调用入口，旧分配不复用。写域仅本根release/controller-authority/controller-ledger.json/native-preflight/actual/E02-controlled-1和后续review/verification。失败保存首结果，不重试。只管理本例已核验身份的新进程；七个生产保护身份/端口及未知后代拒绝清理门保持。无UI、音频或生产服务操作，无需暂停键鼠。

实际首结果、SDK packet、受控来源及逐事实引用、research.md写入/ACK/两次外部读回、原时限与cleanup均满足并经独立复核，才登记本新候选一例信用。最多为新候选受控1/3，后续同候选连续两例、真实联网去重来源及E01/E03新候选回归仍有原门；本授权不包含那些现场例。

两次旧失败与旧候选信用保持。应用native POST与实际原生推理计数区分，未测量计数为null。远端同步仍被先前自动审批blocked by policy阻断，本轮不重试或绕行。
'''
for name,text in [('preparation-report.md',report),('execution-proposal.md',proposal)]:
    with (N/name).open('x',encoding='utf8',newline='\n') as f:f.write(text)
with (R/'.superpowers/sdd/jarvis-work-e02-source13-native-metadata-compat-proposal-20261107/progress.md').open('a',encoding='utf8') as f:
    f.write('\nTask 1: product501 offline PASS, candidate '+candidate+' committed/tagged, seven exact files (three fix/test/fixture files and four unchanged formerly external frozen dependencies). No production mutation. Authority fixture stale candidate produced 11 rejected positives; only fixture identity/hash rebinding corrected, rejection tests retained.\n')
print('Preparation documents written; independent review still pending')
