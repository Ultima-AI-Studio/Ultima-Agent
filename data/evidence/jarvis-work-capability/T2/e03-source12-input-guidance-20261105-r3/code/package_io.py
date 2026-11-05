"""Exact reviewed pure IO helpers; no runtime dispatch."""
from __future__ import annotations
import hashlib, json, os, stat
from pathlib import Path

def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'Duplicate JSON key')
            value[key] = item
        return value
    raw = Path(path).read_bytes()
    require(0 < len(raw) <= 4 * 1024 * 1024, 'JSON size invalid')
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique)


def safe_path(path):
    path = Path(path).absolute()
    require('..' not in path.parts, 'Traversal forbidden')
    for item in (path, *path.parents):
        try:
            attributes = item.lstat()
        except FileNotFoundError:
            require(not item.is_symlink(), 'Reparse path forbidden')
            continue
        require(not item.is_symlink() and not getattr(attributes, 'st_file_attributes', 0)
                & stat.FILE_ATTRIBUTE_REPARSE_POINT, 'Reparse path forbidden')
    return path


def child(root, relative):
    require(isinstance(relative, str) and relative and '\\' not in relative and ':' not in relative
            and all(part not in ('', '.', '..') for part in relative.split('/')), 'Noncanonical package path')
    return safe_path(root.joinpath(*relative.split('/')))


def save_new(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
