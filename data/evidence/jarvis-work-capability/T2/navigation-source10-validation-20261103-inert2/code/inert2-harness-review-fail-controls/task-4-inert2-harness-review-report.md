# T4-PORT-REV2 independent harness review

**Spec compliance FAIL. Task quality NEEDS_FIXES.** Candidate 118ba152b007c30d358c8bc44c51aabe8ae820f0, base manifest 935b3e3b1f42790c6bd3d7ebd88164f4cc47a9de9a1703557f5da0c59806bcb5, reviewed manifest a5b16aed8d8386d2e2018262a6e75677f00b958cb3553154af987a6658fe376d. One Important finding affects admission of a socket operation after the new per-proof cutoff. Execution remains unreleased and E02/T2 remains NOT_PASSED.

## Strengths and coupling checks

- Both former one-second bottlenecks are changed in adapter.py:116–141. The proof has an allocation-time expiry shared by both modes. Its connect-time setter supersedes P4’s original one-second hint, and a late refusal cannot set final eligibility. Unknown, open, exception and late outcomes fail. Each site attempts at most one connect.
- Checked whether the original P4 verdict can admit uncertainty. Pinned preparation-r4/controller.py:241–246 treats any nonzero result as closed, then writes its own evidence. PrivateIO.cleanup at adapter.py:177–189 separately enforces definitive refusal. Checked whether observation bypasses the adapter or differs by mode. The substantive observation at adapter.py:1063–1069 calls the same private socket proof before the inert branch. Socket closure and private binding restoration at adapter.py:132–134,190–198 cover failure paths.
- The fake socket at test_adapter.py:1164–1179 waits the smaller of effective timeout and 2.0139454 seconds. The author’s RED fails the two real cleanup mode cases and the real substantive observer positive. The final full run retains these three positives and adverse outcomes. No further product suite was needed.
- run_checks.py:18–39 binds the OLD fixture and preparation authority. The original archive lookup at test_adapter.py:1140–1150 reads that fixture. Verified the 76 source pins against current bytes including the 12 frozen files, the six V2 files and full run source copies, five manifest members in both new and old harnesses, and all companion input hashes. The candidate and deadline ruling retain their original bytes and the green preparation receipt points at V2.

## Findings

**Critical:** none.

**Important — PORT2-I01. adapter.py:115 (allocation and registration at 136–141).** The original hint still calls raw.settimeout after a socket constructor has consumed the entire new three-second allowance. P4 and the observer both call the hint immediately after construction. The wrapper delegates without checking expiry. The later connect guard correctly refuses admission, but the extra socket configuration has already happened. The new private expiry introduces this condition even with seven seconds left in the enclosing phase. It violates the ruling that expiry admits no new I/O. It does not promote an uncertain result to PASS.

The author’s zero-before-connect cases at test_adapter.py:1191,1223–1229,1236 verify closure and zero connects. They do not inspect the recorded raw setters in the zero-connect branch. A small fix can guard the original hint against both the absolute phase and private proof deadline before touching the raw socket. Preserve finally-owned closure and verify that neither the setter nor the connect executes after construction exhausts the allowance.

**Minor:** none. The 21 earlier closures remain held. The new issue concerns the new per-proof expiry inside a still-live phase.

## Independent evidence

Recomputed the SHA-256 of all five stages’ receipts, JUnit XML, stdout, stderr, before/after records and six source snapshots against the companion/root records and corresponding author receipts. Parsed the XML and read the raw end summaries. Stage counts in order were 3/3 failed, 2/36 failed, 38/38 passed, 43/43 passed and 216/216 passed. The intermediate two failures were clipped-unknown cleanup assertions in both modes. Final unselected fixed H Python -B -X utf8 pytest exited 0, stdout reported 216 passed in 40.48s and stderr was empty. Direct classname/name comparison against the old JUnit found all 173 original cases and 43 additions. Final receipt 0c2e71edf1ee00d5ef36f7520110652286dd1166d453bd33099add2e7e3b5c02 and JUnit 0efc50e3df1e38c25bf8ccc57bb77213dc0166bc7f0b6ba222b3ded9de02fc2d.

One new focused pure/mock check resolved whether the raw hint actually runs on the author’s zero-before-connect scenario. Only Deadline and PrivateIO were compiled verbatim from the reviewed adapter AST. The in-memory P4 substitute and fake socket implement no system I/O. Cleanup phase cutoff 310000000000 ns, allocation start 300000000000 ns, private expiry 303000000000 ns. Raw constructor advances the clock by 3000000000 ns. Exact output follows.

```text
[('construct', 300000000000), ('settimeout', 303000000000, 1), ('refusal', 303000000000, 'Port proof allocation expired before connect'), ('close', 303000000000)] restored True
```

Raw operations were one construction, one setter at expiry, zero connects and one mandatory close. All five borrowed bindings were restored. The check used the fixed H interpreter -B -X utf8 - with this stdin and exited 0.

```python
import ast, time, uuid
from pathlib import Path
from types import SimpleNamespace
source=Path(r'H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261103-inert2/harness/adapter.py')
tree=ast.parse(source.read_text('utf8'))
tree.body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in ('Deadline','PrivateIO')]
exec(compile(tree,str(source),'exec'))
now=[0]; log=[]
def clk(): return now[0]
class Raw:
    def __init__(self):
        log.append(('construct',clk())); now[0]+=3000000000
    def settimeout(self,t): log.append(('settimeout',clk(),t))
    def connect_ex(self,a): raise AssertionError('unexpected connect')
    def close(self): log.append(('close',clk()))
p4=SimpleNamespace(subprocess=None,time=None,socket=SimpleNamespace(socket=Raw),terminate_owned=None,save=None)
saved=vars(p4).copy()
b=Deadline(clock=clk); b.phase='cleanup'
now[0]=b.cutoff_ns()-10000000000
with PrivateIO(p4,b):
    p=p4.socket.socket(); p.settimeout(1)
    try: p.connect_ex(('mock',0))
    except TimeoutError as e: log.append(('refusal',clk(),str(e)))
    finally: p.close()
print(log, 'restored',vars(p4)==saved)
```

## Scope and qualification

Read-only Git inspection returned the stated C118 HEAD and an empty tracked/index status. No native ownership, real Windows refusal latency, physical timeout bound, model capability or actual/inert acceptance can be inferred from these mocked tests. Work275/cleanup310/seal315, service260/client300/outer315/retry0 and the permanent current8B restriction remain in force. The prior failed actual allocation stays 1/1 consumed, zero remaining, model calls zero. This verdict supplies no caller, baseline, dispatch, release, T3, Owner or production authorization.
