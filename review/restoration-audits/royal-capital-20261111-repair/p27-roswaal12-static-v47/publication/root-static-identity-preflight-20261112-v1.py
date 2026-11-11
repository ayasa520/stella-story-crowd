"""Verify delegated identity evidence without displaying or interpreting images.

This is an integration receipt, not a second visual opinion. It binds each
proposed character field to the current owned node and checks the exact files
used by the delegated reviewers. Historical captures remain historical: no
motion, expression, geometry, background or complete-chapter approval follows
from a costume identity match.
"""

import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path('/home/rikka/Projects/stella')
R = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from story_studio.recovery.native_repair import InstalledSnapshot


def require(condition, message):
    if not condition:
        raise ValueError(message)


checked = {}


def path_for(value):
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def sha(path):
    path = path_for(path)
    if path not in checked:
        checked[path] = hashlib.sha256(path.read_bytes()).hexdigest()
    return checked[path]


def references(value):
    """Check explicit file receipts, never infer a reference from prose.

    A receipt can spell its byte reference as file/sha256, frame/frameSha256
    or video/videoSha256. Deduplicating by path keeps the verification bounded
    when the same original video or model payload occurs on many dialogue rows.
    """
    if isinstance(value, dict):
        for file_key, sha_key in [('file', 'sha256'), ('frame', 'frameSha256'),
                                  ('video', 'videoSha256')]:
            if isinstance(value.get(file_key), str) and value.get(sha_key):
                require(sha(value[file_key]) == value[sha_key],
                        f'File receipt differs: {value[file_key]}')
        for child in value.values():
            references(child)
    elif isinstance(value, list):
        for child in value:
            references(child)


def load(relative, digest=None):
    path = R / relative
    if digest:
        require(sha(path) == digest, f'Input changed: {relative}')
    value = json.loads(path.read_text())
    references(value)
    return value


def decoded_image(value):
    return base64.b64decode(value.split(',', 1)[-1], validate=True)


packets = [
    ('visual-high/agent-reviewed-p27-roswaal-followup-v1/roswaal12-character-only-draft.json',
     'da2b38e9a91fc2c4c179e4ff9042dd0e6e1c0e23cb437a3049709f83bf7c9a17', 12),
    ('visual-high/agent-reviewed-p28-identity-v1/batch2-fifteen-character-only-draft.json',
     '6e3006ca8f857fc5523d5e22954f25fd2aa5265532d3f9002fa5a0b836523d22', 15),
    ('visual-high/agent-reviewed-p28-identity-v1/batch3-fourteen-character-only-draft.json',
     '4a861b7d412c872bac0759978ec6165944bdc73f0120f6e7cf0e552fc7e33f10', 14),
    ('visual-high/agent-reviewed-p28-identity-v1/batch4-seven-character-only-draft.json',
     '8cd316a08bff33280607a0eb25c64b31f42705a15a5631c20b5681b18d420231', 7),
]
snapshot = InstalledSnapshot(ROOT, ROOT / 'story_crowd_data')
seen, packet_checks = set(), []
for relative, digest, count in packets:
    packet = load(relative, digest)
    require(packet['reviewer'] == '/root/felt_entry_offline_review', 'Reviewer differs')
    require(len(packet['changes']) == count, 'Packet count differs')
    for row in packet['changes']:
        identity = (row['sceneId'], row['scenarioId'])
        require(identity not in seen, 'Duplicate proposed node')
        seen.add(identity)
        native, review = snapshot.node(*identity, row['stableKey'])
        require(review['sourceText'] == row['sourceText'], 'Japanese source differs')
        require(row['expected'] == {'character': ''} and native['character'] == '',
                'Character field is no longer empty')
        require(set(row['fields']) == {'character'}, 'Proposal exceeds identity scope')
        evidence = row['evidence']
        require(evidence['directImageReview'] is True and evidence['fullFrameReview'] is True,
                'Full-frame delegated image review missing')
        require(evidence['motionAndExpressionVerified'] is False and
                evidence['originalScriptCSVRecovered'] is False,
                'Identity packet claims performance or original CSV')
    packet_checks.append(dict(file=str(R / relative), sha256=digest, nodes=count))

