from pathlib import Path
here=Path(__file__).resolve().parent
source=(here/'check_git_blobs.py').read_text(encoding='utf8')
source=source.replace("assert all(H(git('show',ref+p))==sha for p,sha in audit['source_inputs'].items())", "tracked=set(git('ls-files').decode().splitlines())\n    assert all(H(git('show',ref+p))==sha for p,sha in audit['source_inputs'].items() if p in tracked)\n    assert all(H((C/p).read_bytes())==sha for p,sha in audit['source_inputs'].items())")
source=source.replace("all_final_source_inputs_equal=mode!='staged'", "all_final_source_inputs_equal=mode!='staged',tracked_source_paths=sorted(p for p in audit['source_inputs'] if p in tracked) if mode!='staged' else [],untracked_source_paths=sorted(p for p in audit['source_inputs'] if p not in tracked) if mode!='staged' else []")
(here/'check_git_blobs_v2.py').write_text(source,encoding='utf8')
