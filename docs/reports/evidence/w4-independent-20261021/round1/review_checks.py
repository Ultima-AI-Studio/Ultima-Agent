from __future__ import annotations
import hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(r'H:\UltimaAI\UltimaAgent')
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from src.brain.intent import parse_task_status_intent
from src.brain.queue_source import read_queue_status
from src.brain.reporter import respond_to_text
from tasks.queue_engine import QueueStorage, QueuePlanner, QueueState, StateMachine

def write(name, text):
    with (OUT/name).open('x', encoding='utf-8') as f: f.write(text)

def run(name, args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT))
    p = subprocess.run([sys.executable, '-B', '-X', 'utf8', *args], cwd=ROOT,
        env=env, capture_output=True, text=True, encoding='utf-8', timeout=180,
        creationflags=subprocess.CREATE_NO_WINDOW)
    write(name+'.txt', p.stdout+'\n'+p.stderr)
    return {'name':name, 'returncode':p.returncode}

def hashes():
    paths = list((ROOT/'src/brain').rglob('*.py')) + list((ROOT/'tasks/queue_engine').glob('*.py'))
    paths += [ROOT/'tasks/tasks.json']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

before = hashes()
runs = [run('developer-text-tests', ['-m','unittest','discover','-s','src/brain/tests','-p','test_*.py','-v']),
        run('frozen-baseline-before', ['src/brain/tests/verify_frozen_baseline.py']),
        run('queue-engine-independent-regression', ['-m','unittest','discover','-s','tasks/tests','-p','test_*.py','-v'])]
checks=[]
def check(name, expected, actual):
    checks.append({'name':name,'passed':expected==actual,'expected':expected,'actual':actual})

positive = ['请查询任务状态','麻烦查看任务进展','帮忙看看任务完成情况','报告一下任务执行情况','告诉我队列状态',
 '任务进度怎么样','任务执行得怎么样了','看一下任务队列','查下任务状态','查一查任务进度',
 '请汇报所有任务的进展','现在任务什么情况','有哪些任务失败了','帮我看哪些任务被冻结','请查看队列中排队情况',
 '能帮忙查查任务状态吗','我需要查看任务执行进度','请告诉我哪些任务卡住了','帮忙看一下所有任务的情况','查询队列目前情况']
positive_results=[{'text':s,'matched':parse_task_status_intent(s).matched} for s in positive]
rate=sum(x['matched'] for x in positive_results)/len(positive_results)
check('独立明确查询识别率≥90%',True, rate>=.9)
negative=['先不查任务状态','不需要查任务状态','我看过任务状态了','暂时不查任务状态','我已经查看任务进度了',
 '任务状态我看过了','无需查询任务状态','别查看任务状态','不要汇报任务执行情况','任务进度正常',
 '这段日志写着查任务状态','他说查任务状态','“查任务状态”','请解释“查任务状态”这句话','我昨天看了任务状态',
 '我们讨论过查询任务状态','查任务状态这个功能以后再做','不必查看任务队列']
for s in negative:
    calls=[]
    with patch('src.brain.reporter.read_queue_status', side_effect=lambda root: calls.append(str(root)) or read_queue_status(root)):
        response=respond_to_text(s, queue_root=OUT/'nonexistent-probe')
    check('无明确指令不读库：'+s, {'matched':False,'handled':False,'reads':0},
          {'matched':parse_task_status_intent(s).matched,'handled':response.handled,'reads':len(calls)})

def record(task_id):
    return dict(task_id=task_id,state='QUEUED',priority=50,dependsOn=[],parallelGroup=None,
        fileDomain=[str(ROOT/'src/brain')],reasoningEffort='high',created_at='2026-10-20T00:00:00+00:00',
        updated_at='2026-10-20T00:00:00+00:00',terminal_reason=None,card_path=f'cards/{task_id}/task.md')
def add(storage, task_id):
    card=storage.cards_dir/task_id/'task.md'; card.parent.mkdir(parents=True)
    card.write_text(f'# 审查隔离任务\n- **标题**：独立审查 {task_id}\n',encoding='utf-8')
    QueuePlanner(storage).enqueue(record(task_id))
def move(storage, task_id, states):
    items=storage.load_tasks(); i=next(i for i,r in enumerate(items) if r['task_id']==task_id)
    for state in states:
        items[i],_=StateMachine(storage).transition(items[i],state,
            actor='auditor' if state==QueueState.COMPLETED else 'developer',
            reason='独立审查迁移',audit_passed=state==QueueState.COMPLETED)
    storage.save_tasks(items)
