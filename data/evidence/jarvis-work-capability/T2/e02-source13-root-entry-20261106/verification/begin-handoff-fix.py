from pathlib import Path
import datetime as dt
import hashlib
import json

E=Path(__file__).resolve().parents[1]
repo=E.parents[4]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)
assert sha(E/'manifest.json')=='2975e0f947be408baaa4222f8dd9fd4fbd1cb481adf005f38ea1bc4d8b91c3aa'
manifest=json.loads((E/'manifest.json').read_bytes())
target=E/'history/reviewed-a19a00b'
target.mkdir(parents=True,exist_ok=False)
names=[row['path'] for row in manifest['files']]
for row in manifest['files']:
    assert sha(E/row['path'])==row['sha256'],row['path']
names+=['manifest.json','entry-manifest.json','review/independent-fixed-source-review.json',
        'verification/fixed-source-review-disposition.json']
for name in dict.fromkeys(names):
    dest=target/name
    assert dest.resolve().is_relative_to(target.resolve())
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as stream:stream.write((E/name).read_bytes())
    assert sha(dest)==sha(E/name)
save(E/'verification/handoff-fix-authorization.json',dict(schema=1,recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    authority='explicit-user-reply',question_id='call_e84ac425972c431b843164937a72fe99',
    answer='授权完成本缺口补修与必要独审（推荐）',scope='R1-followup minimal offline repair, validation and necessary independent preparation reviews',
    proposal=str(repo/'docs/plans/jarvis-work-e02-source13-cleanup-handoff-fix-plan-20261106.md'),
    source_checkpoint='a19a00b6d8cceb9784330a4b973d16942b851988',
    history=str(target),preserved_files=len(set(names)),
    actual_profile_runs=0,model_calls=0,native_workers=0,UI=0,audio=0,service_operations=0,
    result_reviews=0,runtime_authority=False))
print(json.dumps(dict(preserved_files=len(set(names)),history=str(target),runtime_authority=False)))
