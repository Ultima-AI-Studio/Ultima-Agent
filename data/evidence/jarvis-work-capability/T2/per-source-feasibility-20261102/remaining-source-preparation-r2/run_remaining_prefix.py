"""Evidence-only remaining-source launcher. No authority is issued by this file."""
import sys

# Must run even on import, before filesystem access or CLI handling.
if sys.flags.optimize:
    raise RuntimeError('Optimized Python execution is prohibited')
sys.dont_write_bytecode = True

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import time

E = Path('H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/per-source-feasibility-20261102')
PREP = E/'remaining-source-preparation-r2'
ACTUAL = E/'remaining-source-actual'
# Independently fixed trust anchor; never derive ownership from ACTUAL.resolve().
TRUSTED_ACTUAL = Path('H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/per-source-feasibility-20261102/remaining-source-actual')
CORE = E/'preparation-r2/run_stage_prefix.py'
CORE_HASH = '4122c8d0c288689f31899fc59cebf7aabbcc546c46342071134af712d4a9863e'
OLD_MANIFEST = E/'preparation-r2/manifest.json'
OLD_HASH = '02d0cd4ee8ae5f502a7c35cf6c630c07b5bd591922cb00eee1bde7265651e1ca'
ORIGINAL = E/'S2-first/first-f53a803-r2/outcome.json'
ORIGINAL_HASH = '597467ca6cd98cf271eaa6a5a62181a614023c591b2a87d66c75eb4df42739aa'
REVIEW = E.parent/'review-per-source-probe-r2/verdict.json'
REVIEW_HASH = '97585bb9f82f9456cfaf658f9ba73c141f85ea7780401f79c866d627baa5a25c'
HEAD = 'f53a803afbb550b20aff2fd95859a563f6c8cc41'
ORDER = ('S3', 'S1', 'S4')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(path, digest):
    if sha(path) != digest:
        raise ValueError('Hash mismatch: '+str(path))


