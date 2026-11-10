"""Freeze offline preparation for one fresh independent review, no release."""
from pathlib import Path
import ast,datetime as dt,hashlib,json
N=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def member_name(path):return path.relative_to(N).as_posix()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
assert not (N/'actual').exists() and not (N/'release').exists()
entry=load(N/'offline/entry-final/receipt.json')
assert entry['exit_code']==0 and entry['result']['tests']==25 and not entry['result']['denied']
for name,digest in entry['sources'].items():assert sha(Path(name))==digest,name
corpus=load(N.parent/'source6-native-reference/controlled-corpus-inputs/corpus.json')
proposal=f'''# 当前8B真实受控研究首例执行提案

仅在本包独立准备审查PASS、且用户明确分配一例真实8B研究及一次独立结果复核后生效。此前零推理授权已经用完；本文件不签发新运行权。

## 目标与输入

原工单wo-ultimaagent-20261101-0021 / T2 / E02-controlled-1。产品候选269aca511d88412dbb9c15d23911138469a37aa2；仅qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。沿用原题和四份完整受控来源，不改默认模型。

原题：{corpus['query']}

固定来源：
'''+''.join('- '+s['final_url']+'\n' for s in corpus['sources'])+f'''
corpus SHA256：9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002。

## 唯一拟执行命令

```powershell
& 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Scripts\\python.exe' -I -B -X utf8 '{N / 'code/entry.py'}'
```

新授权到达后才创建release/user-allocation.json，绑定本manifest、独审报告、新问题编号和原答复；执行前120秒内生成，实际例1、结果独审1、retry0。entry先独占写consumed.json，再创建原RootInvocation，完成实时七身份与模型摘要准入。缺授权、缺准备PASS、漂移或重复消费均不进入产品调用。harness-approval只是准备审查记录，不能替代新用户分配。

入口只创建隔离测试server与一例产品CLI，真实模型调用既有本地Ollama；不启动/停止生产服务，不操作UI、音频或麦克风。隔离server的固定端口18799占用时拒绝，不换端口重试。只管理本例新建进程，七个保护身份必须保持。准备阶段尚未重新查询生产进程，未来以执行入口的实时校验为准。

## 原预算与写域

CLI1、search1、GET4、inspect6、write1、ACK1、native_POST8；service260秒、client300秒；从同一父时钟计算work275 / cleanup310 / seal315秒。父时钟先于preflight和authority，未重置。资料搜索/GET使用原受控全文夹具；模型transport使用真实SDK/HTTPX，绝不使用Mock回答。运行可能沿原SDK SSRF分支对raw.githubusercontent.com进行DNS查询；本例不是另一次真实联网来源验收。

新写域仅本目录下release、controller-authority、native-preflight、controller-ledger.json、actual/E02-controlled-1及随后独立结果review。产品输出应为actual/E02-controlled-1/outputs/<task-id>/research.md。所有旧失败、零推理包和冻结产品保持原字节。失败封存后结束，不重跑。

## 判定与限制

必须拿到真实产品首结果、完整SDK packet、原四来源/引用绑定、一次写入与ACK、文件哈希及两次读回、Owned清理和同父时钟终态。机械通过仍只是PENDING_ROOT_INDEPENDENT_REVIEW；独立事实复核逐条检查research.md陈述与具体来源、Jarvis.ceo与OpenJarvis归属是否区分、有无无依据内容。不能只凭模型自评、测试或文件存在宣布通过。

该例至多获得受控研究1/3；E02完整门仍需同候选连续3例及另一次真实联网至少3条去重来源。E01/E03已通过记录不挪用为E02信用。T2、后续阶段及Owner保持原门。

已完成离线检查269项：14输入、219原harness、10身份/transport、1原始SDK产物只读复放、25入口；原71测试函数全部保留。测试中的Python SSRF/DNS与固定UUID4只用于离线测试，实际child不继承。生产随机ID曾在一个离线随机夹具触发PII扫描，真实运行的行为仍待实证。

远端push仍因此前自动审批blocked by policy未同步；本次不重试绕行。准备包通过后先做本地提交/tag和UltimaDocs逐字镜像，再申请新的实跑额度。
'''
with (N/'execution-proposal.md').open('x',encoding='utf8') as f:f.write(proposal)
members=set()
for sub in ('inputs','harness','tests'):
    members.update(p for p in (N/sub).rglob('*') if p.is_file())
members.update(p for p in (N/'code').iterdir() if p.is_file())
members.update(p for p in (N/'verification').iterdir() if p.is_file() and p.suffix in ('.py','.diff'))
members.add(N/'execution-proposal.md')
for run in (N/'offline').iterdir():
    members.update(p for p in run.iterdir() if p.is_file())
    if (run/'snapshot').exists():members.update(p for p in (run/'snapshot').iterdir() if p.is_file())
for run in (N/'code').glob('harness-preparation-*'):
    members.update(p for p in run.iterdir() if p.is_file())
    for sub in ('harness','harness-source'):members.update(p for p in (run/sub).iterdir() if p.is_file())
manifest=dict(kind='SOURCE13_REAL_CONTROLLED_PREPARATION',candidate='269aca511d88412dbb9c15d23911138469a37aa2',
    model='qwen3-8b-uncensored',model_digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330',actual_released=False,
    prepared_utc=dt.datetime.now(dt.timezone.utc).isoformat(),test_count=269,
    files={member_name(p):sha(p) for p in sorted(members)})
save(N/'manifest.json',manifest)
(N/'review').mkdir(exist_ok=False)
print(json.dumps(dict(manifest_sha256=sha(N/'manifest.json'),members=len(members),tests=269,actual_released=False)))
