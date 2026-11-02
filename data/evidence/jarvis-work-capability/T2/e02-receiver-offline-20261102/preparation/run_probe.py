"""One fixed offline receiver comparison. NOT RELEASED by its existence.

Isolated research modules; unchanged work_tools imported only for real verifier.
No SDK tools, engines, agents or clients are constructed or invoked.
"""
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
import ast
import ctypes
from ctypes import wintypes
import datetime
import hashlib
import importlib.util
import json
import os
import sys
import time

ENTRY = time.monotonic()
PREP = Path(__file__).resolve().parent
OUT = PREP.parent / 'actual-r1'
C = Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
H = Path('H:/UltimaAI/UltimaAgent')
T = H / 'data/evidence/jarvis-work-capability/T2'
IDENTITY = ('source_id', 'final_url', 'decoded_body_sha256', 'read_call_id',
            'request_id', 'session_id', 'task_id')
PROHIBITED_ATTEMPTS = []


def prohibit(message):
    PROHIBITED_ATTEMPTS.append(message)
    raise PermissionError(message)


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(name, value):
    path = OUT / name
    if path.parent != OUT or path.exists():
        raise ValueError('Nonfresh or undeclared output')
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def require(ok, why):
    if not ok:
        raise ValueError(why)


def deadline(frame, event, arg):
    if time.monotonic() - ENTRY >= 1800:
        raise TimeoutError('1800 second entry wall cap; no retry')
    module = frame.f_globals.get('__name__', '')
    if event == 'call' and module.startswith('openjarvis.'):
        name = frame.f_code.co_name
        instance = frame.f_locals.get('self')
        if name in ('execute', 'submit', '_ensure_started', 'create'):
            prohibit('SDK execution/construction prohibited: '+module+'.'+name)
        if name == '__init__' and instance is not None:
            cls = type(instance)
            bases = {base.__name__ for base in cls.__mro__}
            if bases & {'BaseTool','ToolExecutor','BaseAgent','InferenceEngine','Jarvis','JarvisSystem','SystemBuilder'}:
                prohibit('SDK instance prohibited: '+cls.__module__+'.'+cls.__name__)
    if event == 'call' and frame.f_code.co_name == '__init__' and module.split('.')[0] in ('httpx', 'requests', 'httpcore', 'ollama', 'openai'):
        instance = frame.f_locals.get('self')
        if instance is not None and {base.__name__ for base in type(instance).__mro__} & {'Client','AsyncClient','Session','OpenAI','AsyncOpenAI','AzureOpenAI','AsyncAzureOpenAI','ConnectionPool','AsyncConnectionPool'}:
            prohibit('Client construction prohibited')
    return deadline


def head(root):
    gd = root / '.git'
    if gd.is_file():
        gd = (root / gd.read_text().strip().split(': ', 1)[1]).resolve()
    common = (gd / (gd / 'commondir').read_text().strip()).resolve() if (gd / 'commondir').exists() else gd
    value = (gd / 'HEAD').read_text().strip()
    if not value.startswith('ref: '):
        return value
    ref = value[5:]
    for base in (gd, common):
        if (base / ref).is_file():
            return (base / ref).read_text().strip()
    for line in (common / 'packed-refs').read_text().splitlines():
        if line.endswith(' ' + ref):
            return line.split()[0]
    raise ValueError('Cannot establish HEAD')


