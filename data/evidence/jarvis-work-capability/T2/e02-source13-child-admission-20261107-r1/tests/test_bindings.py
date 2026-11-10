from pathlib import Path
import copy,hashlib,importlib.util,json,unittest
N=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('real8b_bindings',N/'code/bindings.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class CurrentInputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=json.loads((N/'inputs/input-manifest.json').read_bytes())
        cls.data={p:Path(p).read_bytes() for p in cls.original['files']}
    def setUp(self):self.value=copy.deepcopy(self.original)
    def check(self):return b.validate(self.value,read_bytes=lambda p:self.data[str(p)])
    def test_valid_current_inputs(self):
        self.assertEqual(self.check(),self.original)
        self.assertFalse(self.check()['actual_released'])
    def test_real_disk_readback(self):self.assertEqual(b.load_inputs(N/'inputs/input-manifest.json'),self.original)
    def test_rejects_wrong_candidate(self):
        self.value['candidate']='118ba152b007c30d358c8bc44c51aabe8ae820f0'
        with self.assertRaises(ValueError):self.check()
    def test_rejects_old_worktree(self):
        self.value['candidate_root']=r'C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent'
        with self.assertRaises(ValueError):self.check()
    def test_rejects_model_or_digest_change(self):
        for key,new in [('model','qwen2.5:14b'),('model','qwen3:8b'),('model_digest','0'*64)]:
            with self.subTest(key=key,value=new):
                self.value=copy.deepcopy(self.original);self.value[key]=new
                with self.assertRaises(ValueError):self.check()
    def test_rejects_corpus_change(self):
        self.value['corpus_sha256']='1'*64
        with self.assertRaises(ValueError):self.check()
    def test_rejects_relaxed_budget(self):
        for key in self.value['budgets']:
            with self.subTest(key=key):
                self.value=copy.deepcopy(self.original);self.value['budgets'][key]+=1
                with self.assertRaises(ValueError):self.check()
    def test_rejects_boolean_budget(self):
        self.value['budgets']['cli']=True
        with self.assertRaises(ValueError):self.check()
    def test_rejects_actual_or_retry(self):
        for key,new in [('actual_released',True),('actual_released',0),('protected_count',5),('protected_count',True)]:
            with self.subTest(key=key,value=new):
                self.value=copy.deepcopy(self.original);self.value[key]=new
                with self.assertRaises(ValueError):self.check()
    def test_rejects_unknown_fields(self):
        for target in ('root','budgets','previous_plumbing'):
            with self.subTest(target=target):
                self.value=copy.deepcopy(self.original)
                node=self.value if target=='root' else self.value[target];node['override']=True
                with self.assertRaises(ValueError):self.check()
    def test_rejects_missing_or_changed_binding(self):
        for mode in ('missing_model','missing_source','changed_bytes','changed_expected'):
            with self.subTest(mode=mode):
                self.value=copy.deepcopy(self.original);key=self.value['model_manifest_path']
                if mode=='missing_model':del self.value['files'][key]
                if mode=='missing_source':del self.value['files'][next(iter(self.value['source_files']))]
                if mode=='changed_expected':self.value['files'][key]='2'*64
                read=lambda p:b'changed' if mode=='changed_bytes' and str(p)==key else self.data[str(p)]
                with self.assertRaises(ValueError):b.validate(self.value,read_bytes=read)
    def test_rejects_relative_or_ambiguous_path(self):
        for name in ('relative.py',r'C:\temp\..\not-canonical.py'):
            with self.subTest(path=name):
                self.value=copy.deepcopy(self.original);self.value['files'][name]='3'*64
                with self.assertRaises(ValueError):self.check()
    def test_rejects_plumbing_as_research_credit(self):
        self.value['previous_plumbing']['real_research_credit']=1
        with self.assertRaises(ValueError):self.check()
    def test_rejects_unbound_review(self):
        self.value['previous_plumbing']['review_sha256']='4'*64
        with self.assertRaises(ValueError):self.check()
