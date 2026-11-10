"""Root allocation tests use temporary data and a fake released-call boundary."""
from pathlib import Path
import ast,contextlib,datetime as dt,hashlib,importlib.util,json,tempfile,types,unittest
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

    def direct_grant(self):
        path=N/'inputs/direct-user-decision.json';decision=json.loads(path.read_bytes())
        target=self.root/'inputs/direct-user-decision.json';target.write_bytes(path.read_bytes())
        self.manifest['files']['inputs/direct-user-decision.json']=sha(target)
        write(self.root/'manifest.json',self.manifest)
        self.review['manifest_sha256']=sha(self.root/'manifest.json');write(self.root/'review/independent-preparation-review.json',self.review)
        self.approval.update(preparation_manifest_sha256=sha(self.root/'manifest.json'),review_sha256=sha(self.root/'review/independent-preparation-review.json'))
        write(self.root/'harness-approval.json',self.approval)
        self.grant.update(question_id=decision['decision_id'],answer=decision['answer'],
            manifest_sha256=sha(self.root/'manifest.json'),review_sha256=sha(self.root/'review/independent-preparation-review.json'))
        write(self.root/'release/user-allocation.json',self.grant)

    def test_direct_user_message_exactly_bound_is_accepted(self):
        self.direct_grant();self.assertEqual(e.read_release(self.root,self.package(),self.now),self.grant)

    def test_direct_message_wrong_answer_or_identity_is_rejected(self):
        self.direct_grant();original=dict(self.grant)
        for field,value in [('question_id','user-message:forged'),('answer','继续'),('answer','')]:
            self.grant=dict(original);self.grant[field]=value
            write(self.root/'release/user-allocation.json',self.grant);self.reject_release()

    def test_direct_message_changed_file_is_rejected(self):
        self.direct_grant();(self.root/'inputs/direct-user-decision.json').write_bytes(b'{}');self.reject_release()

    def test_direct_message_missing_file_is_rejected(self):
        self.direct_grant();(self.root/'inputs/direct-user-decision.json').unlink();self.reject_release()

    def test_direct_message_same_original_expiry_is_required(self):
        self.direct_grant();self.grant['expires_at']=(self.now-dt.timedelta(seconds=1)).isoformat()
        write(self.root/'release/user-allocation.json',self.grant);self.reject_release()

    def test_direct_message_is_consumed_before_one_case_only(self):
        self.direct_grant()
        def boundary(root,grant,package):
            self.assertTrue((root/'release/consumed.json').is_file())
            return dict(status='FAIL',witness={'eligible':False})
        with patch.object(e,'run_released',side_effect=boundary) as called:
            e.run_once(self.root)
            with self.assertRaises((ValueError,FileExistsError)):e.run_once(self.root)
            self.assertEqual(called.call_count,1)
    def test_actual_manifest_producer_names_are_accepted(self):
        tree=ast.parse((N/'verification/prepare_review.py').read_bytes())
        node=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='member_name')
        namespace={'N':self.root}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-manifest-producer','exec'),namespace)
        self.manifest['files']={namespace['member_name'](self.root/name):digest for name,digest in self.manifest['files'].items()}
        write(self.root/'manifest.json',self.manifest)
        self.review['manifest_sha256']=sha(self.root/'manifest.json');write(self.root/'review/independent-preparation-review.json',self.review)
        self.approval.update(preparation_manifest_sha256=sha(self.root/'manifest.json'),review_sha256=sha(self.root/'review/independent-preparation-review.json'))
        write(self.root/'harness-approval.json',self.approval)
        self.assertEqual(self.package()['manifest_sha256'],sha(self.root/'manifest.json'))
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

    def released_fixture(self,*,witness=True,product='PENDING_ROOT_INDEPENDENT_REVIEW',preflight_error=False):
        events=[];root=self.root
        class Budget:
            def call(inner,label,fun,*args,**kwargs):
                events.append(label);return fun(*args,**kwargs)
        budget=Budget();parent=dict(origin_ns=100,run_id='run',clock_domain='same-clock',parent_identity={'pid':77})
        class Invocation:
            def __init__(inner):inner.budget=budget;events.append('root-clock-created')
            def parent_timing(inner):return parent
            def call(inner,fun,*args):
                events.append('root-enclosing-call');return fun(*args)
        def metadata_valid(*args):
            if preflight_error:raise ValueError('native metadata mismatch')
        old=types.SimpleNamespace(protected_entries=lambda value:[dict(pid=91)],metadata_valid=metadata_valid)
        p4=types.SimpleNamespace(old=old,protected=lambda:[],listener_owner=lambda port:[91])
        def actual(authority_path,ledger_path):
            authority=json.loads(authority_path.read_bytes());ledger=json.loads(ledger_path.read_bytes())
            self.assertEqual(authority['parent_timing'],parent)
            self.assertEqual(authority['schedule']['work_seconds'],275)
            self.assertEqual(authority['schedule']['cleanup_seconds'],310)
            self.assertEqual(authority['schedule']['outer_seconds'],315)
            self.assertEqual(ledger['consumed'],['E02-controlled-1'])
            self.assertTrue((root/'release/consumed.json').exists())
            events.append('one-existing-run-case')
            return dict(result={'overall':product},witness={'eligible':witness})
        model=root/'model-manifest';model.write_bytes(b'fixture model')
        adapter=types.SimpleNamespace(RootInvocation=Invocation,check_inputs=lambda:None,load_p4=lambda:p4,
            PrivateIO=lambda *args:contextlib.nullcontext(),validate_protected_members=lambda *args:None,
            load=lambda path:{},PROTECTED_BASELINE=root/'protected',INPUTS_PATH=root/'inputs/input-manifest.json',
            bindings=types.SimpleNamespace(load_inputs=lambda path:dict(model_manifest_path=str(model))),
            CASE='E02-controlled-1',MANIFEST_SHA='current',BUDGETS={'native_POST':8,'retry':0},run_case=actual)
        fake_spec=types.SimpleNamespace(loader=types.SimpleNamespace(exec_module=lambda module:None))
        stack=contextlib.ExitStack();self.addCleanup(stack.close)
        stack.enter_context(patch.object(e.importlib.util,'spec_from_file_location',return_value=fake_spec))
        stack.enter_context(patch.object(e.importlib.util,'module_from_spec',return_value=adapter))
        def native(a,b,path):
            self.assertIs(b,budget);self.assertEqual(events[0],'root-clock-created');events.append(path);return {}
        stack.enter_context(patch.object(e,'native_metadata',side_effect=native))
        return events
    def test_existing_harness_gets_one_root_clock_and_original_schedule(self):
        events=self.released_fixture();result=e.run_once(self.root)
        self.assertEqual(result['status'],'PENDING_ROOT_INDEPENDENT_REVIEW')
        self.assertEqual(events.count('one-existing-run-case'),1)
        self.assertLess(events.index('root-clock-created'),events.index('/api/version'))
        self.assertLess(events.index('same-clock root authority'),events.index('root-enclosing-call'))
        self.assertEqual(result['acceptance_credit'],0)
    def test_metadata_failure_consumes_before_any_product_case(self):
        events=self.released_fixture(preflight_error=True);result=e.run_once(self.root)
        self.assertEqual(result['status'],'FAIL');self.assertNotIn('one-existing-run-case',events)
        self.assertFalse((self.root/'controller-authority').exists())
        self.assertTrue((self.root/'release/consumed.json').exists())
    def test_missing_root_timing_pass_never_promotes_product(self):
        self.released_fixture(witness=False);self.assertEqual(e.run_once(self.root)['status'],'FAIL')
    def test_product_failure_never_promoted_by_root_timing(self):
        self.released_fixture(product='FAIL');self.assertEqual(e.run_once(self.root)['status'],'FAIL')

if __name__=='__main__':unittest.main(verbosity=2)
