"""Pinned official reference conversion, never model inference or native proof."""
import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest
from src.brain import agent_server as server, work_navigation as nav
from src.brain.tests.test_work_code_claim_schema import card, pages

UPSTREAM = Path(__file__).with_name('upstream')


def converter():
    source = UPSTREAM/'json_schema_to_grammar.b10488.py'
    data = source.read_bytes()
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() == '83abd259da57fb6384b4e4281f18875a05cc3d73'
    spec = importlib.util.spec_from_file_location('official_llama_schema_reference', source)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.SchemaConverter(prop_order={}, allow_fetch=False, dotall=False, raw_pattern=False)


def converted(schema):
    c=converter();resolved=c.resolve_refs(deepcopy(schema),'')
    c.visit(resolved,'');return c.format_grammar()


def test_official_converter_rejects_original_lookaround():
    c = converter()
    with pytest.raises(AssertionError, match='Unsupported pattern syntax'):
        c.visit(dict(type='string', pattern=r'^(?<!x)client\.run(?!y)$'), '')


def test_official_converter_accepts_correlated_sampler_schema(capsys):
    for index, op in enumerate(('client.run', '$run', 'a_9.$x', 'a中.bé')):
        schema = server._research_sampler_schema(nav.v3_phase_writer_schema(pages(op)))
        grammar = converted(schema)
        # The upstream Python formatter can split adjacent literal tokens;
        # normalize only that formatting when checking the operation literal.
        assert ('"'+op+'"') in grammar.replace('" "', '') and 'anyOf' not in grammar
        assert '[^A-Za-z0-9_$.]' in grammar and '[^A-Za-z_$]' in grammar
        assert not capsys.readouterr().err
        (Path.cwd()/f'official-pattern-{index}.gbnf').write_text(grammar, encoding='utf8')


def test_maximum_card_case_preserves_constraints_and_existing_byte_gate():
    visible = tuple((f'S{min(page+1, 5)}', nav.canonical_v3([
        card(page*8+i, op='a' * 195 + f'{page*8+i:05d}') for i in range(8)])) for page in range(6))
    schema = nav.v3_phase_writer_schema(visible)
    sampler = server._research_sampler_schema(schema)
    grammar = converted(sampler)
    for i in range(48): assert 'a' * 195 + f'{i:05d}' in grammar.replace('" "', '')
    phase = json.dumps(schema, ensure_ascii=False, separators=(',', ':'))
    # Even without source bodies, duplicating this full contract in the phase
    # plus strict format exceeds the existing byte gate. Never silently trim it.
    strict_bytes = len(nav.canonical_v3([[dict(role='system', content=phase)], schema]))
    assert strict_bytes > 32768
    (Path.cwd()/'maximum-schema-budget.json').write_text(json.dumps(dict(
        pages=6, cards=48, sources=5, operation_chars=200, strict_bytes_lower_bound=strict_bytes,
        strict_cap=32768, native_entity_cap=49152, disposition='original byte gate must reject',
        native_binary_executed=False)), encoding='utf8')
    (Path.cwd()/'official-maximum.gbnf').write_text(grammar, encoding='utf8')


def envelope(writer):
    return nav.v3_research_envelope([dict(type='object',additionalProperties=False,required=['action','action_input'],
        properties=dict(action=dict(enum=['ultima_work_research_write']),action_input=writer)),
        dict(type='object',additionalProperties=False,required=['final_answer'],properties=dict(final_answer=dict(type='string',maxLength=1000)))])


@pytest.mark.parametrize('count',[3,4,5])
def test_complete_envelope_local_refs_and_tuple_conversion(count,capsys):
    from src.brain.tests.test_work_unique_source_sections import visible
    writer=nav.v3_phase_writer_schema(visible(count));whole=envelope(writer)
    grammar=converted(server._research_sampler_schema(whole))
    assert 'tuple' in grammar and not capsys.readouterr().err
    # Shared definitions appear once; ordinary source-count cases fit the old
    # gate. Complete live requests still face the original independent limits.
    messages=[dict(role='system',content=nav.v3_research_phase(writer)),dict(role='user',content='Compare the documented sources.')]
    strict_bytes=len(nav.canonical_v3([messages,whole]));assert strict_bytes<32768
    entity=nav.canonical_v3(dict(model='qwen3-8b-uncensored',messages=messages,format=server._research_sampler_schema(whole),stream=False,
        options=dict(num_ctx=16384,temperature=0,num_predict=2048)))
    assert len(entity)<49152
    (Path.cwd()/f'whole-envelope-{count}.gbnf').write_text(grammar,encoding='utf8')
    (Path.cwd()/f'whole-envelope-{count}-bytes.json').write_text(json.dumps(dict(sources=count,strict_bytes=strict_bytes,entity_bytes=len(entity),
        measure_scope='phase, question and complete envelope; real SDK history remains subject to unchanged live gates',native_binary_executed=False)),encoding='utf8')


def test_observed_six_page_shape_preserves_bound_references_and_size(capsys):
    import time
    from dataclasses import replace
    from src.brain.tests.test_work_navigation import fixture,policy,key
    root=Path(__file__).with_name('fixtures')
    raw=(root/'controlled-corpus.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002'
    diagnostic=(root/'predecessor-failure-diagnostic.json').read_bytes()
    assert hashlib.sha256(diagnostic).hexdigest()=='bf8efb945255dcff31ace9dceee48d69d8450b28f0636c79a86812812a1a65dc'
    corpus=json.loads(raw);selected=json.loads(diagnostic)['pages']
    collection,binding,records=fixture([s['body'] for s in corpus['sources']])
    catalog=collection.catalogue_json;trace=collection.trace_json;record_text=records.decode()
    for i,source in enumerate(corpus['sources'],1):
        before=f'https://example.org/source{i}.md';after=source['final_url']
        catalog=catalog.replace(before,after);trace=trace.replace(before,after);record_text=record_text.replace(before,after)
    collection=replace(collection,catalogue_json=catalog,trace_json=trace)
    cat=nav.prepare_navigation(collection,binding,policy(),get_records_json=record_text.encode(),deadline=time.monotonic()+30)
    views=[nav.build_page(cat,p['source_id'],p['requested_start'],key(i+1)) for i,p in enumerate(selected)]
    assert [len(json.loads(v.cards_json)) for v in views]==[len(p['cards']) for p in selected]
    writer=nav.v3_phase_writer_schema(tuple((v.source_id,v.cards_json) for v in views));whole=envelope(writer)
    grammar=converted(server._research_sampler_schema(whole));assert not capsys.readouterr().err
    messages=[dict(role='system',content=nav.v3_research_phase(writer)),dict(role='user',content=corpus['query'])]
    messages.extend(dict(role='user',content='Observation: '+v.wire_json.decode()) for v in views)
    measured=len(nav.canonical_v3([messages,whole]));assert measured<32768
    (Path.cwd()/'observed-six-page.gbnf').write_text(grammar,encoding='utf8')
    (Path.cwd()/'observed-six-page-bytes.json').write_text(json.dumps(dict(pages=6,cards=sum(len(p['cards']) for p in selected),measured_bytes=measured,
        measure_scope='reconstructed page observations, original question, phase and envelope; excludes inherited SDK system and action messages',
        original_cap=32768,native_binary_executed=False,actual_call=False)),encoding='utf8')
