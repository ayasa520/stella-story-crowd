"""Observe one ordinary installer invocation without replacing its behavior.

The audit and apply operations write distinct, immutable observation folders.
On failure, retain the actual traceback and reader-frame bytes. No JSON parser
fallback, staging repair or automatic retry is permitted. The earlier Rom
reader anomaly remains separate from the resolved outer-wrapper import path.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import traceback

ROOT = Path('/home/rikka/Projects/stella')
AREA = ROOT / 'artifacts/stella-script-continuation-20261121'
STAGE = AREA / 'episode11-scene10110003-normal-stage-v2'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument('--operation', choices=['audit', 'apply'], required=True)
parser.add_argument('--approval')
parser.add_argument('--approval-sha256')
args = parser.parse_args()
assert os.getpriority(os.PRIO_PROCESS, 0) == 19
assert os.sched_getaffinity(0) == {0, 1}
if args.operation == 'apply':
    # A successful nonwriting audit alone does not authorize a later snapshot.
    # Root binds the exact stage and current files after reviewing its output.
    assert args.approval and args.approval_sha256
    assert sha(args.approval) == args.approval_sha256
    approval = json.loads(Path(args.approval).read_bytes())
    assert approval['rootConfirmed'] is True and approval['applyAuthorized'] is True
    assert approval['stageManifestSHA256'] == sha(STAGE / 'manifest.json')
    for path, expected in approval['guards'].items():
        assert sha(path) == expected, path

OUT = AREA / ('episode11-normal-install-' + args.operation + '-observer-v1')
OUT.mkdir()
sys.argv = ['story_studio.recovery.native_install', '--root', str(ROOT),
            '--target', str(AREA / 'data-checkout'), '--staging', str(STAGE)]
if args.operation == 'apply':
    sys.argv.append('--apply')
try:
    runpy.run_module('story_studio.recovery.native_install', run_name='__main__')
except BaseException as error:
    info = {'type': type(error).__name__, 'message': str(error),
            'operation': args.operation, 'argv': sys.argv,
            'traceback': traceback.format_exc(), 'automaticRetries': 0,
            'originalModuleAndParserUnmodified': True,
            'formalDataWriteStatus': 'Audit cannot write; inspect original apply output and snapshots on an apply failure.',
            'originalFrameInputs': []}
    frame = error.__traceback__
    while frame is not None:
        current = frame.tb_frame
        if Path(current.f_code.co_filename).resolve() == ROOT / 'story_studio/recovery/native_install.py':
            local = current.f_locals
            for field in ('raw', 'incoming_raw'):
                if not isinstance(local.get(field), bytes):
                    continue
                raw = local[field]
                name = f'actual-frame-{len(info["originalFrameInputs"])}.raw.bin'
                (OUT / name).write_bytes(raw)
                info['originalFrameInputs'].append({'function': current.f_code.co_name,
                    'line': frame.tb_lineno, 'path': str(local.get('path')),
                    'field': field, 'rawFile': name, 'rawBytes': len(raw),
                    'rawSHA256': hashlib.sha256(raw).hexdigest()})
        frame = frame.tb_next
    if isinstance(error, json.JSONDecodeError):
        doc = error.doc.encode('utf-8', errors='surrogatepass')
        (OUT / 'actual-exception-doc.utf8.bin').write_bytes(doc)
        info.update(pos=error.pos, lineno=error.lineno, colno=error.colno,
                    docCharacters=len(error.doc), docUTF8Bytes=len(doc),
                    actualDocSHA256=hashlib.sha256(doc).hexdigest())
    (OUT / 'failure.json').write_text(json.dumps(info, ensure_ascii=False, indent=2) + '\n')
    raise
else:
    (OUT / 'completion.json').write_text(json.dumps({'operation': args.operation,
        'argv': sys.argv, 'exitCode': 0, 'originalModuleAndParserUnmodified': True,
        'automaticRetries': 0, 'applyRequested': args.operation == 'apply',
        'separateEarlierRomReaderAnomalyCauseUnknown': True}, indent=2) + '\n')
