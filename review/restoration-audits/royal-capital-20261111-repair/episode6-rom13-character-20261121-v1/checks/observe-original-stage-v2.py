"""Observe one original CLI stage, preserving its actual failed inputs.

The previous failed operation retained JSONDecodeError.doc but not the local
raw bytes or source path. This bounded observation leaves the module and JSON
parser unchanged. On error, traceback frames retain the precise file bytes and
identity consumed by that operation; no parser fallback or automatic retry is
permitted. A successful stage does not diagnose or fix the earlier anomaly.
"""
from pathlib import Path
import hashlib
import json
import os
import runpy
import sys
import traceback

ROOT = Path('/home/rikka/Projects/stella')
AREA = ROOT / 'artifacts/stella-script-continuation-20261121'
OUT = AREA / 'episode6-rom13-normal-stage-observer-v2'
OUT.mkdir()
assert os.getpriority(os.PRIO_PROCESS, 0) == 19
assert os.sched_getaffinity(0) == {0, 1}
sys.argv = ['story_studio.recovery.native_repair', '--root', str(ROOT), '--target',
            str(AREA / 'data-checkout'), '--directory',
            str(ROOT / 'data/native_recovery/royal-capital-20261110/native-directory.json'),
            '--node-fields', str(AREA / 'episode6-rom13-observed-stage-v2-approval/node-fields.root-approved.json'),
            '--output', str(AREA / 'episode6-rom13-final-normal-stage-v2')]
try:
    runpy.run_module('story_studio.recovery.native_repair', run_name='__main__')
except BaseException as error:
    info = {'type': type(error).__name__, 'message': str(error), 'argv': sys.argv,
            'traceback': traceback.format_exc(), 'originalModuleAndParserUnmodified': True,
            'automaticRetries': 0, 'formalDataWritten': False, 'originalFrameInputs': []}
    frame = error.__traceback__
    while frame is not None:
        current = frame.tb_frame
        if Path(current.f_code.co_filename).resolve() == ROOT / 'story_studio/recovery/native_repair.py':
            local = current.f_locals
            if isinstance(local.get('raw'), bytes):
                raw = local['raw']
                name = f'actual-frame-{len(info["originalFrameInputs"])}.raw.bin'
                (OUT / name).write_bytes(raw)
                info['originalFrameInputs'].append({
                    'function': current.f_code.co_name, 'line': frame.tb_lineno,
                    'name': local.get('name'), 'identity': local.get('identity'),
                    'kind': local.get('kind'), 'rawFile': name, 'rawBytes': len(raw),
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
    (OUT / 'completion.json').write_text(json.dumps({
        'argv': sys.argv, 'exitCode': 0, 'originalModuleAndParserUnmodified': True,
        'automaticRetries': 0, 'formalDataWritten': False,
        'earlierFailureStillRetainedAndCauseUnknown': True}, indent=2) + '\n')
