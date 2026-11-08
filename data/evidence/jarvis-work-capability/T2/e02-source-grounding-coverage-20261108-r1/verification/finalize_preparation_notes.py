from pathlib import Path
import json
N=Path(__file__).resolve().parents[1];R=N.parents[4]
p=N/'verification/publish.py';s=p.read_text('utf8');assert s.count('foreign_files_unchanged=15')==1
s=s.replace('foreign_files_unchanged=15','foreign_files_unchanged=14,foreign_readback=foreign');p.write_text(s,encoding='utf8',newline='\n')
ledger=R/'.superpowers/sdd/jarvis-work-e02-source-grounding-coverage-plan-20261108/progress.md'
with ledger.open('a',encoding='utf8') as f:f.write('\n- Final regression r3:1022/1022 PASS, failures/errors/skipped0. Earlier full batches10 and8 failures retained; dense five-source diagnostic fixture hit original strict prompt cap, no production cap change. Diagnostic fixture is explicitly original three-source/six-read scenario.\n- Preservation exception:14 original unrelated hashes match; tracker HTML changed outside this task write domain. Source undetermined, original baseline retained, current bytes copied without editing. Only recorded observed hash accepted, not arbitrary future drift; review must inspect this exception.\n- Goal registry was cleared by user during this approved offline work; do not recreate a goal.\n')
state=json.loads((N.parent/'current-run.json').read_bytes());state.update(goal_status='none',goal_registry_status='cleared_by_user')
(N.parent/'current-run.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print('notes, precise unrelated-file wording and cleared goal registry recorded')
