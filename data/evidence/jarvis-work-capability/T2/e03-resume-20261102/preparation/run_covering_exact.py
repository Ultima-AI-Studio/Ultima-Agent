import json,os,subprocess,sys
from pathlib import Path
import acceptance_adapter as a
p=Path(__file__).resolve().parent
folder=p/'covering-exact-owned'; folder.mkdir()
env=a.environment(folder); env['PYTHONPATH']=str(p)+os.pathsep+str(a.ROOT); env['WORK_ACCEPTANCE_PREP_TEST']='covering-exact'
argv=[sys.executable,'-B','-X','utf8','-m','pytest','src/brain/tests/test_work_context.py','src/brain/tests/test_work_delivery.py','-q','-p','no:cacheprovider','--basetemp',str(p/'covering-exact-basetemp'),'--junitxml',str(p/'covering-exact.xml')]
with (p/'covering-exact.log').open('w',encoding='utf-8') as log:
    completed=subprocess.run(argv,cwd=a.ROOT,env=env,stdout=log,stderr=log,timeout=90)
a.save(p/'covering-exact-receipt.json',{'argv':argv,'cwd':str(a.ROOT),'exit_code':completed.returncode,'environment_overrides':{k:env[k] for k in ('TEMP','TMP','TMPDIR','OPENJARVIS_HOME','HF_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','NO_PROXY','PYTHONPATH','WORK_ACCEPTANCE_PREP_TEST','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE')},'reason':'Literal required python -m pytest command, guarded by prep-only sitecustomize; previous same checks through pytest.main also retained'})
proof=a.load(p/'covering-exact-imports.json')
assert not proof['wrong_checkout']
print(json.dumps({'exit_code':completed.returncode,'modules':len(proof['modules'])}))
raise SystemExit(completed.returncode)
