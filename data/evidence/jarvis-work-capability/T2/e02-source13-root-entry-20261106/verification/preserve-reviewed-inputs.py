from pathlib import Path
import hashlib
import json
import subprocess
E=Path(__file__).resolve().parents[1];repo=Path(r'H:\UltimaAI\UltimaAgent')
commit='83312d5f9573ff9cce2a9e331ce70e84e483888c'
manifest=json.loads((E/'manifest.json').read_bytes())
paths=[row['path'] for row in manifest['files']]+['manifest.json','entry-manifest.json']
paths=list(dict.fromkeys(paths))
prefix=E.relative_to(repo).as_posix()+'/'
queries=''.join(commit+':'+prefix+name+'\n' for name in paths).encode()
raw=subprocess.run(['git','-C',str(repo),'cat-file','--batch'],input=queries,capture_output=True,check=True).stdout
target=E/'history/reviewed-83312d5';target.mkdir(parents=True,exist_ok=False)
cursor=0
for name in paths:
    end=raw.index(b'\n',cursor);head=raw[cursor:end].decode().split();assert head[1]=='blob'
    size=int(head[2]);body=raw[end+1:end+1+size];assert raw[end+1+size:end+2+size]==b'\n';cursor=end+2+size
    dest=target/name;assert dest.resolve().is_relative_to(target.resolve())
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(body)
assert cursor==len(raw)
for row in manifest['files']:
    assert hashlib.sha256((target/row['path']).read_bytes()).hexdigest()==row['sha256']
with (target/'independent-preparation-review.json').open('xb') as f:f.write((E/'review/independent-preparation-review.json').read_bytes())
print(json.dumps(dict(preserved=len(paths),reviewed_commit=commit,history=str(target))))
