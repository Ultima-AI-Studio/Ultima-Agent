import hashlib,json
from pathlib import Path
R=Path('H:/UltimaAI/UltimaAgent');O=Path(__file__).parent
data={}
paths=['logs/maintenance/w1-restart-20261021/before.json','logs/maintenance/w1-restart-20261021/boot-check-20261021T035506862801Z.json','logs/maintenance/w1-restart-20261021/post-reboot-desktop-processes.json','logs/w1-host-resume-20261021T024845Z/after/root-post-reboot-process-state.json','src/host-shell/README.md']
for rel in paths:
 p=R/rel;t=O/'support'/rel;t.parent.mkdir(parents=True,exist_ok=True)
 with t.open('xb') as f:f.write(p.read_bytes())
 data[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((R/'logs/w1-delivered-selfcheck-verified-path-positive-20261021T0324/entry-result.json').read_text())['source_manifest']
new=json.loads((O/'result.json').read_text(encoding='utf-8'))['source_manifest']
data['third_round_implementation_source_equal']=all(new.get(p)==h for p,h in old.items())
with (O/'support-manifest.json').open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
print(data['third_round_implementation_source_equal'])
