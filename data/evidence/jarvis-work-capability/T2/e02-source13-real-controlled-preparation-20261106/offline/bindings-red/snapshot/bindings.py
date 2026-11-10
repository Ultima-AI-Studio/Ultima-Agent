"""Closed current8B preparation input contract. Never grants runtime authority."""
from pathlib import Path

def validate(value: dict, *, read_bytes):
    raise NotImplementedError('Current-candidate closed input contract not implemented')

def load_inputs(path: Path):
    raise NotImplementedError('Current-candidate closed input loader not implemented')