def process_identity(item):
    # Read-only Win32 query, PID plus exact 100ns creation time and executable.
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = (wintypes.HANDLE,) + (ctypes.POINTER(wintypes.FILETIME),) * 4
    kernel.QueryFullProcessImageNameW.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD))
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    handle = kernel.OpenProcess(0x1000, False, item['pid'])
    if not handle:
        return dict(expected=item, verified=False, error=ctypes.get_last_error())
    try:
        times = [wintypes.FILETIME() for _ in range(4)]
        require(kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)), 'GetProcessTimes failed')
        buf = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buf))
        require(kernel.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)), 'Query process image failed')
        ticks = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        dt = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(microseconds=ticks // 10)
        created = dt.strftime('%Y-%m-%dT%H:%M:%S.') + f'{ticks % 10000000:07d}Z'
        return dict(expected=item, actual=dict(pid=item['pid'], exe=buf.value, created_utc=created),
                    verified=created == item['created_utc'] and os.path.normcase(buf.value) == os.path.normcase(item['exe']))
    finally:
        kernel.CloseHandle(handle)


def boundary(manifest):
    expected = read(manifest['source21_path'])
    protected = read(manifest['runtime_before'])['protected5']
    return dict(source21_snapshot_sha256=sha(Path(manifest['source21_path']).read_bytes()),
                source21={p: sha((C / p).read_bytes()) for p in expected},
                source21_match=all(sha((C / p).read_bytes()) == h for p, h in expected.items()),
                heads=dict(C=head(C), H=head(H)), protected5=[process_identity(p) for p in protected])


def audit(event, args):
    if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.exec', 'os.spawn')):
        prohibit('Network/process action prohibited: ' + event)
    if event == 'import' and args[0] in ('src.brain.agent_server', 'src.brain.work_service'):
        prohibit('Out-of-scope import: ' + args[0])
    if event == 'open':
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(x in mode for x in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing:
            if not (isinstance(path, (str, bytes, os.PathLike)) and Path(path).resolve().parent == OUT):
                prohibit('Write outside declared actual-r1 root')
    if event in ('os.remove', 'os.rename', 'os.rmdir', 'os.mkdir', 'os.link', 'os.symlink', 'os.chmod', 'os.truncate'):
        prohibit('Filesystem mutation prohibited: ' + event)


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, PREP / filename)
    module = importlib.util.module_from_spec(spec)
    module.__package__ = 'src.brain'
    # New isolated module identity, never a replacement for a product module.
    require(name not in sys.modules, 'Isolated module name already present')
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def syntax(wr, source):
    suffix = PurePosixPath(urlsplit(source['final_url']).path).suffix.lower()
    if suffix == '.py':
        try:
            return list(wr._python_witnesses(source['body']))
        except (SyntaxError, ValueError, wr.tokenize.TokenError):
            return []
    if suffix in ('.js', '.ts', '.mjs', '.cjs'):
        return wr._js_tokens(source['body'], suffix)
    return None


def observation(wr, source, view, table):
    from pygments.lexers.javascript import JavascriptLexer, TypeScriptLexer
    suffix = PurePosixPath(urlsplit(source['final_url']).path).suffix.lower()
    tokens = []
    if suffix == '.py':
        import io
        import tokenize
        offsets = [0]
        for line in source['body'].splitlines(keepends=True):
            offsets.append(offsets[-1]+len(line))
        for token in tokenize.generate_tokens(io.StringIO(source['body']).readline):
            def offset(coord):
                return offsets[min(coord[0]-1,len(offsets)-1)] + coord[1]
            tokens.append(dict(type=tokenize.tok_name[token.type], value=token.string,
                               start=offset(token.start), end=offset(token.end),
                               start_coordinate=token.start, end_coordinate=token.end))
    if suffix in ('.js', '.ts', '.mjs', '.cjs'):
        lexer = TypeScriptLexer() if suffix == '.ts' else JavascriptLexer()
        for start, family, value in lexer.get_tokens_unprocessed(source['body']):
            end = start + len(value)
            def coordinate(pos):
                prefix = source['body'][:pos]
                return [prefix.count('\n') + 1, len(prefix.rsplit('\n', 1)[-1])]
            tokens.append(dict(type=str(family), value=value, start=start, end=end,
                               start_coordinate=coordinate(start), end_coordinate=coordinate(end)))
    syn = syntax(wr, source)
    yielded = list(wr._anchors(source, dict(view['lines']), syn))
    qualified = sorted({a for a in yielded if a[1]-a[0] < 8 and all(i in dict(view['lines']) for i in range(a[0], a[1]+1))})
    return dict(source=source, visible=view, tokens=tokens,
                syntax_rows=[[a,b,str(c),d] for a,b,c,d in syn] if suffix != '.py' and syn else syn,
                yielded_anchors=yielded, qualified_anchors=qualified, table=table)


def witness(card):
    return tuple(card[k] for k in IDENTITY) + (card['first_line'], card['last_line'], card['kind'], card.get('symbol', ''))


def compare(old, new):
    a = {witness(c): (k,c) for k,c in old.items()}
    b = {witness(c): (k,c) for k,c in new.items()}
    return dict(added=[b[x] for x in b.keys()-a.keys()], removed=[a[x] for x in a.keys()-b.keys()],
                changed=[dict(old=a[x], new=b[x]) for x in a.keys() & b.keys() if a[x][1] != b[x][1]],
                id_changes=[dict(old=a[x][0], new=b[x][0], witness=x) for x in a.keys() & b.keys() if a[x][0] != b[x][0]],
                reused_ids=[dict(id=k, old=old[k], new=new[k]) for k in old.keys() & new.keys() if old[k] != new[k]],
                old_order=list(old), new_order=list(new), old_selected=list(a), new_selected=list(b))


def real_readback(wr, catalogue, table, payload, resolved, bindings, name):
    # This is the unchanged full verifier, using synthetic direct-written files,
    # not a model/SDK report or an E02 artifact. No tool instance is constructed.
    from src.brain.work_tools import WorkBinding
    identities = {k:catalogue[0][k] for k in ('request_id','session_id','task_id')}
    require(all(all(s[k] == v for k,v in identities.items()) for s in catalogue), 'Fixture catalogue identities inconsistent')
    binding = WorkBinding(root=OUT, **identities)
    rendered = wr.render_research_report(resolved, compact(catalogue), bindings=bindings)
    path = OUT / payload['path']
    require(path.parent == OUT, 'Synthetic path out of root')
    if not path.exists():
        with path.open('xb') as stream:
            stream.write(rendered.content.encode('utf8'))
    artifact = dict(call_id=name, path=str(path), sha256=sha(path.read_bytes()))
    record = dict(**identities, result=dict(file_call_id=name, payload_json=compact(resolved),
        submitted_json=compact(payload), protocol_version=2, bindings=bindings,
        cited_source_ids=list(rendered.cited_source_ids), evidence=list(rendered.evidence)))
    return wr.verify_research_artifacts(binding, [artifact], [record], compact(catalogue), require_reference=True)


def compat(wr_old, wr_new, catalogue, old, new, label):
    # Exhaust every old issued ID, with generic claims derived from its operation.
    # Sealed per-source packets issued no protocol2 report payload; these are
    # constructed controls against the unchanged public reference path.
    results = []
    verifier_complete = True
    sids = list(dict.fromkeys(c['source_id'] for c in old.values()))
    require(len(sids) >= 3, 'Compatibility controls need three source sections')
    for ordinal, (key, card) in enumerate(old.items(), 1):
        chosen = [key] + [next(k for k,c in old.items() if c['source_id'] == sid) for sid in sids if sid != card['source_id']][:2]
        payload = dict(path=label+'-readback-'+str(ordinal)+'.md', title='Offline reference control', sections=[
            dict(source_id=old[k]['source_id'], heading='Source observation', facts=[
                dict(claim=old[k]['symbol'] or 'witness', evidence_id=k)]) for k in chosen])
        resolved, bindings = wr_old.resolve_references(payload, old, compact(catalogue))
        rendered = wr_old.render_research_report(resolved, compact(catalogue), bindings=bindings)
        record = dict(payload=payload, old_payload=resolved, old_bindings=bindings,
                      old_rendered=rendered.content, original_snapshot_control='resolved')
        try:
            record['real_baseline_readback'] = real_readback(wr_old,catalogue,old,payload,resolved,bindings,label+'-readback-'+str(ordinal)+'.md')
        except Exception as exc:
            verifier_complete = False
            record['real_baseline_readback_error'] = repr(exc)
        try:
            result, rebound = wr_new.resolve_references(payload, new, compact(catalogue))
            record.update(candidate_payload=result, candidate_bindings=rebound,
                          payload_identical=result == resolved, bindings_identical=rebound == bindings)
            if result != resolved or rebound != bindings:
                record['status'] = 'STOP_COMPATIBILITY_ACCEPTANCE_INCORRECT_REMAP'
            else:
                reread = wr_new.render_research_report(result, compact(catalogue), bindings=rebound)
                record['status'] = 'identical' if reread.content == rendered.content else 'STOP_RENDER_CHANGED'
            try:
                # Pass OLD issued payload/full binding receipt into unchanged
                # candidate verifier; changed bindings must be rejected there.
                record['real_candidate_readback'] = real_readback(wr_new,catalogue,new,payload,resolved,bindings,label+'-candidate-readback-'+str(ordinal)+'.md')
                record['real_candidate_status'] = 'accepted_identical' if result == resolved and rebound == bindings else 'UNSAFE_ACCEPTED_REMAP'
            except ValueError as exc:
                record.update(real_candidate_status='rejected_before_success', real_candidate_error=repr(exc))
            except Exception as exc:
                verifier_complete = False
                record.update(real_candidate_status='UNVERIFIED', real_candidate_error=repr(exc))
        except (ValueError, KeyError) as exc:
            record.update(status='rejected_before_success', error=repr(exc))
        except Exception as exc:
            # jsonschema.ValidationError is a safe rejection, other faults incomplete.
            from jsonschema.exceptions import ValidationError
            if not isinstance(exc, ValidationError):
                raise
            record.update(status='rejected_before_success', error=repr(exc))
        results.append(record)
    return dict(controls=results, no_successful_remap=all(x['status'] in ('identical', 'rejected_before_success') for x in results),
                full_verifier_verified=verifier_complete,
                migration='none; preserved original snapshot only; never issue candidate protocol2 IDs')


def fixture_source(case, sid='S1'):
    body = case['body']
    return dict(source_id=sid, final_url='https://offline.invalid/' + sid + case.get('suffix', '.ts'),
                dedupe_url='https://offline.invalid/' + sid + case.get('suffix', '.ts'),
                body=body, text=case.get('text', body), content_type=case.get('content_type', 'text/plain'),
                decoded_body_sha256=sha(body.encode()), read_call_id='offline-read-'+sid,
                request_id='offline-request', session_id='offline-session', task_id='offline-task')


def fixture_matrix(old, new, cases):
    rows = []
    for case in cases:
        source = fixture_source(case)
        visible = dict(enumerate(source['text'].splitlines(), 1))
        for n in case.get('omitted_lines', []):
            visible.pop(n, None)
        tables = []
        for wr in (old, new):
            syn = syntax(wr, source)
            anchors = list(wr._anchors(source, visible, syn))
            accepted = []
            rejected = []
            for first,last,kind,op in anchors:
                fact = dict(kind=kind, claim=op or 'witness', first_line=first, last_line=last)
                if kind == 'code': fact['symbol'] = op
                try:
                    wr._fact_evidence(fact, source, visible, syn)
                    accepted.append([first,last,kind,op])
                except ValueError as exc:
                    rejected.append(dict(anchor=[first,last,kind,op], error=str(exc)))
            view = dict(source_id=source['source_id'], lines=list(visible.items()), omitted=bool(case.get('omitted_lines')))
            try:
                final = cards(wr, source, view)
            except ValueError as exc:
                if str(exc) != 'unused_preflight: no usable anchor': raise
                final = {}
            tables.append(dict(observation=observation(wr, source, view, final), schema=schema_for('offline-fixture-token', final),
                               accepted=accepted, rejected=rejected))
        before = {tuple(x) for x in tables[0]['accepted']}
        after = {tuple(x) for x in tables[1]['accepted']}
        added = after-before
        expected = case['expected']
        # Exact generic operations are fixture expectations, never historical IDs/facts.
        valid_ops = set(case.get('operations', []))
        passed = not (before-after) and all(x[2] == 'code' and x[3] in valid_ops for x in added)
        if expected == 'gain': passed &= valid_ops <= {x[3] for x in after if x[2] == 'code'} and bool(added)
        elif expected == 'preserve': passed &= before == after and valid_ops <= {x[3] for x in after if x[2] == 'code'}
        elif expected == 'reject': passed &= not any(x[2] == 'code' for x in after)
        elif expected == 'baseline_limitation': passed &= before == after
        rows.append(dict(case=case, baseline=tables[0], candidate=tables[1], added=list(added), lost=list(before-after), passed=bool(passed)))
        save('fixture-'+case['name']+'.json', rows[-1])
    return rows


def identity_negatives(wr):
    cases = [dict(body='const result = service.run();', suffix='.js'),
             dict(body='const result = other.run();', suffix='.js'),
             dict(body='const result = third.run();', suffix='.js')]
    sources = [fixture_source(c, 'S'+str(i)) for i,c in enumerate(cases, 1)]
    catalogue = compact(sources)
    table = wr.reference_cards(catalogue)
    records = []
    def attempt(label, call):
        try:
            call()
            records.append(dict(case=label, rejected=False))
        except ValueError as exc:
            records.append(dict(case=label, rejected=True, error=str(exc)))
    from types import SimpleNamespace
    attempt('cross-request', lambda: wr.bound_sources(catalogue, SimpleNamespace(request_id='foreign', session_id='offline-session', task_id='offline-task')))
    changed = json.loads(catalogue); changed[0]['body'] += '\n'
    attempt('body-hash', lambda: wr.reference_cards(compact(changed)))
    duplicate = json.loads(catalogue); duplicate[1]['source_id'] = 'S1'
    attempt('duplicate-source', lambda: wr.bound_sources(compact(duplicate)))
    keys = list(table)
    foreign = dict(path='offline.md', title='Offline', sections=[dict(source_id='S2',heading='Observation',facts=[dict(claim='service.run', evidence_id=keys[0])])]*3)
    try:
        wr.resolve_references(foreign, table, catalogue)
        records.append(dict(case='foreign-source-reference', rejected=False))
    except Exception as exc:
        from jsonschema.exceptions import ValidationError
        if not isinstance(exc, (ValueError, ValidationError)): raise
        records.append(dict(case='foreign-source-reference', rejected=True, error=repr(exc)))
    return records


def run(manifest):
    import pygments
    require(pygments.__version__ == '2.21.0', 'Pygments version mismatch')
    old = load_module('receiver_offline_baseline', 'baseline_work_research.py')
    new = load_module('receiver_offline_candidate', 'candidate_work_research.py')
    scopes = []
    for sid, filename in manifest['packets'].items():
        packet = read(filename)
        catalogue = packet['catalogue']
        source = next(s for s in catalogue if s['source_id'] == sid)
        require(all(sha(s['body'].encode()) == s['decoded_body_sha256'] for s in catalogue), 'Catalogue body identity mismatch')
        view, omitted = project(source)
        require(view == packet['view'], 'Historical projection mismatch')
        historical_old = cards(old, source, view)
        historical_new = cards(new, source, view)
        fidelity = {str(k):v for k,v in historical_old.items()} == packet['table']
        token = packet['schema']['anyOf'][0]['properties']['action_input']['oneOf'][0]['properties']['stage_token']['enum'][0]
        fidelity = fidelity and schema_for(token,historical_old) == packet['schema']
        historical_diff = compare(historical_old, historical_new)
        for label, wr, table in [('baseline',old,historical_old), ('candidate',new,historical_new)]:
            obs = observation(wr, source, view, table)
            obs.update(schema=schema_for(token,table), omitted_ranges=omitted, packet_sha256=sha(Path(filename).read_bytes()),
                       original_schema=packet['schema'], schema_fidelity=schema_for(token, historical_old) == packet['schema'])
            save(sid+'-historical-'+label+'.json', obs)
        old_public = old.reference_cards(compact(catalogue))
        new_public = new.reference_cards(compact(catalogue))
        require(len(historical_old) <= 48 and len(historical_new) <= 48 and
                all(sum(c['source_id'] == s['source_id'] for c in new_public.values()) <= 48 for s in catalogue), 'Card cap drift')
        for label, wr, table in [('baseline',old,old_public), ('candidate',new,new_public)]:
            save(sid+'-public-'+label+'.json', dict(catalogue=catalogue, schema=wr.reference_schema(table), table=table,
                observations=[observation(wr,s,wr._source_view(s,len(catalogue)),{k:c for k,c in table.items() if c['source_id']==s['source_id']}) for s in catalogue]))
        public_diff = compare(old_public, new_public)
        compatibility = compat(old,new,catalogue,old_public,new_public,sid)
        save(sid+'-compatibility.json', compatibility)
        # Generic complete this/super calls are the only allowable additions.
        added = [row[1] for row in historical_diff['added']]
        public_added = [row[1] for row in public_diff['added']]
        pure_receiver_additions = all(c['kind']=='code' and c['symbol'].split('.')[0] in ('this','super') for c in added+public_added)
        core_gain = any(c['symbol'].startswith('this.') and c['symbol'].split('.')[-1] not in ('log','info','warn','warning','debug','error','now') for c in added)
        public_core_gain = any(c['source_id']==sid and c['symbol'].startswith('this.') and c['symbol'].split('.')[-1] not in ('log','info','warn','warning','debug','error','now') for c in public_added)
        scope = dict(source_id=sid, baseline_fidelity=fidelity, historical_diff=historical_diff, public_diff=public_diff,
                     comparison_scope='historical 24000 per source vs public catalogue source-count projection; distinct numbering algorithms retained',
                     pure_receiver_additions=pure_receiver_additions, final_core_gain=core_gain, public_final_core_gain=public_core_gain,
                     compatibility_safe=compatibility['no_successful_remap'],
                     full_verifier_verified=compatibility['full_verifier_verified'],
                     historical_old_payload=packet['stage_payload'], historical_old_binding=packet['binding'],
                     historical_old_binding_hash=packet['binding_hash'],
                     historical_compatibility='STOP_REUSED_ORDINAL' if historical_diff['reused_ids'] else 'original_table_bindings_identical',
                     no_unrelated_loss=not historical_diff['removed'] and not historical_diff['changed'] and not public_diff['removed'] and not public_diff['changed'])
        scopes.append(scope)
        save(sid+'-differences.json', scope)
    fixtures = fixture_matrix(old, new, read(PREP/'fixtures.json'))
    negatives = identity_negatives(new)
    save('identity-negatives.json', negatives)
    return dict(scopes=scopes, fixture_pass=all(r['passed'] for r in fixtures), identity_negatives_pass=all(r['rejected'] for r in negatives),
                representation_checks_pass=all(s['baseline_fidelity'] and s['pure_receiver_additions'] and s['no_unrelated_loss'] for s in scopes)
                    and all(r['passed'] for r in fixtures) and all(r['rejected'] for r in negatives)
                    and scopes[0]['final_core_gain'],
                compatibility_checks_pass=all(s['compatibility_safe'] and s['historical_compatibility'] != 'STOP_REUSED_ORDINAL' for s in scopes),
                full_verifier_verified=all(s['full_verifier_verified'] for s in scopes))


TOOL = 'ultima_work_research_stage'

def project(source):
    """Existing complete-line head/tail algorithm with design's per-source cap."""
    lines = list(enumerate(source['text'].splitlines(), 1))
    view = dict(source_id=source['source_id'], lines=lines, omitted=False)
    if len(compact(view)) > 24000:
        view.update(lines=[], omitted=True)
        half = (24000-len(compact(view)))//2
        def take(rows):
            selected, used = [], 0
            for row in rows:
                used += len(compact(row))+1
                if used > half:
                    break
                selected.append(row)
            return selected
        view['lines'] = take(lines)+list(reversed(take(reversed(lines))))
    visible = set(n for n, _ in view['lines'])
    omitted = []
    for n in range(1, len(lines)+1):
        if n not in visible:
            if omitted and omitted[-1][1] == n-1:
                omitted[-1][1] = n
            else:
                omitted.append([n,n])
    assert len(compact(view)) <= 24000
    return view, omitted


def cards(wr, source, view):
    """Small projection adapter; same parser, witness, selection and padding rules."""
    visible = dict(view['lines'])
    suffix = PurePosixPath(urlsplit(source['final_url']).path).suffix.lower()
    syntax = None
    if suffix == '.py':
        syntax = list(wr._python_witnesses(source['body']))
    elif suffix in ('.ts','.js','.mjs','.cjs'):
        syntax = wr._js_tokens(source['body'],suffix)
    anchors = sorted({a for a in wr._anchors(source,visible,syntax) if a[1]-a[0]<8
                      and all(i in visible for i in range(a[0],a[1]+1))})
    selected = []
    for limitations in (True,False):
        group = [a for a in anchors if (a[2]=='limitation') == limitations]
        n = min(len(group),48-len(selected))
        selected.extend(group[round(i*(len(group)-1)/max(n-1,1))] for i in range(n))
    table = {}
    for number, (first,last,kind,operation) in enumerate(sorted(selected),1):
        left,right = first,last
        padding = 7-(last-first)
        for _ in range(padding//2):
            if left-1 not in visible: break
            left -= 1
        for _ in range(padding-padding//2):
            if right+1 not in visible: break
            right += 1
        fact = dict(kind=kind,claim=operation or 'witness',first_line=first,last_line=last)
        if kind == 'code': fact['symbol'] = operation
        witness = wr._fact_evidence(fact,source,visible,syntax)
        table[number] = dict(witness, symbol=operation, citation_first=left,citation_last=right)
    if not table: raise ValueError('unused_preflight: no usable anchor')
    return table


def schema_for(token, table):
    def obj(**props):
        return dict(type='object',additionalProperties=False,required=list(props),properties=props)
    def text(n): return dict(type='string',minLength=1,maxLength=n)
    line_range = obj(lo=dict(type='integer',minimum=1), hi=dict(type='integer',minimum=1))
    fact = obj(claim=text(400),ref=dict(type='integer',enum=list(table)),
               ranges=dict(type='array',minItems=1,maxItems=3,items=line_range))
    token_shape = dict(type='string',enum=[token])
    local = {'oneOf':[obj(stage_token=token_shape,facts=dict(type='array',minItems=1,maxItems=4,items=fact)),
                      obj(stage_token=token_shape,unused_reason=text(200))]}
    return {'anyOf':[obj(action=dict(type='string',enum=[TOOL]),action_input=local),obj(final_answer=text(1000))]}


def main():
    require(not sys.flags.optimize and sys.dont_write_bytecode and sys.flags.utf8_mode, 'Require unoptimized -B -X utf8')
    require(Path(sys.executable).resolve() == (H/'tools/venv-openjarvis/Scripts/python.exe').resolve(), 'Interpreter mismatch')
    require(not OUT.exists(), 'Preexisting actual-r1: STOP, never retry')
    for ancestor in (PREP, *PREP.parents):
        info = ancestor.lstat()
        require(not getattr(info, 'st_file_attributes', 0) & 0x400, 'Output ancestor reparse boundary')
    OUT.mkdir(exist_ok=False)
    sys.addaudithook(audit)
    sys.settrace(deadline)
    sys.path.insert(0, str(C))
    manifest = None
    result = dict(status='INCOMPLETE', model_calls=0, product_edits=0, E02='NOT_PASSED', T2='NOT_PASSED', T3='NOT_RELEASED')
    try:
        manifest = read(PREP/'manifest.json')
        for path, expected in manifest['bound_hashes'].items():
            require(sha(Path(path).read_bytes()) == expected, 'Hash mismatch: '+path)
        before = boundary(manifest)
        save('boundary-before.json', before)
        require(before['source21_match'] and before['source21_snapshot_sha256'] == manifest['bound_hashes'][manifest['source21_path']], 'Source21 mismatch')
        require(before['heads'] == manifest['expected_heads'], 'C/H HEAD mismatch')
        require(all(p['verified'] for p in before['protected5']), 'Protected5 unverifiable or changed')
        result.update(run(manifest))
        result['status'] = 'PASS' if result['representation_checks_pass'] and result['compatibility_checks_pass'] and result['full_verifier_verified'] else 'FAIL'
        if not result['full_verifier_verified']:
            result.update(status='INCOMPLETE', reason='Real full verifier incomplete; acceptance STOP')
    except BaseException as exc:
        result.update(status='INCOMPLETE', exception=repr(exc))
    finally:
        sys.settrace(None)
        if manifest:
            try:
                after = boundary(manifest)
                save('boundary-after.json', after)
                hashes_after = {path:sha(Path(path).read_bytes()) for path in manifest['bound_hashes']}
                save('bound-hashes-after.json', hashes_after)
                result['all_bound_hashes_unchanged'] = hashes_after == manifest['bound_hashes']
                result['boundary_unchanged'] = 'before' in locals() and after == before
                if not result['boundary_unchanged'] or not all(p['verified'] for p in after['protected5']):
                    result.update(status='INCOMPLETE', boundary_error='Drift or unverifiable boundary')
                if not result['all_bound_hashes_unchanged']:
                    result.update(status='INCOMPLETE', hash_error='Bound input or preparation file drift')
            except BaseException as exc:
                result.update(status='INCOMPLETE', boundary_error=repr(exc))
        result['elapsed_seconds'] = time.monotonic()-ENTRY
        result['prohibited_attempts'] = PROHIBITED_ATTEMPTS
        if PROHIBITED_ATTEMPTS:
            result.update(status='INCOMPLETE', reason='Prohibited effect attempted, including caught attempts')
        if result['elapsed_seconds'] >= 1800:
            result.update(status='INCOMPLETE', timeout=True)
        save('result.json', result)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
