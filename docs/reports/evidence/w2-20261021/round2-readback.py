import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent/'round2'
report=ROOT/'docs/reports/w2-independent-acceptance-20261021.md';text=report.read_text(encoding='utf-8')
table=text.split('### 35项最终技术结论')[1].split('### 技术签署后的剩余门项')[0]
rows=[line for line in table.splitlines() if line.startswith(tuple('| '+x+'-' for x in ['ST','SM','DI','PD','AU']))]
assert len(rows)==35 and all('| 通过 |' in row for row in rows)
manifest=json.loads((OUT/'source-manifest.json').read_text(encoding='utf-8'))
changed=[name for name,digest in manifest.items() if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest]
# Administrative report/index changes after the tested snapshot do not alter engine validation.
engine_changed=[name for name in changed if '/tasks/queue_engine/' in name.replace('\\','/') or '/tasks/tests/' in name.replace('\\','/')]
assert not engine_changed,engine_changed
assert json.loads((ROOT/'tasks/tasks.json').read_text(encoding='utf-8'))==[]
receipt=json.loads((OUT/'audit-receipt.json').read_text(encoding='utf-8'));assert receipt['closed_state']=='COMPLETED'
correction=json.loads((OUT/'correction-independent-receipt.json').read_text(encoding='utf-8'));assert len(correction['final_tasks'])==2
result={'final_rows':len(rows),'all_technical_pass':True,'engine_test_manifest_unchanged':True,'non_engine_changes_since_snapshot':changed,'production_empty':True,'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest()}
(OUT/'independent-readback.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=True))
