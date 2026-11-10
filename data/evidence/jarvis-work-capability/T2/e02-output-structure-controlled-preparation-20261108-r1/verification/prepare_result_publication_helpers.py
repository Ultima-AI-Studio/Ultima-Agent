"""Prepare local-only result publication/readback; preserve old helpers unchanged."""
from pathlib import Path
import ast
import hashlib
import json

N = Path(__file__).resolve().parents[1]
O = N.parent / 'e02-output-budget-controlled-preparation-20261107-r1'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)

def write_new(p, text):
    ast.parse(text, filename=str(p))
    with p.open('x', encoding='utf8', newline='\n') as f:
        f.write(text)

source = N / 'verification/verify_result_preservation.py'
preservation = source.read_text(encoding='utf8')
preservation = replace_once(preservation,
    '"""After allocation, verify immutable inputs without obsolete allocation-zero assertions."""',
    '"""Post-closeout readback: immutable predecessor checks plus exact reviewed-result state."""')
preservation = replace_once(preservation,
    "s=load(T/'current-run.json');assert s['last_actual_result']==load(N/'inputs/previous-current-run.json')['last_actual_result']",
    "s=load(T/'current-run.json');assert s['previous_actual_result']==load(N/'inputs/previous-current-run.json')['last_actual_result']\n    actual=s['last_actual_result'];review=load(N/'review/independent-result-review.json')\n    assert actual['run_id']==review['run_id']=='c4caa739-c466-44f3-866b-0c57ea8c5e40'\n    assert actual['result_manifest_sha256']==review['result_manifest_sha256']==sha(N/'review/result-inputs/result-manifest.json')\n    assert actual['review_sha256']==sha(N/'review/independent-result-review.json')\n    assert actual['independent_review']=='FAIL_CONFIRMED' and actual['acceptance_credit']==0\n    assert s['actual_case_allocation_remaining']==s['result_review_allocation_remaining']==0")
closed = N / 'verification/verify_closed_result_preservation.py'
write_new(closed, preservation)

publish_source = O / 'verification/publish_allocated_result.py'
publish = publish_source.read_text(encoding='utf8')
for old, new in (
    ('jarvis-e02-output-budget/UltimaAgent', 'jarvis-e02-output-structure-r2/UltimaAgent'),
    ('ultimaagent-e02-output-budget-controlled-result-20261107', 'ultimaagent-e02-output-structure-controlled-result-20261108'),
    ("N/'verification/verify_preservation.py'", "N/'verification/verify_closed_result_preservation.py'"),
    ('verification/workers-before-allocated-case.json', 'verification/allocated-worker-observation.json'),
    ('7ee6b08efdf0375278cce79e4a4a81736ad1cfc3', 'dff378fec3ce30f9c252a4713147bc389e22c125'),
    ('06b138cd699f7a1ef8de1ac5b912ba7ff017bc1a', '17b53acd9dd980fb6afeffa8be1035ee8e719b5f'),
    ('docs(e02): preserve output-budget one-case failure and independent review', 'docs(e02): preserve full-output failure and independent result review'),
    ('docs(e02): mirror output-budget one-case result', 'docs(e02): mirror full-output failure and next repair proposal'),
    ('0421a54cab572be013c3f7ad562e86406bfe8e52', 'bf7f7a9cf0e4ba559c29daa388c00379d12d345a'),
):
    publish = replace_once(publish, old, new)
publish = replace_once(publish, "for directory in ('allocation-before','result-audit-before','result-closeout-before'):",
    "project.update(N/name for name in ('verification/prepare_result_publication_helpers.py','verification/verify_result_preservation.py','verification/verify_closed_result_preservation.py','verification/result-goal-registry-observation.json','review/result-inputs/output-text-observation.json','review/result-inputs/structural-analysis.json'))\nfor directory in ('allocation-before','result-audit-before','result-closeout-before'):")
publish_path = N / 'verification/publish_allocated_result.py'
write_new(publish_path, publish)

readback_source = O / 'verification/result_final_readback.py'
readback = readback_source.read_text(encoding='utf8')
readback = replace_once(readback, "previous['run_id']=='72d7d71b-39a9-455a-b0b4-8823b3f24c00'", "previous['run_id']=='9dbe192a-3bc1-4a4d-a218-581846d5f654'")
readback = replace_once(readback, "manifest['run_id']=='9dbe192a-3bc1-4a4d-a218-581846d5f654'", "manifest['run_id']=='c4caa739-c466-44f3-866b-0c57ea8c5e40'")
readback = replace_once(readback, 'call_8b7f20b59b8d4855b50e36d5ccc115ba', 'call_5c06d21b59b8475b873814f857990cc3')
readback = replace_once(readback, "value=dict(verdict=", "assert actual['output_structure']==review['output_structure']\nassert actual['output_structure']['mode']=='FULL' and actual['output_structure']['omitted_chars']==0\nassert sorted(actual['output_structure']['literal_repeat_counts'].values())==[49,50]\nassert state['next_proposal']['status']=='PROPOSED_NOT_IMPLEMENTED_OR_REVIEWED'\nvalue=dict(verdict=")
readback = replace_once(readback, "with (N/'verification/result-final-readback.json').open", "value['output_structure']=actual['output_structure']\nvalue['next_proposal']=state['next_proposal']\nwith (N/'verification/result-final-readback.json').open")
readback_path = N / 'verification/result_final_readback.py'
write_new(readback_path, readback)
register = N / 'verification/register_reviewed_result.py'
ast.parse(register.read_text(encoding='utf8'), filename=str(register))
binding = dict(
    kind='LOCAL_RESULT_BOOKKEEPING_SOURCE_BINDINGS',
    scope='No model/runtime/production changes; exact publication and readback only',
    source_sha256={str(p):sha(p) for p in (source, publish_source, readback_source)},
    generated_sha256={str(p):sha(p) for p in (closed, publish_path, readback_path, register)},
    product_changes=0, actual_invocations=0, model_calls=0)
with (N / 'verification/result-publish-source.json').open('x', encoding='utf8', newline='\n') as f:
    json.dump(binding, f, ensure_ascii=False, indent=2)
print(json.dumps(dict(prepared=4, ast_parse='PASS', product_changed=False, runtime_invoked=False)))
