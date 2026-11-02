import json,os,sys,time
from pathlib import Path
folder=Path(sys.argv[1]); (folder/'child.json').write_text(json.dumps({'pid':os.getpid(),'parent':os.getppid(),'exe':sys.executable}))
deadline=time.monotonic()+25
while time.monotonic()<deadline and not (folder/'stop').exists(): time.sleep(.05)