completed=(QueueState.EXECUTING,QueueState.SELF_CHECK,QueueState.AUDIT,QueueState.COMPLETED)
with tempfile.TemporaryDirectory(prefix='ultima-w4-') as tmp:
    base=Path(tmp); storage=QueueStorage(base/'real'); storage.ensure_layout()
    for n in range(20):
        tid=f'holdout-{n:02}'; add(storage,tid)
        move(storage,tid,completed if n<19 else (QueueState.EXECUTING,QueueState.FAILED))
    snapshot=read_queue_status(storage.root)
    check('真实独立库20项19完成1失败',[20,19,1,1],
        [snapshot.total,snapshot.counts.get('COMPLETED'),snapshot.counts.get('FAILED'),len(snapshot.anomalies)])
    response=respond_to_text('查询任务状态',queue_root=storage.root)
    check('异常优先合格项聚合',True,response.text.startswith('当前共 20 个任务，有 1 个异常。') and
        'holdout-19' in response.text and all(f'holdout-{n:02}' not in response.text for n in range(19)))
    write('real-20-1-output.txt',response.text)
    for tid in ['holdout-00','holdout-19']:
        result=respond_to_text('查任务状态',queue_root=storage.root,detail_task_id=tid)
        check('下钻 '+tid,True,result.ok and tid in result.text)
    for tid in ['../tasks.json',r'..\tasks.json',r'C:\secret','/etc/passwd','a/b','a:b']:
        with patch('src.brain.reporter.read_queue_status',side_effect=AssertionError('unexpected read')):
            r=respond_to_text('查任务状态',queue_root=storage.root,detail_task_id=tid)
        check('路径ID拒绝 '+tid,True,not r.ok and '非法' in r.text)
    missing=respond_to_text('查任务状态',queue_root=storage.root,detail_task_id='absent')
    check('未知ID明确拒绝',True,not missing.ok and '未找到' in missing.text)
    move(storage,'holdout-19',(QueueState.QUEUED,*completed))
    s=read_queue_status(storage.root)
    history=(storage.events_dir/'holdout-19.jsonl').read_text(encoding='utf-8')
    check('历史失败已修复无残留',True,s.ok and not s.anomalies and 'FAILED' in history and s.counts['COMPLETED']==20)
    # Eight-state matrix independent persisted schema, plus real transitions above.
    matrix=QueueStorage(base/'matrix'); matrix.ensure_layout(); rows=[]
    for state in QueueState:
        tid='matrix-'+state.value.lower(); add(matrix,tid)
        row=record(tid); row['state']=state.value; rows.append(row)
    matrix.index_path.write_text(json.dumps(rows),encoding='utf-8')
    s=read_queue_status(matrix.root)
    check('八态当前计数各1', {st.value:1 for st in QueueState},s.counts)
    check('仅失败冻结为当前异常',['BLOCKED','FAILED'], sorted(t.state for t in s.anomalies))
    for label,payload in [('invalid-json','{bad'),('object','{}'),('null-item','[null]'),
            ('missing-field',json.dumps([{k:v for k,v in rows[0].items() if k!='state'}]))]:
        matrix.index_path.write_text(payload,encoding='utf-8'); s=read_queue_status(matrix.root)
        check('损坏失败关闭 '+label,True,not s.ok and s.total is None and not s.counts)
    for field,value in [('state','UNKNOWN'),('priority',True),('priority',101),('terminal_reason',33),
            ('created_at','broken'),('updated_at','1990-01-01T00:00:00+00:00'),('card_path','../escape.md'),('task_id','../escape')]:
        row=dict(rows[0]); row[field]=value; matrix.index_path.write_text(json.dumps([row]),encoding='utf-8')
        s=read_queue_status(matrix.root)
        check('非法字段失败关闭 '+field+'='+str(value),True,not s.ok and s.total is None and not s.counts)
    s=read_queue_status(base/'missing')
    check('缺失库无创建',True,not s.ok and not (base/'missing').exists())
    def tree(path):
        return sorted(str(p.relative_to(path)) + ('/' if p.is_dir() else ':'+hashlib.sha256(p.read_bytes()).hexdigest()) for p in path.rglob('*'))
    for label,payload in [('empty','[]'),('corrupt','{broken')]:
        r=base/label;r.mkdir(); (r/'tasks.json').write_text(payload,encoding='utf-8'); pre=tree(r)
        result=read_queue_status(r); post=tree(r)
        check('不完整库只读无目录创建 '+label,pre,post)

runs.append(run('frozen-baseline-after',['src/brain/tests/verify_frozen_baseline.py']))
after=hashes();check('源码与生产索引哈希不变',before,after)
result={'runs':runs,'positive_holdout':positive_results,'positive_rate':rate,
        'checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks)}
write('independent-results.json',json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'runs':runs,'checks_passed':result['passed'],'checks_failed':result['failed'],
    'positive_rate':rate,'failures':[c for c in checks if not c['passed']]},ensure_ascii=False,indent=2))
