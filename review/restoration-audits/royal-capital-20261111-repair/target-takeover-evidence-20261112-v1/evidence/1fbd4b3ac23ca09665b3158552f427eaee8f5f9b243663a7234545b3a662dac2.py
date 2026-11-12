"""Revalidate the final P30 seven-identity packet on the ARM target.

This is a read-only publication preflight, not an installer or playback test.
The final packet gained integration metadata after its old ca54646e draft, so
that draft's historical receipt must not stand in for the final packet bytes.
Every current-state claim is bound to the observed data HEAD, ownership ledger,
and exact source rows. Original failed trials remain failed: their particular
raw model canvases support costume identity only through exact actor-instance
attribution, never through the trial's overall success flag.
"""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('/home/rikka/Projects/stella')
R = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111'
OUT = Path(__file__).parent
DATA = ROOT / 'story_crowd_data'
PACKET = R / 'visual-high/accepted-p30-first15-identities-v1.json'
EXPECTED_SHA = '3b2b9a5feac1b07a3a98973bfc48fc7a44fdc03a1b9903b1f082ce7bb44d4c96'
sys.path.insert(0, str(ROOT))
from story_studio.recovery.native_repair import InstalledSnapshot


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(*args):
    return subprocess.check_output(['git', '-C', str(DATA), *args], text=True).strip()


checked = {}


