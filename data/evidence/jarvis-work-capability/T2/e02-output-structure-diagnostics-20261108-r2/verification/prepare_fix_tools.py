"""Adapt only the bounded closure's candidate and evidence coordinates."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parents[1];P=N.parent/'e02-output-structure-diagnostics-20261108-r1'
old='jarvis-e02-output-structure/UltimaAgent';new='jarvis-e02-output-structure-r2/UltimaAgent'
parent='47ac3a464ca15e01311d5739eda53b2a32d8783c'
for name in ('prepare_package.py','closeout.py','publish.py','read_protected.ps1'):
    text=(P/'verification'/name).read_text('utf8').replace(old,new)
    text=text.replace('ultimaagent-e02-output-structure-ready-20261108','ultimaagent-e02-output-structure-ready-20261108-r2')
    text=text.replace('ultimaagent-e02-output-structure-candidate-20261108','ultimaagent-e02-output-structure-candidate-20261108-r2')
    text=text.replace('jarvis-work-t2-e02-output-structure-diagnostics-preparation-20261108.md','jarvis-work-t2-e02-output-structure-diagnostics-preparation-20261108-r2.md')
    text=text.replace("git(C,'rev-parse','HEAD^').decode().strip()==BASE", "git(C,'rev-parse','HEAD^').decode().strip()=="+repr(parent))
    text=text.replace('candidate=head,parent=BASE,','candidate=head,parent='+repr(parent)+',')
    text=text.replace('父 `{BASE}`。','父 `'+parent+'`，原基线 `{BASE}`。')
    text=text.replace('初始27项RED确为缺少结构诊断；补充负例再发现6项结构校验缺口后修正，所有失败日志保留。41项新结构检查',
        'r1的27项初始RED、6项补充RED及NEEDS_FIXES均保留；本r2对PREP-STATE-01新增状态关联负例和真实字符串解析不可用正例，9项RED修正后通过。51项结构检查')
    text=text.replace("preparation_test_scope='Fresh965 product plus4 compatibility; zero actual'", "preparation_test_scope=f'Fresh{manifest[\"tests\"]-4} product plus4 compatibility; zero actual'")
    text=text.replace('SOURCE32_E02_OUTPUT_STRUCTURE_PREPARATION_REVIEW','SOURCE32_R2_E02_OUTPUT_STRUCTURE_PREPARATION_REVIEW')
    text=text.replace('SOURCE32_E02_OUTPUT_STRUCTURE_DIAGNOSTICS_PREPARATION_PASS','SOURCE32_R2_E02_OUTPUT_STRUCTURE_DIAGNOSTICS_PREPARATION_PASS')
    text=text.replace("active_review_agent='/root/review_e02_output_structure_preparation'", "active_review_agent='/root/review_e02_output_structure_preparation'")
    with (N/'verification'/name).open('x',encoding='utf8',newline='\n') as f:f.write(text)
# The sealed first worktree and all original pointers remain valid.
p=N/'verification/verify_offline.py';text=p.read_text('utf8')
anchor="    pins=load(N/'inputs/accepted-dependency-pins.json')['files']"
extra="""    predecessor=load(N/'inputs/predecessor.json');prior=Path(predecessor['root'])
    assert sha(prior/'manifest.json')==predecessor['manifest_sha256']
    assert sha(prior/'review/independent-preparation-review.json')==predecessor['review_sha256']
    for name,h in load(prior/'manifest.json')['files'].items():assert sha(prior/name)==h,name
    for name,h in load(prior/'inputs/current-inputs.json')['files'].items():assert sha(name)==h,name
    frozen_root=Path(predecessor['root_candidate'])
    assert git(frozen_root,'rev-parse','HEAD').decode().strip()==predecessor['candidate']
    assert not git(frozen_root,'status','--porcelain').strip()
"""
assert anchor in text;p.write_text(text.replace(anchor,extra+anchor),encoding='utf8',newline='\n')
plan='H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-e02-output-structure-diagnostics-plan-20261108.md'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-structure-r2/UltimaAgent')
ledger=C/'.superpowers/sdd/jarvis-work-e02-output-structure-diagnostics-plan-20261108/progress.md';ledger.parent.mkdir(parents=True,exist_ok=True)
previous=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-structure/UltimaAgent')/ledger.relative_to(C)
ledger.write_bytes(previous.read_bytes()+b'\nTask 2: bounded Important fix PREP-STATE-01 in isolated r2. Original r1/47ac3a4 and its NEEDS_FIXES are preserved. Actual/model allocation remains zero.\nRuling: the original exact-plan Task2 requires a fresh exact-byte preparation closure after Important fixes; local independent gate takes precedence over the generic no-rereview suggestion. No old PASS is reused.\nRuling: preserve the existing frozen r1 worktree and use native managed r2; a new commit alone would not preserve live source pins referenced by r1. Cost is one additional checkout.\n')
print(json.dumps(dict(status='CLOSURE_TOOLS_PREPARED',new_scope=False)))
