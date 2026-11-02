"""Reproducible preparation-only runner; no actual namespace is touched."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

p=Path(__file__).resolve().parent
env=os.environ.copy()
settings={name:str(p/folder) for name,folder in [('TEMP','temp'),('TMP','temp'),('TMPDIR','temp'),
          ('OPENJARVIS_HOME','sdk-home'),('HF_HOME','cache'),('XDG_CACHE_HOME','cache')]}
settings.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                PYTHONDONTWRITEBYTECODE='1')
env.update(settings)
argv=[sys.executable,'-B','-X','utf8','-m','pytest',str(p/'test_remaining_prefix.py'),'-q',
      '-p','no:cacheprovider','--basetemp',str(p/'pytest-offline'),'--junitxml',str(p/'tests.xml')]
(p/'argv.json').write_text(json.dumps(dict(argv=argv,env=settings,cwd=str(p)),indent=2),encoding='utf8')
with (p/'tests.log').open('w',encoding='utf8') as log:
    result=subprocess.run(argv,cwd=p,env=env,stdout=log,stderr=subprocess.STDOUT)
(p/'tests.exit').write_text(str(result.returncode),encoding='utf8')
print((p/'tests.log').read_text())
raise SystemExit(result.returncode)
