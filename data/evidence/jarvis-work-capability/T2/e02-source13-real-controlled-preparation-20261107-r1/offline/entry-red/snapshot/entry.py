"""Prepared one-case root entry. No default runtime allocation."""
from pathlib import Path
import datetime as dt
N=Path(__file__).resolve().parents[1]
CANDIDATE='269aca511d88412dbb9c15d23911138469a37aa2'
MODEL='qwen3-8b-uncensored'
DIGEST='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'
KIND='SOURCE13_CURRENT8B_REAL_CONTROLLED_ONE_CASE'

def read_ready(root):raise NotImplementedError('T3 preparation gate')
def read_release(root,package,now):raise NotImplementedError('T3 allocation gate')
def run_released(root,grant,package):raise NotImplementedError('T3 existing RootInvocation connection')
def run_once(root):raise NotImplementedError('T3 exclusive consumption')
