"""Root allocation tests use temporary data and a fake released-call boundary."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,tempfile,unittest
from unittest.mock import patch
N=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('entry_under_test',N/'code/entry.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v),encoding='utf8')

class RootAllocation(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.now=dt.datetime.now(dt.timezone.utc)
        self.patcher=patch.object(e,'N',self.root);self.patcher.start();self.addCleanup(self.patcher.stop)
        files={}
        for name in ('code/entry.py','code/bindings.py','harness/adapter.py','harness/manifest.json','inputs/input-manifest.json','execution-proposal.md'):
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'bound source');files[name]=sha(p)
        self.manifest=dict(kind='SOURCE13_REAL_CONTROLLED_PREPARATION',candidate=e.CANDIDATE,model=e.MODEL,model_digest=e.DIGEST,actual_released=False,files=files)
        write(self.root/'manifest.json',self.manifest)
        self.review=dict(reviewer='root-independent',verdict='PASS_PREPARATION_ONLY',manifest_sha256=sha(self.root/'manifest.json'),actual_run_authorized=False)
        write(self.root/'review/independent-preparation-review.json',self.review)
        self.approval=dict(reviewer='root-independent',overall='PASS',manifest_sha256=sha(self.root/'harness/manifest.json'),review_sha256=sha(self.root/'review/independent-preparation-review.json'),preparation_manifest_sha256=sha(self.root/'manifest.json'))
        write(self.root/'harness-approval.json',self.approval)
        self.grant=dict(schema=1,kind=e.KIND,source='user_explicit',question_id='call_future_real8b_case',answer='授权一次真实8B受控研究及独立结果复核',candidate=e.CANDIDATE,model=e.MODEL,model_digest=e.DIGEST,
            manifest_sha256=sha(self.root/'manifest.json'),review_sha256=sha(self.root/'review/independent-preparation-review.json'),
            case='E02-controlled-1',actual_case_allocation=1,result_review_allocation=1,retry=0,issued_at=self.now.isoformat(),expires_at=(self.now+dt.timedelta(seconds=120)).isoformat())
        write(self.root/'release/user-allocation.json',self.grant)
    def package(self):return e.read_ready(self.root)
    def reject_ready(self):
        with self.assertRaises((ValueError,FileNotFoundError)):self.package()
    def reject_release(self):
        with self.assertRaises((ValueError,FileNotFoundError)):e.read_release(self.root,self.package(),self.now)
    def test_accepts_reviewed_package_and_current_grant(self):
        self.assertEqual(e.read_release(self.root,self.package(),self.now),self.grant)
    def test_missing_independent_review(self):
        (self.root/'review/independent-preparation-review.json').unlink();self.reject_ready()
    def test_author_review_is_not_independent(self):
        self.review['reviewer']='author';write(self.root/'review/independent-preparation-review.json',self.review);self.reject_ready()
    def test_nonpass_review(self):
        self.review['verdict']='NEEDS_FIXES';write(self.root/'review/independent-preparation-review.json',self.review);self.reject_ready()
    def test_changed_source(self):
        (self.root/'code/entry.py').write_bytes(b'drift');self.reject_ready()
    def test_changed_manifest(self):
        self.manifest['actual_released']=True;write(self.root/'manifest.json',self.manifest);self.reject_ready()
    def test_wrong_candidate_or_digest(self):
        for key in ('candidate','model_digest'):
            with self.subTest(key=key):
                grant=dict(self.grant);grant[key]='other';write(self.root/'release/user-allocation.json',grant);self.reject_release()
    def test_other_model(self):
        self.grant['model']='qwen2.5:14b';write(self.root/'release/user-allocation.json',self.grant);self.reject_release()
    def test_missing_grant(self):
        (self.root/'release/user-allocation.json').unlink();self.reject_release()
    def test_expired_grant(self):
        self.grant['expires_at']=self.now.isoformat();write(self.root/'release/user-allocation.json',self.grant);self.reject_release()
    def test_extended_ttl(self):
        self.grant['expires_at']=(self.now+dt.timedelta(seconds=121)).isoformat();write(self.root/'release/user-allocation.json',self.grant);self.reject_release()
    def test_future_grant(self):
        self.grant['issued_at']=(self.now+dt.timedelta(seconds=1)).isoformat();write(self.root/'release/user-allocation.json',self.grant);self.reject_release()
    def test_old_zero_inference_allocation(self):
        self.grant['question_id']='call_e9e5dd014d9b43f4b529f09bd2487d52';write(self.root/'release/user-allocation.json',self.grant);self.reject_release()
    def test_second_case_or_retry(self):
        for field,value in [('case','E02-controlled-2'),('retry',1),('actual_case_allocation',2),('result_review_allocation',0),('actual_case_allocation',True)]:
            with self.subTest(field=field,value=value):
                grant=dict(self.grant);grant[field]=value;write(self.root/'release/user-allocation.json',grant);self.reject_release()
    def test_grant_cannot_supply_clock_or_parent(self):
        for key in ('parent_identity','origin_ns'):
            with self.subTest(key=key):
                grant=dict(self.grant);grant[key]=1;write(self.root/'release/user-allocation.json',grant);self.reject_release()
    def test_wrong_root(self):
        with self.assertRaises(ValueError):e.read_ready(self.root/'other')
    def test_traversal_manifest(self):
        self.manifest['files']['../escape']='0'*64;write(self.root/'manifest.json',self.manifest);self.reject_ready()
    def test_changed_harness_approval(self):
        self.approval['review_sha256']='0'*64;write(self.root/'harness-approval.json',self.approval);self.reject_ready()
    def test_no_grant_no_released_call(self):
        (self.root/'release/user-allocation.json').unlink()
        with patch.object(e,'run_released') as called:
            with self.assertRaises((ValueError,FileNotFoundError)):e.run_once(self.root)
            called.assert_not_called()
        self.assertFalse((self.root/'release/consumed.json').exists())
    def test_exactly_one_call_after_exclusive_consumption(self):
        def boundary(root,grant,package):
            self.assertTrue((root/'release/consumed.json').is_file())
            return dict(status='PENDING_ROOT_INDEPENDENT_REVIEW',witness={'eligible':True})
        with patch.object(e,'run_released',side_effect=boundary) as called:
            result=e.run_once(self.root)
            self.assertEqual(result['status'],'PENDING_ROOT_INDEPENDENT_REVIEW')
            with self.assertRaises((ValueError,FileExistsError)):e.run_once(self.root)
            self.assertEqual(called.call_count,1)
    def test_failure_stays_consumed(self):
        with patch.object(e,'run_released',side_effect=RuntimeError('retained first failure')) as called:
            result=e.run_once(self.root)
            self.assertEqual(result['status'],'FAIL')
            self.assertIn('retained first failure',result['error'])
            self.assertTrue((self.root/'release/root-outcome.json').exists())
            with self.assertRaises((ValueError,FileExistsError)):e.run_once(self.root)
            self.assertEqual(called.call_count,1)

if __name__=='__main__':unittest.main(verbosity=2)
