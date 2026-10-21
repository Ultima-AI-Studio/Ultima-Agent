import hashlib,json
from pathlib import Path
ROOT=Path(r'H:\UltimaAI\UltimaAgent');OUT=Path(__file__).resolve().parent
OLD=ROOT/'docs/reports/evidence/text-loop-development-20261021/round1/source'
raw=(OUT/'result.json').read_bytes()
with (OUT/'preliminary-byte-prefix-result.json').open('xb') as f:f.write(raw)
result=json.loads(raw);append=json.loads((OUT/'card-append-check.json').read_text())
for tid,check in append.items():
    old=(OLD/'tasks/cards'/tid/'task.md').read_bytes();new=(ROOT/'tasks/cards'/tid/'task.md').read_bytes()
    check['old_crlf_count']=old.count(b'\r\n');check['new_crlf_count']=new.count(b'\r\n')
    check['old_lf_count']=old.count(b'\n');check['new_lf_count']=new.count(b'\n')
result['cards_append_only_readback']=append
result['conditions']['cards_append_only']=all(x['normalized_text_prefix'] for x in append.values())
result['preliminary_check_note']='初检以字节前缀核对任务卡，两卡换行格式改变导致未通过；正文diff复核均仅追加修复段落。初检原样保存在preliminary-byte-prefix-result.json。'
dev=ROOT/'logs/text-loop-w4-repair-20261021';seal=json.loads((dev/'evidence-sha256.json').read_text())
bad=[n for n,h in seal.items() if hashlib.sha256((dev/n).read_bytes()).hexdigest()!=h]
result['developer_evidence_seal']={'files':len(seal),'mismatches':bad}
result['conditions']['developer_evidence_seal_valid']=not bad
result['verdict']='PASS' if all(result['conditions'].values()) else 'REVISE'
(OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'verdict':result['verdict'],'conditions':result['conditions'],'card_readback':append,'developer_seal':result['developer_evidence_seal']},ensure_ascii=False,indent=2))
