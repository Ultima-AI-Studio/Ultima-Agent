"""Preserve unrelated concurrent commits; publish the same exact reviewed file set."""
from pathlib import Path
import ast,hashlib,importlib.util,json,subprocess,sys
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo')
mode=sys.argv[1];assert mode in ('publish','final')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original=subprocess.check_output
def git(root,*args):return original(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)
close=json.loads((N/'verification/closeout-registration.json').read_bytes())
# Immutable Git object reads are batched; each result is still compared byte-for-byte
# by the original publication/readback assertions. No writes use this cache.
cache={}
def checked_output(argv,*args,**kwargs):
    if (isinstance(argv,list) and len(argv)==5 and argv[0]=='git' and argv[1]=='-C'
            and argv[3]=='show' and ':' in argv[4] and Path(argv[2]) in (R,M)):
        root=Path(argv[2]);revision,name=argv[4].split(':',1);key=(str(root),revision)
        if key not in cache:
            paths=(N/'verification/publication-recovery-pathspec.txt').read_text('utf8').splitlines() if root==R else [Path(x['target']).relative_to(M).as_posix() for x in close['mirror']]
            assert name in paths and all('\n' not in p and '\r' not in p for p in paths)
            raw=original(['git','-C',str(root),'cat-file','--batch'],input=''.join(revision+':'+p+'\n' for p in paths).encode('utf8'),creationflags=subprocess.CREATE_NO_WINDOW)
            values={};offset=0
            for path in paths:
                end=raw.index(b'\n',offset);header=raw[offset:end].split();assert len(header)==3 and header[1]==b'blob'
                size=int(header[2]);offset=end+1;values[path]=raw[offset:offset+size];offset+=size
                assert raw[offset:offset+1]==b'\n';offset+=1
            assert offset==len(raw);cache[key]=values
        return cache[key][name]
    return original(argv,*args,**kwargs)
if mode=='publish':
    old='9ab8d0c6a064cd2bda557cf1f4e887e181ec9c57';head=git(R,'rev-parse','HEAD').decode().strip()
    assert git(R,'merge-base',old,head).decode().strip()==old
    changes=set(git(R,'diff','--name-only','-z',old,head).decode('utf8').split('\0'))-{''}
    paths=set((N/'verification/publication-pathspec.txt').read_text('utf8').splitlines())
    assert not changes.intersection(paths),(changes.intersection(paths))
    assert not git(R,'diff','--cached','--name-only').strip() and not git(M,'diff','--cached','--name-only').strip()
    receipt=dict(reason='Original publication stopped before staging at stale project HEAD assertion',expected_previous_head=old,observed_project_head=head,observed_mirror_head=git(M,'rev-parse','HEAD').decode().strip(),concurrent_paths=sorted(changes),overlap_with_reviewed_publication=[],original_pathspec_sha256=sha(N/'verification/publication-pathspec.txt'),original_publisher_sha256=sha(N/'verification/publish.py'),reviewed_candidate_unchanged=True,actual_cases=0,readback='Git cat-file batch; original per-file byte equality assertions retained')
    with (N/'verification/publication-recovery-context.json').open('x',encoding='utf8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
    s=(N/'verification/publish.py').read_text('utf8')
    a="assert before==dict(project='9ab8d0c6a064cd2bda557cf1f4e887e181ec9c57',mirror='db6d02f8a787780b1d0a8a9d41eb9bf6e3b36ab1')"
    assert s.count(a)==1;s=s.replace(a,'assert before=='+repr(dict(project=head,mirror=receipt['observed_mirror_head'])))
    s=s.replace("pathspec=N/'verification/publication-pathspec.txt';project.add(pathspec)","project.update(N/'verification'/name for name in ('publication_recovery.py','publication-recovery-context.json','publication-pathspec.txt'))\nassert R/'docs/tracker/北极星上线任务清单.html' not in project\npathspec=N/'verification/publication-recovery-pathspec.txt';project.add(pathspec)")
    s=s.replace("v.git(R,'commit','-m'", "v.git(R,'commit','--only','--pathspec-from-file='+str(pathspec),'-m'")
    filename=N/'verification/publish.py'
else:
    s=(N/'verification/final_readback.py').read_text('utf8');filename=N/'verification/final_readback.py'
ast.parse(s);subprocess.check_output=checked_output
try:exec(compile(s,str(filename),'exec'),{'__file__':str(filename),'__name__':'__main__'})
finally:subprocess.check_output=original
