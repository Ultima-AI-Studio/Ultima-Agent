"""Prepare publication programs before sealing; no run authority is issued."""
from pathlib import Path
N=Path(__file__).resolve().parents[1];OLD=N.parent/'e02-native-rejection-diagnostics-20261107-r1'
BASE='d860b2ab4e4d9974e33c96472e4ea15abb807280'
def write(name,s):
    with (N/'verification'/name).open('x',encoding='utf8',newline='\n') as f:f.write(s)
def common(s):
    return s.replace('C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-rejection/UltimaAgent','C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-budget/UltimaAgent').replace('6d758d9c3961f156a062e349ec4a949e2ee7a9a9',BASE).replace('ultimaagent-e02-native-rejection-','ultimaagent-e02-output-budget-')
s=common((OLD/'verification/commit_candidate.py').read_text('utf8'))
s=s.replace("checked['tests']==909", "checked['tests']==927").replace('fix(research): retain bounded request-bound native refusal reasons','fix(research): align shared phase guidance with actual output budget')
write('commit_candidate.py',s)
s=common((OLD/'verification/seal_preparation.py').read_text('utf8'))
s=s.replace('C:/Users/Administrator/.codex/worktrees/jarvis-e02-json-string-projection/UltimaAgent','C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-rejection/UltimaAgent').replace('e02-json-string-controlled-preparation-20261107-r1','e02-native-rejection-controlled-preparation-20261107-r1').replace('NATIVE_REJECTION_DIAGNOSTICS','OUTPUT_BUDGET_GUIDANCE')
s=s.replace("save(N/'inputs/current-inputs.json'", "assert len(complete_sources)==76\nsave(N/'inputs/current-inputs.json'")
s=s.replace("members.update([N/'plan.md'", "members.update(p for p in (N/'review').iterdir() if p.is_file())\nmembers.update([N/'plan.md'")
write('seal_preparation.py',s)
s=common((OLD/'verification/publish.py').read_text('utf8'))
s=s.replace('808ed5ca844f8b15afdcf3615bf4e3c16ea3f6a9','ae3b4e15a3544635dfb93ee4e58388430e2ca355').replace('1cfcff15f640fbdffe8a041360ea28ac1db3a36a','c7193bbdb0cbb303ec30d52ae2cff716edce0921')
s=s.replace('bounded native response rejection diagnostics','actual output budget guidance').replace('foreign_files_unchanged=9',"foreign_files_unchanged=len(json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files'])")
write('publish.py',s)
print('Prepared commit/seal/publication programs; no product or actual operation')
