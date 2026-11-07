"""Pinned official reference conversion, never model inference or native proof."""
import hashlib
import importlib.util
import json
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


def test_official_converter_rejects_original_lookaround():
    c = converter()
    with pytest.raises(AssertionError, match='Unsupported pattern syntax'):
        c.visit(dict(type='string', pattern=r'^(?<!x)client\.run(?!y)$'), '')


def test_official_converter_accepts_correlated_sampler_schema(capsys):
    for index, op in enumerate(('client.run', '$run', 'a_9.$x', 'a中.bé')):
        schema = server._research_sampler_schema(nav.v3_phase_writer_schema(pages(op)))
        c = converter(); c.visit(schema, ''); grammar = c.format_grammar()
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
    c = converter(); c.visit(sampler, ''); grammar = c.format_grammar()
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