# The compact model bindings retain the entire catalog row's canonical digest,
# not merely its label or a hand-selected subset. Compare that digest and the
# exact decoded capture anchor independently of the reviewer's identity verdict.
catalog = json.loads((ROOT / 'story_crowd_data/assets/catalog.json').read_text())
models = {row['id']: row for row in catalog['models'].values()}
bound_models = set()
for filename in ['batch2-model-reference-bindings.json', 'batch3-model-reference-bindings.json']:
    binding = load('visual-high/agent-reviewed-p28-identity-v1/' + filename)
    for model, record in binding['models'].items():
        assembled = record['assembledReferenceBinding']
        capture = json.loads(gzip.decompress(path_for(assembled['sourceCapture']['file']).read_bytes()))
        require(capture['model'] == model and capture['kind'] == assembled['sourceKind'],
                'Capture model/kind differs')
        require(decoded_image(capture[assembled['sourceField']]) ==
                path_for(assembled['anchor']['file']).read_bytes(), 'Anchor decode differs')
        canonical = json.dumps(models[model], ensure_ascii=False, sort_keys=True,
                               separators=(',', ':')).encode()
        require(hashlib.sha256(canonical).hexdigest() == assembled['catalogModelEntrySha256'],
                f'Current catalog model row differs: {model}')
        bound_models.add(model)

ros = load('visual-high/agent-reviewed-p27-roswaal-followup-v1/fresh-static-model-binding.json',
           'ef9854e0abd994b5ad755eed869ba04efc4358b7cc3ee3f305667a1a18c98d1e')
raw = json.loads(gzip.decompress(path_for(ros['rawCapture']['file']).read_bytes()))
static = raw['trace']['staticCapture']
require(decoded_image(static['actorPng']) == path_for(ros['actorPng']['file']).read_bytes(),
        'Fresh Roswaal actor PNG differs from raw capture')
require(base64.b64decode(static['rawRgbaBase64'], validate=True) ==
        path_for(ros['rawRgba']['file']).read_bytes(), 'Fresh Roswaal RGBA differs')
require(raw['failure'] is None and not raw['pageErrors'] and not raw['http'] and
        not raw['overflow'] and not raw['trace']['traceOverflow'], 'Fresh runtime capture failed')
compiled = next(row for row in raw['actualCompiledNodes'] if row['id'] == '10200006:13')
require(compiled['model'] == 'roswaal01' and not compiled['body'] and not compiled['face'] and
        not compiled['extra_motions'], 'Fresh static reference contains unexpected acting')
for key in ['render', 'instance', 'lastApplied', 'gameFrame', 'hudKey']:
    require(static[key] == ros['renderBinding'][key], f'Fresh render binding differs: {key}')

coverage = load('visual-high/agent-reviewed-p28-identity-v1/full-part-coverage-manifest.json',
                '54733a768dcf147601a745b1f09154dbed63f959d9fd072b1860c0c728261d6f')
require(len(coverage['rows']) == 58 and coverage['fullPartReviewed'] is True and
        coverage['fullPartIdentityAccepted'] is False, 'P28 coverage scope differs')
require(len({(row['sceneId'], row['scenarioId']) for row in coverage['rows']}) == 58,
        'Duplicate P28 coverage node')
snapshot.unchanged_on_disk()
output = R / 'root-static-identity-preflight-20261112-v1.json'
require(not output.exists(), 'Use a fresh receipt path')
receipt = dict(status='passed_metadata_and_exact_byte_bindings', reviewer='/root',
               visualReviewer='/root/felt_entry_offline_review', mainThreadViewedImages=False,
               dataHead=subprocess.check_output(['git', '-C', str(ROOT / 'story_crowd_data'),
                                                 'rev-parse', 'HEAD'], text=True).strip(),
               proposedCharacterNodes=len(seen), packets=packet_checks,
               p28BoundModelIds=sorted(bound_models), p28CoverageRows=58,
               freshRoswaalRawImageByteBindings=True, filesChecked=len(checked),
               checkedFiles=[dict(file=str(path), sha256=digest)
                             for path, digest in sorted(checked.items())],
               actingAccepted=False, geometryAccepted=False, backgroundAccepted=False,
               wholeChapterAccepted=False, formalWrites=0, browserOpened=False)
output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in receipt.items() if k != 'checkedFiles'}))
