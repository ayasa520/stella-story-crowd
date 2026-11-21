"""Run the unchanged asset writer after real proposal resource validation.

Only json.loads callable-entry inputs are hashed. No decoder/scanner frame is
traced, and no reader/parser is replaced. A real JSON failure retains its exact
exception document after tracing stops; successful large bodies are not copied.
The six prospective story fields are checked in memory only, never installed by
this resource operation. The original writer owns both metadata writes.
"""
import gzip
import hashlib
import json
from pathlib import Path
import runpy
import sys
import traceback

ROOT = Path('/home/rikka/Projects/stella')
AREA = ROOT/'artifacts/stella-script-continuation-20261121'
OUT = AREA/'bg070b-root-publication-8b43089d-v1/normal-integrate-attempt1'
PLAN = AREA/'bg070b-root-publication-8b43089d-v1/integration-plan.root-approved.json'
WRITER = AREA/'apply-asset-plan.py'
DATA = AREA/'data-checkout'
PACKET = AREA/'p42-six-visual-fields-8b43089d-preflight-v1/node-fields.rootfalse.json'
sys.path.insert(0, str(ROOT))
OUT.mkdir()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
assert sha(PLAN.read_bytes()) == '42e01c64a3654bbcd55d650c0052ba606d047ae4fe2f7cd097fbbbb1d3434faa'
assert sha(WRITER.read_bytes()) == 'ff5ef8fa4a20ac5d5f222be7164b8bc961cafda5a4fc1cbeed235efb0322feb2'
assert sha(PACKET.read_bytes()) == '76d9b4b120358f992cc539139ad74261a3290bf67c7111cc8c1ddfc0aa8f7f48'
original_loads = json.loads
receivers = []


def observe(frame, event, _argument):
    if event == 'call' and frame.f_code is original_loads.__code__:
        value = frame.f_locals['s']
        raw = value if isinstance(value, bytes) else value.encode('utf-8', 'surrogatepass')
        caller = frame.f_back
        receivers.append({'sequence': len(receivers)+1, 'bytes': len(raw), 'sha256': sha(raw),
            'inputType': type(value).__name__, 'caller': caller.f_code.co_filename,
            'line': caller.f_lineno, 'path': str(caller.f_locals.get('path', caller.f_locals.get('plan_path', ''))),
            'decoderOrScannerTraced': False})
    return None


def load(path):
    raw = path.read_bytes()
    return json.loads(raw)


failure = None
validation = False
writer_invoked = False
try:
    assert sys.gettrace() is None
    sys.settrace(observe)
    plan = load(PLAN)
    assert plan['rootConfirmed'] is True and plan['newMediaBytes'] == 0
    document = load(DATA/'native/scenes/10430012.json')
    packet = load(PACKET)
    assert len(packet['changes']) == 6
    for change in packet['changes']:
        row = next(row for row in document['scenario_list'] if row['scenario_id'] == change['scenarioId'])
        for field, value in change['expected'].items():
            assert row[field] == value, (change['scenarioId'], field)
        assert set(change['fields']) <= {'bg_picture', 'character_image'}
        row.update(change['fields'])
    candidate = next(change for change in plan['changes'] if change['path'] == 'catalog.json')
    catalog = load(Path(candidate['source']))
    from story_studio.recovery.native_resources import validate_resources
    validate_resources(document, catalog, DATA/'assets', 10430012)
    validation = True
    sys.argv = [str(WRITER), str(PLAN), str(OUT/'installer-receipt.json')]
    writer_invoked = True
    runpy.run_path(str(WRITER), run_name='__main__')
except BaseException as error:
    failure = error
finally:
    sys.settrace(None)

result = {'schema': 'stella.original-asset-writer-observation.v1',
    'exitCode': 1 if failure else 0, 'proposalNormalResourceValidationPassed': validation,
    'proposalStoryFieldsWritten': False, 'originalWriterInvoked': writer_invoked,
    'receivers': receivers, 'loadsIdentityUnchanged': json.loads is original_loads,
    'readerOrParserReplaced': False, 'decoderOrScannerInternalTrace': False,
    'writerSha256After': sha(WRITER.read_bytes())}
if failure:
    result['failure'] = {'type': type(failure).__name__, 'message': str(failure)}
    if isinstance(failure, json.JSONDecodeError):
        raw = failure.doc.encode('utf-8', 'surrogatepass')
        packed = gzip.compress(raw, mtime=0)
        (OUT/'actual-json-exception-doc.utf8.gz').write_bytes(packed)
        result['jsonException'] = {'pos': failure.pos, 'line': failure.lineno, 'column': failure.colno,
            'utf8Bytes': len(raw), 'utf8Sha256': sha(raw), 'gzipSha256': sha(packed),
            'lastObservedReceiver': receivers[-1] if receivers else None}
    (OUT/'traceback.txt').write_text(''.join(traceback.format_exception(failure)))
    traceback.print_exception(failure)
(OUT/'observation.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({key: value for key, value in result.items() if key != 'receivers'}))
raise SystemExit(result['exitCode'])
