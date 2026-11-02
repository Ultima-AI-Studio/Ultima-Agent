"""LF-only unified diffs; reconstruct each hunk and compare original raw bytes."""
from pathlib import Path
import difflib
import hashlib
import json
import re

PREP = Path(__file__).resolve().parent
OLD = PREP.parent/'preparation-r2'
W = Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent/.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101')
REPORT = W/'task-2-e02-receiver-outer-preparation-report.md'
PACKAGE = W/'task-2-e02-receiver-fix1-review-package.txt'


def lines(raw):
    # U+2028/U+2029 and other Unicode separators are literal payload bytes.
    parts = raw.split(b'\n')
    return [p+b'\n' for p in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def diff(before, after, oldname, newname):
    chunks = difflib.unified_diff([p.decode('utf8') for p in lines(before)],
        [p.decode('utf8') for p in lines(after)], fromfile=oldname,tofile=newname)
    out = []
    for chunk in chunks:
        out.append(chunk)
        if not chunk.endswith('\n'):
            out.append('\n\\ No newline at end of file\n')
    return ''.join(out).encode('utf8')


def reconstruct(patch, original):
    rows = lines(patch)
    # Attach the missing-final-newline marker to the preceding payload line.
    normalized = []
    for row in rows:
        if row == b'\\ No newline at end of file\n':
            if not normalized[-1].endswith(b'\n'): raise ValueError('Bad marker')
            normalized[-1] = normalized[-1][:-1]
        else:
            normalized.append(row)
    before = lines(original); result = []; position = 0; i = 2
    while i < len(normalized):
        match = re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n',normalized[i])
        if not match: raise ValueError('Malformed hunk header')
        start,count = int(match[1]), int(match[2] or b'1')
        begin = start-1 if count else start
        result.extend(before[position:begin]); position = begin; i += 1
        while i < len(normalized) and not normalized[i].startswith(b'@@ '):
            row = normalized[i]; prefix, payload = row[:1],row[1:]
            if prefix in (b' ',b'-'):
                if position>=len(before) or before[position] != payload: raise ValueError('Original hunk mismatch')
                position += 1
            if prefix in (b' ',b'+'): result.append(payload)
            if prefix not in (b' ',b'+',b'-'): raise ValueError('Malformed hunk payload')
            i += 1
    result.extend(before[position:])
    return b''.join(result)


def main():
    files = sorted(p for p in PREP.iterdir() if p.is_file())
    files += sorted(p for p in (PREP.parent/'fix1-guard-tests').rglob('*') if p.is_file())
    files.append(REPORT)
    all_parts=[]; entries=[]
    for section in ('FIX DIFF r2 -> r3','CORRECTED FULL NEW FILES'):
        all_parts.append(('### '+section+'\n').encode())
        for target in files:
            raw=target.read_bytes()
            prior=OLD/target.name if target.parent==PREP else None
            if target==REPORT: prior=PREP/'prior-outer-report.md'
            before=prior.read_bytes() if section.startswith('FIX') and prior is not None and prior.exists() else b''
            if not raw:
                all_parts.append(('# EMPTY FILE '+str(target)+' SHA256 '+hashlib.sha256(raw).hexdigest()+'\n').encode())
                continue
            if before==raw:
                all_parts.append(('# BYTE-IDENTICAL COPY '+str(prior)+' -> '+str(target)+' SHA256 '+hashlib.sha256(raw).hexdigest()+'\n').encode())
                continue
            patch=diff(before,raw,str(prior) if before else '/dev/null',str(target))
            if reconstruct(patch,before)!=raw:raise ValueError('Reconstruction differs: '+str(target))
            all_parts.append(patch)
            entries.append(dict(section=section,path=str(target),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),equal=True))
    with PACKAGE.open('xb') as stream:stream.write(b''.join(all_parts))
    # Re-read package itself, extract every exact patch entry using LF headers,
    # and verify the bytes that a reviewer actually receives, not just buffers.
    rows=lines(PACKAGE.read_bytes()); reconstructed=0; empty=0; copies=0; i=0
    while i<len(rows):
        if rows[i].startswith(b'# BYTE-IDENTICAL COPY '):
            source,tail=rows[i][22:].split(b' -> ',1)
            target,digest=tail.rstrip(b'\n').rsplit(b' SHA256 ',1)
            raw=Path(target.decode('utf8')).read_bytes()
            if Path(source.decode('utf8')).read_bytes()!=raw or hashlib.sha256(raw).hexdigest().encode()!=digest:
                raise ValueError('Byte-identical copy declaration mismatch')
            copies+=1;i+=1;continue
        if rows[i].startswith(b'# EMPTY FILE '):
            name=rows[i][13:].split(b' SHA256 ',1)[0].decode('utf8')
            if Path(name).read_bytes()!=b'':raise ValueError('Nonempty file declared empty')
            empty+=1;i+=1;continue
        if not rows[i].startswith(b'--- '): i+=1; continue
        start=i; oldname=rows[i][4:-1].decode('utf8'); newname=rows[i+1][4:-1].decode('utf8');i+=2
        while i<len(rows) and not rows[i].startswith((b'--- ',b'### ',b'# BYTE-IDENTICAL COPY ',b'# EMPTY FILE ')):i+=1
        original=b'' if oldname=='/dev/null' else Path(oldname).read_bytes()
        if reconstruct(b''.join(rows[start:i]),original)!=Path(newname).read_bytes():raise ValueError('Packaged bytes differ: '+newname)
        reconstructed+=1
    full_count=sum(e['section'].startswith('CORRECTED') for e in entries)
    if full_count+sum(not p.read_bytes() for p in files)!=len(files):raise ValueError('Full-new file coverage gap')
    print(json.dumps(dict(status='PASS',patched_entries=reconstructed,byte_identical_copies=copies,full_new_entries=full_count,
        expected_full_new_files=len(files),empty_file_declarations=empty,missing_final_newlines=sum(bool(p.read_bytes()) and not p.read_bytes().endswith(b'\n') for p in files),
        unicode_separator_fixture_unchanged=(PREP/'fixtures.json').read_bytes()==(OLD/'fixtures.json').read_bytes(),
        package_sha256=hashlib.sha256(PACKAGE.read_bytes()).hexdigest()),indent=2))


if __name__=='__main__':main()
