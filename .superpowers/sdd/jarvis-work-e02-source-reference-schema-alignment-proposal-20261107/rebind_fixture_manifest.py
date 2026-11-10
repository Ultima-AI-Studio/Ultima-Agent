from pathlib import Path
import json,hashlib
R=Path('H:/UltimaAI/UltimaAgent');N=R/'data/evidence/jarvis-work-capability/T2/e02-source-reference-schema-20261107-r1'
L=R/'.superpowers/sdd/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((N/'offline/bindings-red-bound/receipt.json').read_bytes())['sources'][str(N/'inputs/input-manifest.json')]
new=sha(N/'inputs/input-manifest.json')
p=N/'harness/test_adapter.py';text=p.read_text('utf8');assert text.count(old)==1
p.write_text(text.replace(old,new),encoding='utf8')
p=N/'harness/manifest.json';value=json.loads(p.read_bytes());value['files']={name:sha(N/'harness'/name) for name in value['files']}
p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
with (L/'progress.md').open('a',encoding='utf8') as f:
    f.write('\nTask1: harness base-a11fail/68pass and recovery5fail/14pass, all traced to documents() fixture retaining the pre-baseline-update input-manifest SHA. Runtime correctly refused it before intended tests. Rebind that one fixture literal, keep every runtime function/assertion and all failed receipts, rerun all238 against final harness bytes; base-b earlier140pass is not counted under final hashes.\n')
with (N/'preparation-report.md').open('a',encoding='utf8') as f:
    f.write('\n执行框架首次回归另有16个失败，均因documents()夹具保留更新保护基线前的输入manifest SHA，运行时在正确的候选/来源门提前拒绝。仅重绑该夹具常量，断言和运行函数不变，最终238项按新哈希复测；旧失败与旧哈希通过记录均保留且不计当前通过数。\n')
print('Rebound single fixture manifest literal; runtime unchanged')
