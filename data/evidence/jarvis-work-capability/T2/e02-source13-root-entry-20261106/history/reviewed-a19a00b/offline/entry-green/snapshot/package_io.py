"""Bounded strict records, based on the accepted E01 package helpers."""
import hashlib
import json
import os
from pathlib import Path
import stat

CAP=4*1024*1024


def require(condition,message):
    if not condition:raise ValueError(message)


def safe_path(path):
    path=Path(path)
    require(path.is_absolute() and '..' not in path.parts,'Absolute non-traversing path required')
    for item in (path,*path.parents):
        try:attributes=item.lstat()
        except FileNotFoundError:
            require(not item.is_symlink(),'Reparse path refused');continue
        require(not item.is_symlink() and not getattr(attributes,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT,
                'Reparse path refused')
    return path


def read(path):
    path=safe_path(path)
    require(path.is_file() and path.stat().st_size<=CAP,'Bounded record file required')
    with path.open('rb') as stream:raw=stream.read(CAP+1)
    require(0<len(raw)<=CAP,'Record byte bound')
    return raw


def sha(path):return hashlib.sha256(safe_path(path).read_bytes()).hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')


def decode(raw):
    def unique(pairs):
        value={}
        for key,item in pairs:
            require(key not in value,'Duplicate JSON key');value[key]=item
        return value
    def nonfinite(value):raise ValueError('Nonfinite JSON')
    return json.loads(raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=nonfinite)


def load(path):return decode(read(path))


def save_new(path,value):
    raw=canonical(value)+b'\n'
    require(len(raw)<=CAP,'Record byte bound')
    with safe_path(path).open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return digest(raw)
