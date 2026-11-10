"""Reuse preserved checks and exact checkpoint helpers in the new evidence root."""
from pathlib import Path
import ast,hashlib,json
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-native-write-diagnostics-20261107-r1';N=T/'e02-fixed-target-schema-20261107-r1'
OL=R/'.superpowers/sdd/jarvis-work-e02-native-write-failure-diagnostics-proposal-20261107'
L=R/'.superpowers/sdd/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-fixed-target-schema/UltimaAgent')
def new(p,text):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(text)
def rep(text,old,new):
    assert old in text,old
    return text.replace(old,new)
assert N.is_dir() and not (C/'src/brain/tests/test_work_fixed_target_schema.py').exists()
(C/'src/brain/tests/test_work_fixed_target_schema.py').write_bytes((L/'fixed_target_tests.py').read_bytes())
p=N/'verification/run_product_checks.py';text=p.read_text('utf8')
text=rep(text,"    'diagnostics-red':", "    'target-red':['test_work_fixed_target_schema.py'], 'target-green':['test_work_fixed_target_schema.py'],\n    'diagnostics-red':")
p.write_text(text,encoding='utf8')
text=(OL/'commit_product.py').read_text('utf8')
for old,value in [(OLD.name,N.name),('jarvis-e02-write-diagnostics','jarvis-e02-fixed-target-schema'),('ultimaagent-e02-write-diagnostics-candidate-20261107','ultimaagent-e02-fixed-target-candidate-20261107'),
    ("[('diagnostics-green',17)","[('target-green',19),('diagnostics-green',17)"),('assert total==518','assert total==537'),
    ("changed=['src/brain/work_service.py','src/brain/tests/test_work_write_diagnostics.py']","changed=['src/brain/work_navigation.py','src/brain/tests/test_work_fixed_target_schema.py']"),
    ("=='src/brain/work_service.py'","=='src/brain/work_navigation.py'"),("=='src/brain/tests/test_work_write_diagnostics.py'","=='src/brain/tests/test_work_fixed_target_schema.py'"),
    ('0a57d50f226df70542838c05fb8a21e025e19447','6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696'),
    ('fix(research): retain bounded trusted writer failure diagnostics','fix(research): align generation schema with fixed research target')]:text=rep(text,old,value)
new(L/'commit_product.py',text)
# Rebind from immediate predecessor; all runtime functions stay unchanged.
text=(OL/'rebind_candidate.py').read_text('utf8')
text=rep(text,"N=T/'e02-native-write-diagnostics-20261107-r1';OLD=T/'e02-source13-native-metadata-20261107-r1'", "N=T/'e02-fixed-target-schema-20261107-r1';OLD=T/'e02-native-write-diagnostics-20261107-r1'")
text=rep(text,'0a57d50f226df70542838c05fb8a21e025e19447','6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696')
text=rep(text,'jarvis-e02-write-diagnostics','jarvis-e02-fixed-target-schema')
text=rep(text,'jarvis-e02-native-metadata','jarvis-e02-write-diagnostics')
text=rep(text,'src/brain/tests/test_work_write_diagnostics.py','src/brain/tests/test_work_fixed_target_schema.py')
text=rep(text,"['src\\\\brain\\\\work_service.py']","['src\\\\brain\\\\work_navigation.py']")
text=rep(text,'Bounded public research-write failure diagnostics only; all writer/END gates unchanged','Fixed research.md enum in v3 writer schema only; unchanged writer/END gates')
new(L/'rebind_candidate.py',text)
print('New tests and preparation helpers created; product implementation unchanged')
