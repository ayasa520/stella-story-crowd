"""Bind five delegated P29 identity packets to current nodes and exact evidence.

No image is displayed or interpreted here. A historical raw model canvas can
support a costume reference even when its surrounding story trial was rejected;
its exact instance/model/pixel attribution and failure limitations are retained.
That does not authorize the old trial, a pose, a face or another story identity.
"""

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('/home/rikka/Projects/stella')
R = Path(__file__).parent
P = R / 'visual-high/agent-reviewed-p29-identity-v1'
sys.path.insert(0, str(ROOT))
from story_studio.recovery.native_repair import InstalledSnapshot


def require(condition, message):
    if not condition:
        raise ValueError(message)


checked = {}


def sha(value):
    path = Path(value)
    path = path if path.is_absolute() else ROOT / path
    if path not in checked:
        checked[path] = hashlib.sha256(path.read_bytes()).hexdigest()
    return checked[path]


def references(value):
    if isinstance(value, dict):
        for key, digest in [('file', 'sha256'), ('frame', 'frameSha256'), ('video', 'videoSha256')]:
            if isinstance(value.get(key), str) and value.get(digest):
                require(sha(value[key]) == value[digest], f'Referenced bytes changed: {value[key]}')
        for child in value.values():
            references(child)
    elif isinstance(value, list):
        for child in value:
            references(child)


def load(name, digest=None):
    path = P / name
    if digest:
        require(sha(path) == digest, f'Input changed: {name}')
    value = json.loads(path.read_text())
    references(value)
    return value


catalog = json.loads((ROOT / 'story_crowd_data/assets/catalog.json').read_text())
bindings = []
for model in ['rom01', 'felt01']:
    binding = load(model + '-assembled-original-binding.json')
    require(binding['model'] == model and binding['identityAndCostumeOnly'] is True and
            binding['directImageReview'] is True, 'Reference scope differs')
    current = catalog['models']['live2d/AC_' + model]
    canonical = json.dumps(current, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    require(hashlib.sha256(canonical).hexdigest() == binding['catalogModelEntryCanonicalSha256'],
            'Current full model row differs from the reviewed row')
    require(json.loads(Path(binding['catalogModelEntryFile']['file']).read_text()) == current,
            'Saved model row differs from current full row')
    actual = binding['actualAttribution']
    index = json.loads(Path(binding['actualCaptureIndex']['file']).read_text())
    run = index['runs'][actual['run']]
    frame = run['actorPixelSequences'][actual['node']]['frames'][actual['frameIndex']]
    require(frame['instance'] == actual['instance'] and frame['actor'] == actual['actor'] and
            frame['actor']['model'] == model and frame['instance']['modelId'] == model,
            'Historical actual canvas model/instance attribution differs')
    require(sha(frame['path']) == binding['anchor']['sha256'] and
            frame['sha256'] == binding['anchor']['sha256'] and
            frame['opacity'] == actual['cssOpacity'], 'Actual pixel bytes or CSS alpha differs')
    require(binding['actorOriginalEqualsInstalled'] is True, 'Original actor binding differs')
    bindings.append(dict(model=model, actualNode=actual['node'], frameIndex=actual['frameIndex'],
                         instance=frame['instance'], cssOpacity=frame['opacity'],
                         actorPngSha256=frame['sha256'], historicalTrialAccepted=False))

inputs = [
    ('batch3-seven-rom-character-only-draft.json', 'd3c261e38a27ab0cad9b4bb5cc1c02155c6cc72fb182a913f56726e5b81b3204', 7),
    ('batch4-seven-rom-character-only-draft.json', 'a1e68e6e6623f551310a9f4939e3b9ba14d9d53e3cb1bd56a1648fcdd907678d', 7),
    ('batch5-three-rom-character-only-draft.json', '027ccd116cfd7533c2f80117ba4609674ffd857e7aaa327ebdfb529fc455afee', 3),
    ('batch6-eight-felt-rom-character-only-draft.json', '082adde62ec895c2c4435c45560a0bffa44a5ca34066f7563308b7f3c87e377d', 8),
    ('batch7-four-felt-character-only-draft.json', '8cdb7b2e2cb2b3351cdfe286fa0b5328e56b0b18803c8462697f327ae13bd4ce', 4),
]
snapshot = InstalledSnapshot(ROOT, ROOT / 'story_crowd_data')
seen, models = set(), Counter()
for name, digest, count in inputs:
    packet = load(name, digest)
    require(packet['reviewer'] == '/root/felt_entry_offline_review' and len(packet['changes']) == count,
            'Packet reviewer/count differs')
    for row in packet['changes']:
        identity = (row['sceneId'], row['scenarioId'])
        require(identity not in seen, 'Duplicate proposed node')
        seen.add(identity)
        native, review = snapshot.node(*identity, row['stableKey'])
        require(review['sourceText'] == row['sourceText'] and native['character'] == '' and
                row['expected'] == {'character': ''}, 'Current node/empty-field/source guard differs')
        require(set(row['fields']) == {'character'} and
                row['fields']['character'] in ['live2d/AC_rom01', 'live2d/AC_felt01'],
                'Packet exceeds the guarded identity scope')
        evidence = row['evidence']
        require(evidence['directImageReview'] is True and evidence['fullFrameReview'] is True and
                evidence['motionAndExpressionVerified'] is False, 'Visual scope differs')
        models[row['fields']['character']] += 1
coverage = load('full-part98-coverage-manifest.json',
                '73e028a242b9881cfbe60e46c6e026fa5888de53ebc9012daf682637d9f381b2')
require(coverage['counts']['allocatedObservations'] == 98 and
        coverage['counts']['newCharacterOnlyDrafts'] == 36 and
        coverage['counts']['pendingIdentityObservations'] == 61 and
        coverage['counts']['unreviewedAllocatedObservations'] == 0, 'Full coverage counts differ')
snapshot.unchanged_on_disk()
output = R / 'p29-remaining-identities-root-preflight-v1.json'
require(not output.exists(), 'Use a fresh receipt path')
result = dict(status='passed_metadata_current_guards_and_exact_actual_pixel_attribution',
              nodes=len(seen), proposedByModel=dict(models), filesChecked=len(checked),
              historicalActualBindings=bindings, fullAllocatedObservations=98,
              mainThreadViewedImages=False, actingAccepted=False, geometryAccepted=False,
              historicalFailedTrialAccepted=False, formalWrites=0,
              checkedFiles=[dict(file=str(path), sha256=digest) for path, digest in sorted(checked.items())])
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'checkedFiles'}))
