import argparse,socket,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--runtime-root');p.add_argument('--work-output-root');p.add_argument('--query');p.add_argument('--port',type=int);a=p.parse_args()
root=Path(a.runtime_root).parent
sock=socket.socket();sock.bind(('127.0.0.1',a.port));sock.listen()
(root/'ready').touch();deadline=time.monotonic()+45
while time.monotonic()<deadline and not (root/'stop').exists(): time.sleep(.03)
sock.close()
