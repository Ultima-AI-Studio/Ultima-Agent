import json,os,sys,unittest,subprocess,time
from pathlib import Path
sys.path.insert(0,r'H:\UltimaAI\UltimaAgent')
sys.path.insert(0,r'H:\UltimaAI\UltimaAgent\tasks\tests')
import test_audit_e2e as fixture
from tasks.queue_engine.dispatcher import Dispatcher,DispatchLock
from tasks.queue_engine.audit import RecoveryManager
from tasks.queue_engine.priority_deps import QueuePlanner
from tasks.queue_engine.dispatcher import BACKGROUND_CREATION_FLAGS

class ReviewRegression(unittest.TestCase):
    def setUp(self):
        self.f=fixture.AuditE2ETests('test_no_receipt_is_blocked_and_never_completed')
        self.f.setUp()
    def tearDown(self): self.f.tearDown()
    def test_nonexistent_artifact_cannot_pass_audit(self):
        task=self.f.put_in_audit()
        result=self.f.audit_engine.audit(task,self.f.receipt(self.f.task_root/'missing.txt'),self.f.summary(),auditor_skill='eng.audit')
        self.assertNotEqual(result.verdict,'PASS')
    def test_planner_cannot_overwrite_while_dispatch_transaction_is_locked(self):
        QueuePlanner(self.f.storage).enqueue(self.f.task())
        with DispatchLock(self.f.task_root/'.dispatch.lock'):
            with self.assertRaises(RuntimeError):
                QueuePlanner(self.f.storage).adjust_priority('e2e',60,actor='brain',reason='concurrent edit')
        self.assertEqual(self.f.storage.load_tasks()[0]['priority'],50)
    def test_reused_live_pid_does_not_match_historical_session(self):
        paths=self.f.storage.create_run_artifacts('reuse')
        paths['session'].write_text(json.dumps({'pid':os.getpid(),'process_identity':'wrong-process-creation-token','started_at':'2000-01-01'}))
        self.assertFalse(Dispatcher(self.f.storage)._session_running('reuse'))
    def test_recovery_does_not_block_a_live_child_without_done(self):
        QueuePlanner(self.f.storage).enqueue(self.f.task())
        dispatcher=Dispatcher(self.f.storage)
        decision=dispatcher.dispatch('e2e',[sys.executable,'-c',"import time;time.sleep(1);print('{\"business_success\":true}')"])
        self.assertTrue(decision.dispatched)
        handle=dispatcher.take_process(decision.pid)
        try:
            task,_=RecoveryManager(self.f.storage).recover_finished_run('e2e')
            self.assertEqual(task['state'],'EXECUTING')
        finally: handle.wait(timeout=5)
    def test_real_parent_death_leaves_durable_child_completion(self):
        task=self.f.task()
        QueuePlanner(self.f.storage).enqueue(task)
        counter=self.f.task_root/'counter.txt'
        child="import time;from pathlib import Path;time.sleep(0.3);Path("+repr(str(counter))+").write_text('1');print('{\"business_success\":true}')"
        parent=("import sys,os;sys.path.insert(0,r'H:\\UltimaAI\\UltimaAgent');"
                "from tasks.queue_engine.storage import QueueStorage;"
                "from tasks.queue_engine.dispatcher import Dispatcher;"
                "d=Dispatcher(QueueStorage("+repr(str(self.f.task_root))+"));"
                "r=d.dispatch('e2e',"+repr([sys.executable,'-c',child])+");"
                "assert r.dispatched;os._exit(0)")
        result=subprocess.run([sys.executable,'-c',parent],creationflags=BACKGROUND_CREATION_FLAGS,capture_output=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)
        paths=list((self.f.storage.runs_dir/'e2e').glob('*.done'))
        deadline=time.monotonic()+5
        while time.monotonic()<deadline and (not paths or not paths[0].stat().st_size):
            time.sleep(.05)
            paths=list((self.f.storage.runs_dir/'e2e').glob('*.done'))
        self.assertTrue(paths and paths[0].stat().st_size,'parent death lost durable completion')
        recovered,_=RecoveryManager(self.f.storage).recover_finished_run('e2e')
        self.assertEqual(recovered['state'],'SELF-CHECK')
        self.assertEqual(counter.read_text(),'1')
    def test_old_audit_pass_cannot_close_a_changed_task_revision(self):
        QueuePlanner(self.f.storage).enqueue(self.f.task())
        artifact=self.f.task_root/'artifact.txt';artifact.write_text('ok')
        dispatcher=Dispatcher(self.f.storage)
        result=dispatcher.dispatch('e2e',[sys.executable,'-c',"print('{\"business_success\":true}')"])
        dispatcher.take_process(result.pid).wait(timeout=5)
        recovery=RecoveryManager(self.f.storage)
        recovery.recover_finished_run('e2e')
        task=recovery.finish_self_check_from_run('e2e')
        approved=self.f.audit_engine.audit(task,self.f.receipt(artifact),self.f.summary(),auditor_skill='eng.audit')
        self.assertEqual(approved.verdict,'PASS')
        changed=self.f.storage.load_tasks();changed[0]['updated_at']='new-retry-revision'
        self.f.storage.save_tasks(changed)
        with self.assertRaises(ValueError): self.f.audit_engine.close('e2e',approved)
        self.assertEqual(self.f.storage.load_tasks()[0]['state'],'AUDIT')

if __name__=='__main__': unittest.main()
