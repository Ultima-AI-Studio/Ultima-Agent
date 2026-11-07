from pathlib import Path
R=Path('H:/UltimaAI/UltimaAgent')
OL=R/'.superpowers/sdd/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107'
L=R/'.superpowers/sdd/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107'
text=(OL/'publish_ready.py').read_text('utf8')
replacements={
    'e02-fixed-target-schema-20261107-r1':'e02-source-reference-schema-20261107-r1',
    'jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107':'jarvis-work-e02-source-reference-schema-alignment-proposal-20261107',
    'jarvis-e02-fixed-target-schema/UltimaAgent':'jarvis-e02-source-reference/UltimaAgent',
    'ultimaagent-t2-e02-fixed-target-ready-20261107':'ultimaagent-t2-e02-source-reference-ready-20261107',
    '40bb6cdd08c6e18a05d118165402e5965d00b90f':'4653f923b66346fbfa81eb738d0a7db941b0dd64',
    '4dc293524f372ae7811404bd03d213308734928f':'f079ab8bf1a4929075c333ae278b880b9835cf1f',
    '826':'857','1551':'1557','61来源':'62来源',
    'jarvis-work-t2-e02-fixed-target-preparation-20261107.md':'jarvis-work-t2-e02-source-reference-preparation-20261107.md',
    '固定目标schema':'来源与证据schema',
    'SOURCE16_E02_FIXED_TARGET_SCHEMA_REVIEWED_READY':'SOURCE17_E02_SOURCE_REFERENCE_SCHEMA_REVIEWED_READY',
    'chore(e02): seal reviewed fixed-target schema and one-case readiness':'chore(e02): seal source-reference schema and reconciled identity readiness',
    'docs(e02): mirror fixed-target schema preparation':'docs(e02): mirror source-reference schema preparation'}
for old,new in replacements.items():
    assert old in text,old
    text=text.replace(old,new)
with (L/'publish_ready.py').open('x',encoding='utf8',newline='\n') as f:f.write(text)
print('Publication helper prepared; not invoked')
