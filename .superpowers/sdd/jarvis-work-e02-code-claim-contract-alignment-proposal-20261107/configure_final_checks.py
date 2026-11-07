from pathlib import Path
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-source-reference-schema-20261107-r1';N=T/'e02-code-claim-schema-20261107-r1'
OL=R/'.superpowers/sdd/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107'
L=Path(__file__).parent
BASE='a0d21ebf167c41a76410075f7a92f1680926213f'

def new(p,text):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(text)

text=(OL/'commit_product.py').read_text('utf8')
for a,b in [(OLD.name,N.name),('jarvis-e02-source-reference/UltimaAgent','jarvis-e02-code-claim/UltimaAgent'),
    ('ultimaagent-e02-source-reference-candidate','ultimaagent-e02-code-claim-candidate'),
    ("[('reference-green',29)","[('claim-green',28),('grammar',3),('reference-green',29)"),
    ('total==566','total==597'),('900b944165c0175b91492e3fe5b31d96aabdcd5c',BASE),
    ("'src/brain/tests/test_work_write_diagnostics.py','src/brain/tests/test_work_source_reference_schema.py'","'src/brain/tests/test_work_code_claim_schema.py'"),
    ('fix(research): correlate visible source and evidence schema','fix(research): constrain code claims to issued operations')]:
    assert a in text,a
    text=text.replace(a,b)
new(L/'commit_product.py',text)
text=(OL/'rebind_candidate.py').read_text('utf8')
for a,b in [(OLD.name,N.name),('e02-fixed-target-schema-20261107-r1',OLD.name),
    ('jarvis-e02-source-reference','jarvis-e02-code-claim'),('jarvis-e02-fixed-target-schema','jarvis-e02-source-reference'),
    ('900b944165c0175b91492e3fe5b31d96aabdcd5c',BASE),
    ('test_work_source_reference_schema.py','test_work_code_claim_schema.py'),
    ('Visible source/evidence schema in generation and independent replay; original writer/fact/END gates retained',
     'Evidence-specific exact code operation schema in generation and independent replay; original writer and fact gates retained'),
    (",'src\\\\brain\\\\tests\\\\test_work_write_diagnostics.py'",''),
    ("changed_existing_sources=changed,added_tests=","protected_baseline_sha256=sha(Path(inputs['protected_baseline_path'])),changed_existing_sources=changed,added_tests=")]:
    assert a in text,a
    text=text.replace(a,b)
new(L/'rebind_candidate.py',text)
with (L/'progress.md').open('a',encoding='utf8') as f:
    f.write('\nTask1 RED: 26 failures / 1 existing phase-forgery pass; six real SDK mock cases showed old schema admitting bad claims into the writer (Unlinked or failed END). First RED replay assertions used StopIteration; the second retained RED has explicit missing-pattern assertions. New final product coverage28 includes unchanged writer diagnostic defense.\n')
    f.write('\nTask1: official b10488 converter matches Ollama v0.32.15 source pin. Initial grammar checks had2 assertion failures because Python formatter splits adjacent literals; normalize only adjacent literal formatting, keep all semantic constraints. Final3 pass, no source parser changes or model calls. Host DNS retrieval failed and empty artifact is retained as unused; connector-fetched bytes match Git blob hashes.\n')
    f.write('\nRuling: use the supported anchored groups/classes/alternation equivalent to the original operation guard for valid single-line claims; do not copy lookaround into the sampler. Code card IDs sharing one operation are grouped without dropping IDs. Cost: large diverse-operation schemas can reach original byte gates and fail closed; installed native sampling remains unproven until the granted single case.\n')
print('N8 commit and candidate rebind helpers prepared; no runtime authority')
