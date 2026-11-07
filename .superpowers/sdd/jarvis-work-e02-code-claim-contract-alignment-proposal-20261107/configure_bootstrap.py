from pathlib import Path
R=Path('H:/UltimaAI/UltimaAgent')
OL=R/'.superpowers/sdd/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107'
L=R/'.superpowers/sdd/jarvis-work-e02-code-claim-contract-alignment-proposal-20261107'
s=(OL/'bootstrap.py').read_text('utf8')
changes=[('e02-source-reference-schema-20261107-r1','e02-code-claim-schema-20261107-r1'),('e02-fixed-target-schema-20261107-r1','e02-source-reference-schema-20261107-r1'),
    ('jarvis-e02-source-reference','jarvis-e02-code-claim'),('jarvis-e02-fixed-target-schema','jarvis-e02-source-reference'),
    ('jarvis-work-e02-source-reference-schema-alignment-proposal-20261107','jarvis-work-e02-code-claim-contract-alignment-proposal-20261107'),
    ('900b944165c0175b91492e3fe5b31d96aabdcd5c','a0d21ebf167c41a76410075f7a92f1680926213f'),
    ('call_33506a697ec545c6b2a396ff83086672','call_99e734b15417466b92af3e8e85fdc3ea'),
    ('reference-contract-readback.json','code-operation-contract-readback.json'),("observed_rejection='FOREIGN_REFERENCE'","observed_rejection='CODE_OPERATION_REQUIRED'"),
    ('Correlate visible source and evidence enums in generation and independent replay; original writer checks retained.','Align code-claim operation constraints from trusted cards in generation and independent replay; original fact and writer gates retained.'),
    ('SOURCE17_E02_SOURCE_REFERENCE_SCHEMA_PREPARATION','SOURCE18_E02_CODE_CLAIM_SCHEMA_PREPARATION'),
    ('authorized_source_reference_schema_preparation','authorized_code_claim_schema_preparation'),
    ('source-reference schema alignment','code-claim contract alignment'),('frozen900b944','frozena0d21eb'),
    ('6ba6a53b-e91b-4c90-9ab6-388a82ea2ed9','f719ee48-7bce-4194-8bfc-82835af6d915'),
    ('来源与证据schema关联','代码事实生成契约对齐'),('来源引用schema授权接续','代码事实契约授权接续')]
for a,b in changes:
    assert a in s,a
    s=s.replace(a,b)
anchor="save(N/'inputs/copy-origin.json'"
pos=s.index(anchor)
s=s[:pos]+'''# Reuse the frozen N7 identity baseline; do not reinterpret a live listener.
p=N/'code/bindings.py';text=p.read_text('utf8')
text=text.replace("PROTECTED_BASELINE=N/'inputs/protected-baseline.json'", "PROTECTED_BASELINE=T/'e02-source-reference-schema-20261107-r1/inputs/protected-baseline.json'")
p.write_text(text,encoding='utf8')
p=N/'harness/adapter.py';text=p.read_text('utf8')
text=text.replace("PROTECTED_BASELINE=V/'inputs/protected-baseline.json'", "PROTECTED_BASELINE=T/'e02-source-reference-schema-20261107-r1/inputs/protected-baseline.json'")
p.write_text(text,encoding='utf8')
'''+s[pos:]
with (L/'bootstrap.py').open('x',encoding='utf8') as f:f.write(s)
s=(OL/'check_protected_preparation.py').read_text('utf8').replace('e02-fixed-target-schema-20261107-r1','e02-source-reference-schema-20261107-r1').replace(OL.name,L.name)
with (L/'check_protected_preparation.py').open('x',encoding='utf8') as f:f.write(s)
print('N8 bootstrap prepared')