def sha(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    if path not in checked:
        # Streaming keeps hashing the original recording memory-bounded. CPU
        # affinity and niceness are inherited from the command invoking this file.
        value = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                value.update(chunk)
        checked[path] = dict(sha256=value.hexdigest(), bytes=path.stat().st_size)
    return checked[path]['sha256']


def references(value):
    """Check explicit byte bindings without treating old catalog hashes as current."""
    if isinstance(value, dict):
        for key, digest_key in [('file', 'sha256'), ('frame', 'frameSha256'),
                                ('video', 'videoSha256'), ('sourcePacket', 'sourcePacketSha256')]:
            if isinstance(value.get(key), str) and value.get(digest_key):
                require(sha(value[key]) == value[digest_key], f'Reference differs: {value[key]}')
                if key == 'file' and isinstance(value.get('bytes'), int):
                    require(Path(value[key]).stat().st_size == value['bytes'],
                            f'Reference length differs: {value[key]}')
        for child in value.values():
            references(child)
    elif isinstance(value, list):
        for child in value:
            references(child)


def load(path):
    value = json.loads(Path(path).read_text())
    sha(path)
    references(value)
    return value


head_before = git('rev-parse', 'HEAD')
snapshot = InstalledSnapshot(ROOT, DATA)
require(sha(PACKET) == EXPECTED_SHA, 'Final accepted packet SHA differs')
packet = load(PACKET)
require(packet['fieldGroups'] == ['character'] and len(packet['changes']) == 7,
        'Final packet scope/count differs')
require(packet['fullPartReviewed'] is False and packet['fullPartIdentityAccepted'] is False,
        'Final packet improperly expands review scope')
catalog_path = DATA / 'assets/catalog.json'
catalog = load(catalog_path)
revalidation = load(packet['referenceRevalidation']['file'])
bindings = []
for model in revalidation['models']:
    identity = model['model']
    current = catalog['models'][model['nativeToken']]
    canonical = json.dumps(current, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    require(hashlib.sha256(canonical).hexdigest() == model['completeCatalogRowCanonicalSha256'],
            f'Full current model row differs: {identity}')
    require(load(model['completeCurrentCatalogRow']['file']) == current,
            f'Saved full model row differs: {identity}')
    binding = load(model['priorAssembledOriginalBinding']['file'])
    require(binding['identityAndCostumeOnly'] is True and binding['actorOriginalEqualsInstalled'] is True,
            'Assembled original binding scope differs')
    require(binding['catalogModelEntryCanonicalSha256'] == model['completeCatalogRowCanonicalSha256'],
            'Current model row and original assembled binding disagree')
    index = load(binding['actualCaptureIndex']['file'])
    actual = binding['actualAttribution']
    frame = index['runs'][actual['run']]['actorPixelSequences'][actual['node']]['frames'][actual['frameIndex']]
    require(frame['actor'] == actual['actor'] and frame['instance'] == actual['instance'] and
            frame['actor']['model'] == identity and frame['instance']['modelId'] == identity,
            'Actual pixel actor-instance attribution differs')
    require(frame['sha256'] == model['anchor']['sha256'] == sha(frame['path']) and
            frame['opacity'] == actual['cssOpacity'], 'Exact canvas or opacity differs')
    bindings.append(dict(model=identity, actualNode=actual['node'], frameIndex=actual['frameIndex'],
                         cssOpacity=actual['cssOpacity'], rawCanvasSha256=frame['sha256'],
                         historicalTrialAccepted=False))

mapping = load(packet['changes'][0]['evidence']['sceneRecordingMapping']['file'])
require(mapping['metadataTotalCharacterObservations'] == 161 and
        mapping['remainingMetadataObservationsNotReviewed'] == 146,
        'Bounded observation counts differ')
ledger = load(packet['changes'][0]['evidence']['sourceLedger']['file'])
require(len(ledger) == 15, 'First15 ledger count differs')
require({x['ordinal'] for x in ledger} == set(range(15)), 'First15 ordinals differ')
targets, seen, counts = [], set(), Counter()
for change in packet['changes']:
    scene, number = change['sceneId'], change['scenarioId']
    require((scene, number) not in seen, 'Duplicate target')
    seen.add((scene, number))
    native, review = snapshot.node(scene, number, change['stableKey'])
    require(native['character'] == '' and change['expected'] == {'character': ''},
            f'Current character guard differs: {scene}:{number}')
    require(review['sourceText'] == change['sourceText'], 'Source text differs')
    require(set(change['fields']) == {'character'}, 'Non-character field proposed')
    evidence = change['evidence']
    require(evidence['motionAndExpressionVerified'] is False and
            evidence['originalScriptCSVRecovered'] is False and
            evidence['directImageReview'] is True and evidence['fullFrameReview'] is True,
            'Identity evidence scope differs')
    witness = evidence['sourceWitness']
    require(witness['sceneId'] == scene and witness['scenarioId'] == number and
            witness['stableKey'] == change['stableKey'] and witness['sourceText'] == review['sourceText'],
            'Witness identity differs')
    original = ledger[evidence['originalObservationOrdinal']]
    require(all(original[key] == witness[key] for key in
                ('sceneId', 'scenarioId', 'stableKey', 'sourceText', 'frame', 'frameSha256',
                 'sourceFrameIndex', 'sourceFrameTime', 'videoSha256', 'sourceEventId')),
            'Witness differs from bounded ledger')
    matching = [x for x in review['recordings'] if x['recordingId'] == 'bili-capital-30' and
                x['ocrEventId'] == witness['sourceEventId']]
    require(len(matching) == 1 and matching[0]['start'] <= witness['time'] <= matching[0]['end'],
            'Current recording interval does not bind witness')
    counts[change['fields']['character']] += 1
    targets.append(dict(sceneId=scene, scenarioId=number, stableKey=change['stableKey'],
                        expected=change['expected'], fields=change['fields'], sourceText=change['sourceText'],
                        sourceFrame=witness['frame'], sourceFrameSha256=witness['frameSha256'],
                        sourceTime=witness['time'], currentNativeRowSha256=hashlib.sha256(
                            json.dumps(native, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()))

# The saved source snapshots must still equal each actual P30 file. They are
# historical f7c3bd6 bytes, explicitly rebound here to this observed target HEAD.
provenance = load(packet['changes'][0]['evidence']['sourceSnapshotProvenance']['file'])
for entry in provenance['files']:
    require(sha(entry['sourceFile']) == entry['rawSnapshot']['sha256'],
            f'Current P30 source differs from reviewed snapshot: {entry["sourceFile"]}')

pending = []
for entry in packet['pending']:
    native, review = snapshot.node(entry['sceneId'], entry['scenarioId'], entry['stableKey'])
    require(native['character'] == '', 'Pending character unexpectedly filled')
    pending.append(dict(ordinal=entry['ordinal'], sceneId=entry['sceneId'], scenarioId=entry['scenarioId'],
                        classification=entry['classification'], currentCharacter=native['character']))
require(len(pending) == 8, 'Pending first15 count differs')
snapshot.unchanged_on_disk()
head_after = git('rev-parse', 'HEAD')
require(head_before == head_after, 'Data HEAD changed while auditing; repeat with fresh output')
result = dict(schema='stella.target_p30_first15_preflight.v1',
              status='passed_current_metadata_guards_and_independent_costume_review',
              reviewer='/root/p30_packet_preflight', createdUtc=datetime.now(timezone.utc).isoformat(),
              dataHeadBefore=head_before, dataHeadAfter=head_after,
              packet=dict(file=str(PACKET), sha256=EXPECTED_SHA, bytes=PACKET.stat().st_size),
              sourceOwnershipSha256=hashlib.sha256(snapshot.ownership_raw).hexdigest(),
              sourceManifestSha256=hashlib.sha256(snapshot.manifest_raw).hexdigest(),
              currentCatalogSha256=sha(catalog_path), proposedByModel=dict(counts), newTargets=targets,
              first15ReviewedObservations=15, newCharacterChanges=7, preexistingAcceptedChanges=0,
              pendingFirst15=pending, remainingUnreviewedObservations=146, totalP30Observations=161,
              resources=dict(models=len(catalog['models']), backgrounds=len(catalog['backgrounds']),
                             music=len(catalog['music'])), historicalActualCanvasBindings=bindings,
              independentVisualReview=dict(originalSourceFramesViewed=7, assembledReferencesViewed=2,
                felt='Blonde braided crown, large dark bow, red scarf with gold tabs, brown buttoned vest with white fur hem, dark bandeau and bare midriff match actual felt01 canvas in all five original witnesses.',
                rom='Bald head with red spiral, white brows/side locks, colored bead earrings, broad marked torso with tiered white chest hair, ragged cape with blue-green trim and diagonal chain match actual rom01 canvas in both original witnesses.',
                scope='Costume/identity only. Static source/reference viewing does not accept body motion, facial expression, geometry, lighting, original CSV, timing or playback.'),
              oldDraftReceiptIsNotFinalPacketProof=True, fullPartReviewed=False,
              fullPartIdentityAccepted=False, actingAccepted=False, geometryAccepted=False,
              browserStarted=False, formalWrites=0, gitMutations=0, mainThreadViewedImages=False,
              checkedFiles=[dict(file=str(path), **value) for path, value in sorted(checked.items())])
output = OUT / 'receipt.json'
require(not output.exists(), 'Use a fresh receipt path')
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key not in ('checkedFiles','newTargets')}, ensure_ascii=False))
