import json
from pathlib import Path
p=Path(__file__).resolve().parents[2]/'w2-independent-acceptance-20261021.md'
t=p.read_text(encoding='utf-8')
rows=[line for line in t.splitlines() if line.startswith(tuple('| '+x+'-' for x in ['ST','SM','DI','PD','AU']))]
counts={value:sum(('| '+value+' |') in row for row in rows) for value in ['通过','失败','未验证']}
result={'rows':len(rows),'counts':counts,'report_bytes':p.stat().st_size,'first_readback_failure':'inline python command quoting SyntaxError; corrected using saved script'}
assert len(rows)==35 and counts=={'通过':28,'失败':4,'未验证':3},result
Path(__file__).with_name('readback.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(result)
