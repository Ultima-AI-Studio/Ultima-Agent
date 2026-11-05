from pathlib import Path
import json,os,subprocess,sys,time
root=Path(r"C:\Users\Administrator\.codex\worktrees\jarvis-e03-source13\UltimaAgent")
evidence=Path(__file__).resolve().parent
label=sys.argv[1]
assert label.replace("-","").isalnum()
log=evidence/(label+".log")
assert not log.exists()
env=os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE="1",PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",PYTHONPATH=str(root)+os.pathsep+str(evidence),PYTHONIOENCODING="utf-8",PYTHONUTF8="1")
sdk_root=evidence/("sdk-"+label)
assert not sdk_root.exists()
sdk_root.mkdir()
env["OPENJARVIS_HOME"]=str(sdk_root)
env["ULTIMA_OFFLINE_GUARD_RECEIPT"]=str(evidence/(label+"-io-guard.json"))
args=[r"H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe","-B","-m","pytest","-q","-p","no:cacheprovider","-p","offline_guards","--basetemp",str(evidence/("tmp-"+label)),*sys.argv[2:]]
started=time.time()
with log.open("w",encoding="utf8") as out:
 result=subprocess.run(args,cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT)
receipt=dict(argv=args,cwd=str(root),started=started,elapsed_seconds=time.time()-started,exit_code=result.returncode,log=str(log),scope="offline tests; no actual E03/model allocation")
(evidence/(label+".json")).write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf8")
print(json.dumps(receipt))
print("\n".join(log.read_text(encoding="utf8").splitlines()[-55:]))
sys.exit(result.returncode)
