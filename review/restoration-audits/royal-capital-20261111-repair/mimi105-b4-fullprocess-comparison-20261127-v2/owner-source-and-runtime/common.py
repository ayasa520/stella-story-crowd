"""Artifact-only first-read I/O and the existing complete inventory verifier.

No formal repository or canonical source is written. Large maps are expanded
only in RAM from one immutable inventory; ordinary receipts retain its ref.
"""
import base64
import gzip
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = HERE.parent / 'data-checkout'
SOURCE = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'
UNBOUND = object()


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


def load(path, expected=UNBOUND, expected_bytes=None, failure_directory=None):
    raw = Path(path).read_bytes()
    proof = {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    try:
        if expected is not UNBOUND:
            assert proof['sha256'] == expected, proof
        if expected_bytes is not None:
            assert len(raw) == expected_bytes, proof
        return json.loads(raw)
    except BaseException as error:
        # Capture the ORIGINAL parse/proof exception before any archival I/O.
        # Failure of either independent file sink must not replace it, lose
        # this first-read buffer, or trigger a later reread/normalization.
        original_traceback = traceback.format_exc()
        fact = {
            'firstRead': proof, 'error': str(error), 'doc': getattr(error, 'doc', None),
            'pos': getattr(error, 'pos', None), 'lineno': getattr(error, 'lineno', None),
            'colno': getattr(error, 'colno', None), 'traceback': original_traceback,
            'rereadOrInputRepair': False,
        }
        try:
            folder = Path(failure_directory or HERE / 'first-read-failures')
            folder.mkdir(parents=True, exist_ok=True)
            stem = folder / ('json-first-read-' + str(time.time_ns()))
            with Path(str(stem) + '.raw.gz').open('xb') as stream:
                stream.write(gzip.compress(raw, compresslevel=1, mtime=0))
            with Path(str(stem) + '.failure.json.gz').open('xb') as stream:
                stream.write(gzip.compress(json.dumps(fact, ensure_ascii=False).encode(),
                                           compresslevel=1, mtime=0))
        except BaseException as archive_error:
            print('JSON_FIRST_READ_ARCHIVE_FAILED ' + json.dumps({
                **fact, 'rawBase64': base64.b64encode(raw).decode('ascii'),
                'archiveError': str(archive_error), 'archiveTraceback': traceback.format_exc(),
            }, ensure_ascii=False), file=sys.stderr, flush=True)
        raise


def limits():
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19
    assert sorted(os.sched_getaffinity(0)) == [0, 1]


def processes():
    return subprocess.check_output(['ps', '-eo', 'pid,ppid,pgid,comm,args'], text=True)


def group_members(group):
    result = []
    for line in processes().splitlines()[1:]:
        fields = line.strip().split(None, 4)
        if len(fields) >= 4 and int(fields[2]) == group:
            result.append({'pid': int(fields[0]), 'ppid': int(fields[1]), 'pgid': int(fields[2]),
                           'comm': fields[3], 'args': fields[4] if len(fields) > 4 else ''})
    return result


def checked_guards(guards):
    actual = {path: sha(ROOT / path) for path in guards}
    assert actual == guards
    return actual


def differences(left, right, prefix=''):
    if isinstance(left, dict) and isinstance(right, dict):
        assert list(left) == list(right), prefix
        return [item for key in left for item in differences(left[key], right[key], prefix + '/' + key)]
    if isinstance(left, list) and isinstance(right, list):
        assert len(left) == len(right), prefix
        return [item for index, pair in enumerate(zip(left, right))
                for item in differences(*pair, prefix + '/' + str(index))]
    assert type(left) is type(right), prefix
    return [] if left == right else [{'path': prefix, 'before': left, 'after': right}]


def inventory_view(binding):
    ref = binding['inventory']
    inventory = load(ref['path'], ref['sha256'], ref.get('bytes'))
    assert inventory['dataRoot'] == str(DATA) and inventory['sourceRoot'] == str(SOURCE)
    assert inventory['dataHead'] == binding['finalDataHead']
    assert inventory['sourceHead'] == binding['finalSourceHead']
    return inventory


def verify(binding, output, additional=None):
    """Reuse the reviewed UI31 core's actual hashes and exact tracked gate.

    The imported core is itself an immutable root-bound input. This function
    changes only the explicit context, preserving its full D tracked hashes,
    NUL-delimited membership, native/review coverage, C/dist membership and
    small normal summaries. No old A screenshot inventory is rediscovered.
    """
    ref = binding['ownerCore']
    assert sha(ref['path']) == ref['sha256']
    spec = importlib.util.spec_from_file_location('mimi105_reviewed_inventory_core', ref['path'])
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    inventory = inventory_view(binding)
    refs = {**inventory['sharedClosure'], **inventory['evidenceGuards'],
            **binding['sourceGuards'], **(additional or {}),
            binding['inventory']['path']: binding['inventory']['sha256']}
    value = {'dataRoot': str(DATA), 'sourceRoot': str(SOURCE),
             'dataHead': binding['finalDataHead'], 'dataStatus': '',
             'dataInputs': inventory['dataInputs'], 'globalGuards': inventory['globalGuards'],
             'protectedFirstThree': inventory['protectedFirstThree'],
             'resourceAndSourceGuards': refs, 'toolFiles': inventory['toolFiles'],
             'kitGuards': binding['kitGuards'],
             'source': {'head': binding['finalSourceHead'], 'status': inventory['sourceStatus'],
                        'sourceFiles': inventory['sourceFiles'], 'distFiles': inventory['distFiles']}}
    counts = {key: len(inventory[key]) for key in ('dataInputs', 'globalGuards',
              'protectedFirstThree', 'sourceFiles', 'distFiles', 'toolFiles')}
    core.bind_context(root=ROOT, binding_value=value, output=output,
                      inventory_reference=binding['inventory'], summary={'inventoryCounts': counts})
    return core.summarize_inputs(core.inputs(value))
