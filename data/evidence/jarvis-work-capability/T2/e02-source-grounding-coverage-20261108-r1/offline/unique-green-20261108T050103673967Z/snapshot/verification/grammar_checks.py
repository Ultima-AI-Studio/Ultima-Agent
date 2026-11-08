"""Pinned upstream conversion of the actual product projection; no native calls."""
from pathlib import Path
import json,re,runpy
import pytest
from src.brain import agent_server as server, work_navigation as nav
from src.brain.tests.test_work_code_claim_schema import pages,phase
from src.brain.tests.test_work_sampler_json_strings import pattern
N=Path(__file__).resolve().parents[1]

def convert_canonical(schema):
    module=runpy.run_path(str(N/'inputs/upstream/json_schema_to_grammar.py'),run_name='offline_pinned_order')
    converter=module['SchemaConverter'](prop_order={},allow_fetch=False,dotall=False,raw_pattern=False)
    schema=json.loads(nav.canonical_v3(schema))
    converter.visit(converter.resolve_refs(schema,'file://offline-fact-order.json'),'')
    grammar=converter.format_grammar()
    rules=[line for line in grammar.splitlines() if 'claim-kv' in line and 'evidence-id-kv' in line]
    assert rules
    return grammar,rules

@pytest.mark.parametrize('kind',['code','documented','limitation'])
def test_reference_emits_evidence_before_each_fact_kind_after_j3(kind):
    from src.brain.tests.test_work_evidence_first_generation import fact_node
    schema=server._research_sampler_schema(fact_node(kind))
    _,rules=convert_canonical(schema)
    assert all(line.index('evidence-id-kv')<line.index('claim-kv') for line in rules)

def test_saved_actual_writer_uses_production_projection_and_keeps_request_cap():
    from copy import deepcopy
    prior=N.parent/'e02-claim-generation-controlled-preparation-20261108-r1'
    wire=json.loads((prior/'actual/E02-controlled-1/trusted-runtime.raw').read_bytes())['wires'][6]
    request=json.loads(wire['entity'])
    before=deepcopy(wire['strict_schema'])
    old_grammar,old_rules=convert_canonical(request['format'])
    request['format']=server._research_sampler_schema(wire['strict_schema'])
    grammar,rules=convert_canonical(request['format'])
    assert wire['strict_schema']==before
    assert len(rules)==len(old_rules)==8
    assert all(line.index('claim-kv')<line.index('evidence-id-kv') for line in old_rules)
    assert all(line.index('evidence-id-kv')<line.index('claim-kv') for line in rules)
    assert len(grammar.encode())==len(old_grammar.encode())
    assert len(nav.canonical_v3(request))<=49152
    assert request['options']['num_predict']==2048
    (Path.cwd()/'actual-writer-evidence-first.gbnf').write_text(grammar,encoding='utf8')
    (Path.cwd()/'actual-writer-order.json').write_text(json.dumps(dict(
        original_entity_bytes=len(wire['entity'].encode()),projected_entity_bytes=len(nav.canonical_v3(request)),
        fact_rules=len(rules),grammar_bytes=len(grammar.encode()),strict_unchanged=True,
        native_calls=0,semantic_acceptance_credit=0)),encoding='utf8')

@pytest.mark.parametrize('op',['Logger.info','Date.now','$run','a中.bé'])
def test_pinned_reference_converts_actual_projected_pattern(op):
    source=N/'inputs/upstream/json_schema_to_grammar.py'
    module=runpy.run_path(str(source),run_name='offline_pinned_reference')
    converter=module['SchemaConverter'](prop_order={},allow_fetch=False,dotall=False,raw_pattern=False)
    value=pattern(server._research_sampler_schema(phase(pages(op))))
    converter.visit(dict(type='string',pattern=value),'')
    grammar=converter.format_grammar()
    assert 'dot ::=' not in grammar and r'\x00-\x1f' in grammar
    assert 'root ::=' in grammar and '[0-9a-fA-F]' in grammar

def test_three_logged_malformed_claims_are_rejected_by_current_projection():
    output=(N/'inputs/native-log-supplement/unvalidated-output.txt').read_text(encoding='utf8')
    assert json.loads((N/'inputs/native-log-supplement/capture.json').read_bytes())['logged_generation_tokens']==840
    lines=output.splitlines();count=0
    for i,line in enumerate(lines):
        if not line.startswith(('Logger.info(','Date.now(')):continue
        op=line.split('(',1)[0]
        body=lines[i-1].split('"claim": "',1)[1]+'\n'+line[:-2]
        strict=phase(pages(op))
        assert re.fullmatch(pattern(strict),body)
        assert not re.fullmatch(pattern(server._research_sampler_schema(strict)),body)
        with pytest.raises(json.JSONDecodeError):json.loads('"'+body+'"')
        count+=1
    assert count==3

def test_whole_writer_envelope_converts_with_local_refs_and_no_fetch():
    module=runpy.run_path(str(N/'inputs/upstream/json_schema_to_grammar.py'),run_name='offline_pinned_reference')
    converter=module['SchemaConverter'](prop_order={},allow_fetch=False,dotall=False,raw_pattern=False)
    writer=phase(pages())
    strict=nav.v3_research_envelope([
        dict(type='object',additionalProperties=False,required=['action','action_input'],
             properties=dict(action=dict(enum=['ultima_work_research_write']),action_input=writer)),
        nav.v3_research_final_schema()])
    sampler=server._research_sampler_schema(strict)
    converted=converter.resolve_refs(sampler,'file://offline-writer.json')
    converter.visit(converted,'')
    grammar=converter.format_grammar()
    assert 'root ::=' in grammar and 'research' in grammar
    assert 'dot ::=' not in grammar
    with (Path.cwd()/'product-writer-reference.gbnf').open('x',encoding='utf8') as f:f.write(grammar)
    with (Path.cwd()/'reference-conversion.json').open('x',encoding='utf8') as f:json.dump(dict(
        grammar_bytes=len(grammar.encode()),sampler_bytes=len(nav.canonical_v3(sampler)),
        reference_revision='b10488',compiled_native_validator_run=False,native_model_calls=0),f,indent=2)