def read(path):
    def unique(pairs):
        out = dict(pairs)
        if len(out) != len(pairs):
            raise ValueError('Duplicate JSON key')
        return out
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def refuse_reparse(path):
    # Inspect unresolved ancestors: resolve() hides Windows junctions.
    for part in (Path(path), *Path(path).parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Reparse points are not authorized in managed paths')


def trusted_namespace():
    refuse_reparse(TRUSTED_ACTUAL)
    refuse_reparse(ACTUAL)
    if ACTUAL != TRUSTED_ACTUAL or TRUSTED_ACTUAL.resolve() != TRUSTED_ACTUAL:
        raise ValueError('Actual namespace differs from fixed trusted root')
    return TRUSTED_ACTUAL.resolve()


def managed_run(path, source):
    raw = Path(path)
    refuse_reparse(raw)
    trusted = trusted_namespace()
    if (not raw.is_absolute() or '..' in raw.parts or source not in ORDER or
            not raw.name or ':' in raw.name or
            raw != TRUSTED_ACTUAL/source/raw.name):
        raise ValueError('Noncanonical managed attempt path')
    resolved = raw.resolve()
    if resolved != raw or resolved.parent != trusted/source or not resolved.is_relative_to(trusted):
        raise ValueError('Attempt outside fixed trusted namespace')
    return resolved


def frozen_core():
    checked(CORE, CORE_HASH)
    spec = importlib.util.spec_from_file_location('remaining_frozen_core', CORE)
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    return core


def snapshot_gate(auth, now=None):
    checked(auth['snapshot_path'], auth['snapshot_sha256'])
    snap = read(auth['snapshot_path'])
    age = (time.time() if now is None else now)-snap['captured_unix']
    if not 0 <= age <= 30:
        raise ValueError('Snapshot must be at most 30 seconds old')
    if any(type(snap[k]) not in (int, float) or not math.isfinite(snap[k]) or snap[k] < minimum for k, minimum in
           [('available_ram_bytes',12*2**30), ('commit_headroom_bytes',16*2**30), ('gpu_free_bytes',8*2**30)]):
        raise ValueError('Precautionary resource minimum not met')
    expected = read(E/'S2-first-root-reconciliation.json')['protected_processes_after']
    if (snap['head'] != HEAD or snap['selected_digest'] != auth['digest'] or
            snap['protected5'] != expected or snap['protected5_unchanged'] is not True):
        raise ValueError('Snapshot identity proof differs')
    return snap


def validate(auth, runroot, *, now=None):
    """All admission checks precede namespace creation, SDK setup and sockets."""
    trusted_namespace()
    core = frozen_core()
    if (auth['mode'] != 'remaining_source_sdk_prefix' or auth['execute'] is not True or
            auth['head'] != HEAD or auth['digest'] != core.DIGEST or
            type(auth['max_native_posts']) is not int or auth['max_native_posts'] != 1 or
            type(auth['group_total_cap']) is not int or auth['group_total_cap'] != 4):
        raise ValueError('Authority limits differ')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=core.CHECKOUT,text=True).strip() != HEAD:
        raise ValueError('Checkout HEAD differs')
    checked(CORE, auth['core_sha256'])
    if auth['core_sha256'] != CORE_HASH or auth['frozen_manifest_sha256'] != OLD_HASH:
        raise ValueError('Frozen identity differs')
    checked(OLD_MANIFEST, OLD_HASH)
    checked(REVIEW, REVIEW_HASH)
    checked(ORIGINAL, ORIGINAL_HASH)
    if auth['original_outcome_sha256'] != ORIGINAL_HASH:
        raise ValueError('Original spent packet differs')
    manifest_path = PREP/'manifest.json'
    checked(manifest_path, auth['launcher_manifest_sha256'])
    manifest = read(manifest_path)
    for path, digest in manifest['frozen_files'].items():
        checked(path, digest)
    old = read(OLD_MANIFEST)
    for path, digest in {**old['frozen_files'], **old['input_files']}.items():
        checked(path, digest)
    prior = auth['previous_attempts']
    if not isinstance(prior, list) or len(prior) > 2:
        raise ValueError('Invalid prior attempt count')
    source = auth['source_id']
    if source != ORDER[len(prior)] or auth['next_source'] != source:
        raise ValueError('S2, skipped source, duplicate or retry prohibited')
    if type(auth['cumulative_spent_before']) is not int or auth['cumulative_spent_before'] != 1+len(prior):
        raise ValueError('Original S2 and every consumed namespace must remain spent')
    if auth['cumulative_spent_before']+1 > 4:
        raise ValueError('Cumulative cap exceeded')
    known = set()
    for index, item in enumerate(prior):
        root = managed_run(item['run_root'], ORDER[index])
        if item['source_id'] != ORDER[index]:
            raise ValueError('Prior source or exact runroot differs')
        packet = root/'outcome.json'
        refuse_reparse(packet)
        checked(packet, item['outcome_sha256'])
        outcome = read(packet)
        checked(item['review_path'], item['review_sha256'])
        verdict = read(item['review_path'])
        if (verdict['verdict'] != 'PASS' or verdict['source_id'] != ORDER[index] or
                Path(verdict['run_root']).resolve() != root or
                verdict['outcome_sha256'] != item['outcome_sha256'] or
                outcome['source_id'] != ORDER[index] or
                outcome['status'] != 'PENDING_INDEPENDENT_FACT_REVIEW' or
                outcome['native_posts'] != 1 or outcome['native_post_intents'] != 1 or
                outcome['confirmed'] is not True or not outcome['stage_payload'].get('facts')):
            raise ValueError('Prior actual packet requires bound independent factual PASS')
        known.add(root)
    # Inspect the complete namespace; root may not omit failed/zero-POST attempts.
    existing = set()
    if ACTUAL.exists():
        for directory in ACTUAL.iterdir():
            refuse_reparse(directory)
            if directory.name not in ORDER or not directory.is_dir():
                raise ValueError('Unexpected actual namespace entry')
            for child in directory.iterdir():
                refuse_reparse(child)
                if not child.is_dir():
                    raise ValueError('Unexpected attempt entry')
                existing.add(managed_run(child, directory.name))
    if existing != known:
        raise ValueError('Unlisted, failed, preexisting or repeated attempt')
    root = managed_run(runroot, source)
    if (root != managed_run(auth['run_root'], source) or root.exists()):
        raise ValueError('Exclusive controller-unique exact source runroot required')
    snap = snapshot_gate(auth, now)
    return core, old, snap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--authority',required=True,type=Path)
    parser.add_argument('--run-root',required=True,type=Path)
    args = parser.parse_args()
    auth = read(args.authority)
    core, old, snap = validate(auth,args.run_root)
    args.run_root.mkdir(parents=True,exist_ok=False)  # consumption even if no POST
    core.save(args.run_root/'admission.json',dict(authority=auth,authority_sha256=sha(args.authority),snapshot=snap))
    os.environ['NO_PROXY']='localhost,127.0.0.1,::1'
    for name in ('TEMP','TMP','TMPDIR','OPENJARVIS_HOME','HF_HOME','XDG_CACHE_HOME'):
        os.environ[name]=str(args.run_root/name.lower()); Path(os.environ[name]).mkdir()
    os.environ['HF_HUB_OFFLINE']=os.environ['TRANSFORMERS_OFFLINE']='1'
    if 'OLLAMA_API_KEY' in os.environ:
        raise ValueError('Unexpected Ollama credential')
    core.socket_guard()
    sys.path.insert(0,str(core.CHECKOUT))
    import httpx
    from src.brain import agent_server
    records=[]; phase=['owner_bootstrap_readiness_before_t0']; owner=None; output=None
    try:
        snapshot_gate(auth)  # fresh immediately before normal SDK bootstrap
        with core.observe_http(records,lambda:phase[0]):
            owner=core.make_owner(args.run_root/'openjarvis_home')
            owner._ensure_engine()
            if len(records)!=1 or records[0]['method']!='GET' or records[0]['url']!=core.ORIGIN+'/api/tags':
                raise ValueError('Bootstrap metadata cap differs')
            core.save(args.run_root/'bootstrap-readiness.json',dict(requests=records.copy(),native_posts=0,complete_at=time.monotonic()))
            phase[0]='trial'
            with httpx.Client(base_url=core.ORIGIN,trust_env=False,follow_redirects=False,timeout=25) as client:
                output=core.run_prefix(owner,client,args.run_root,auth['source_id'],agent_server._research_manifest_digest,
                                       input_hashes=old['input_files'])
    except Exception as exc:
        output=dict(status='FAILED',source_id=auth['source_id'],error=dict(type=type(exc).__name__,message=str(exc)),
                    phase=phase[0],native_posts=sum(r['method']=='POST' for r in records),effects=[],owner_closed=False)
    finally:
        if owner:
            owner.close()
            if output: output['owner_closed']=True
        core.save(args.run_root/'http-observer.json',records)
        if output: core.save(args.run_root/'outcome.json',output)
    print(core.compact(dict(status=output['status'],run_root=str(args.run_root))))
    return 0 if output['status']=='PENDING_INDEPENDENT_FACT_REVIEW' else 1


if __name__=='__main__':
    raise SystemExit(main())
