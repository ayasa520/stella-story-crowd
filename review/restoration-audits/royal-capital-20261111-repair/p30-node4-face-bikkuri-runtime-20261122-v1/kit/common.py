"""Artifact I/O and immutable input verification; no player/business logic."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = HERE.parent / 'data-checkout'
SOURCE = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'

def load(path):
    return json.loads(Path(path).read_text())

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def field_differences(left, right, prefix=''):
    # Enumerate semantic leaves independently of pretty-printing. An overlay
    # may not hide a changed ID/order/branch by presenting only a text diff.
    if isinstance(left, dict) and isinstance(right, dict):
        assert left.keys() == right.keys(), prefix
        return [v for k in left for v in field_differences(left[k], right[k], prefix + '/' + k)]
    if isinstance(left, list) and isinstance(right, list):
        assert len(left) == len(right), prefix
        return [v for i, pair in enumerate(zip(left, right)) for v in field_differences(*pair, prefix + '/' + str(i))]
    return [] if left == right else [{'path': prefix, 'before': left, 'after': right}]

def checked_guards(guards):
    actual = {p: sha(ROOT / p) for p in guards}
    assert actual == guards, {p: actual[p] for p in actual if actual[p] != guards[p]}
    return actual

def limits():
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19
    assert sorted(os.sched_getaffinity(0)) == [0, 1]

def processes():
    return subprocess.check_output(['ps', '-eo', 'pid,ppid,pgid,comm,args'], text=True)

def group_members(group):
    result = []
    for line in processes().splitlines()[1:]:
        f = line.strip().split(None, 4)
        if len(f) >= 4 and int(f[2]) == group:
            result.append({'pid': int(f[0]), 'ppid': int(f[1]), 'pgid': int(f[2]), 'comm': f[3], 'args': f[4] if len(f) > 4 else ''})
    return result
