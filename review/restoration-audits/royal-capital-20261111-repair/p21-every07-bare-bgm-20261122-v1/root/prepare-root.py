"""Bind one reviewed BGM identity to the current immutable data snapshot.

This is metadata preparation only. The original stage/audit/apply modules
remain separate operations. Recovery stableKey is not Studio's optional UI
node ID; summarized negative controls are compared with their declared three
fields, while their complete original measurement JSON remains hash-bound.
"""
from pathlib import Path
import hashlib
import json
import subprocess
from datetime import datetime, timezone

A = Path('/home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121')
D = A / 'data-checkout'
K = A / 'p21-every07-bare-bgm-normal-preparation-rootfalse-v1'
O = Path(__file__).resolve().parent


def load(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    path = Path(path)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest)


def bind(item):
    assert ref(item['path']) == item, item['path']


head = subprocess.check_output(['git', '-C', str(D), 'rev-parse', 'HEAD'], text=True).strip()
assert head == '610795a930985436f1e66efdf195e613b0289086'
assert subprocess.check_output(['git', '-C', str(D), 'status', '--short'], text=True) == ''
packet = load(K / 'node-fields.rootfalse.json')
request = load(K / 'root-request.template.rootfalse.json')
guards = load(K / 'target-guards.rootfalse.json')
measurement = load(K / 'measurement-review.rootfalse.json')
peer = ref(A / 'p21-every07-bare-bgm-static-peer-v1/receipt.rootfalse.json')
assert peer['sha256'] == 'cd8cd2bda100c761c7e7e49ecafb28d783b3bb0671feeecb166102ec71009488'
assert ref(K / 'node-fields.rootfalse.json')['sha256'] == '24b9199d555f0340bd76d2092badae69c2bfb334f9f853fa11e659bae7f40973'
drift = []
for item in load(K / 'input-bindings.rootfalse.json')['bindings']:
    actual = ref(item['path'])
    if actual != item:
        assert item['path'] in [str(D / 'assets/catalog.json'), str(D / 'assets/package.json')]
        drift.append(dict(original=item, current=actual))
assert len(drift) == 2
for item in request['codeGuards']:
    bind(item)
target = guards['targets'][0]
bind(target['native'])
bind(target['review'])
native, review = load(D / 'native/scenes/10030001.json'), load(D / 'review/scenes/10030001.json')
row = native['scenario_list'][2]
assert len(native['scenario_list']) == 20 and row == target['wholeCurrentNativeRow']
assert row['uniq_id'] == 1003000100003 and row['scenario_id'] == 3
assert review['scenarios']['3']['stableKey'] == 's10030001-p21-at0023'
for field, value in packet['changes'][0]['expected'].items():
    assert row[field] == value, field
assert row['branch_list'] == target['branchList']
assert row['branch_list'][0]['transition_list'][0]['next_scenario_id'] == 4

originals = {}
for name, item in measurement['originalMeasurements'].items():
    bind(item)
    originals[name] = load(item['path'])
for original in originals.values():
    assert original['sourceSha256'] == 'b3893cabaa51fd06a943f1faabcf4455af46ee1ba68fa0099a0c7e9ba0c37d4b'
    assert not original['audioListened']
controls = []
for control in measurement['full65LibraryControls']:
    values = originals['location']['candidates'][control['key']]
    assert len(values) == len({value['id'] for value in values}) == 65
    winner = max(values, key=lambda value: abs(value['signedCorrelation']))
    assert winner == control['winner']
    others = [value for value in values if value['id'] != winner['id']]
    summarized = [{key: value[key] for key in ('id', 'signedCorrelation', 'exactTrackSample')}
                  for value in others]
    assert summarized == control['all64Others']
    strongest = max(others, key=lambda value: abs(value['signedCorrelation']))
    assert strongest == control['strongestOtherSignedControl']
    assert winner['id'] == 'bgm_adv_every07_cd2_13' and winner['signedCorrelation'] > 0
    controls.append(dict(query=control['key'], winner=winner, strongestOtherSigned=strongest, otherTracks=64))
queries = [next(query for query in originals[name]['sourceQueries']
                if query['start'] == 23 and query['duration'] == 3) for name in ('opening', 'location')]
assert queries[0] == queries[1]
assert queries[0]['pcmF32leSha256'] == '74103dab4fa39b62d96d8c22af5e6c239c24a9a7603d52039265c2b5a767870d'
short = []
for at, sample in [(23, 363), (23.5, 1363), (24, 2363)]:
    values = originals['refinement']['candidates'][f'at-{at:.4f}']
    assert len(values) == 1
    value = values[0]
    assert value['id'] == 'bgm_adv_every07_cd2_13' and value['exactTrackSample'] == sample
    assert value['signedCorrelation'] > .77 and 23 <= value['time'] and value['time'] + value['duration'] <= 25
    short.append(value)
source_video = ref(originals['location']['sourceVideo'])
assert source_video['sha256'] == originals['location']['sourceSha256']
assert sum(len(values) for original in originals.values() for values in original['candidates'].values()) == 397

paths = sorted((D / 'native/scenes').glob('*.json')) + sorted((D / 'review/scenes').glob('*.json'))
assert len(paths) == 280
paths += [D / name for name in ('manifest.json', 'review/native-restoration.json', 'assets/catalog.json', 'assets/package.json')]
snapshot = {str(path.relative_to(D)): {key: value for key, value in ref(path).items() if key != 'path'} for path in paths}
assert len(snapshot) == 284
protected = load(A / 'ordinary-QA-root-bindings-edd4afed-p30v2-v1/inventory.rootfalse.json')['protectedFirstThree']
assert len(protected) == 22
for name, digest in protected.items():
    assert snapshot[name]['sha256'] == digest, name
resources = [ref(D / 'assets' / name) for name in ('catalog.json', 'package.json', 'preview/catalog.json',
             'preview/music/bgm_adv_every07_cd2_13.opus', 'preview/music/bgm_adv_every07_cd2_13.json')]
assert resources[0]['sha256'] == '009fb8072b8cf56f6c95ade4587f4132cabd2eae9e7ee74af130c4582087ff87'
assert resources[1]['sha256'] == '47ca071baf350f30aff163b743e6c315e426e338537b7b09f8d8cd34c5cb5fde'
assert load(D / 'assets/catalog.json')['music']['bgm_adv_every07_cd2_13']['url'] == 'preview/music/bgm_adv_every07_cd2_13.opus'
preflight = dict(schema='stella.p21.every07.normal-root-preflight.v1', rootConfirmed=True,
    createdAt=datetime.now(timezone.utc).isoformat(), baseHead=head, sourceOwnerPacket=ref(K / 'node-fields.rootfalse.json'),
    independentPeer=peer, originalMeasurementRefs=measurement['originalMeasurements'], freshSourceVideoBytesSHA=source_video,
    controls=controls, threeOneSecondInCardWindows=short, all397OriginalStoredCandidateRowsRead=True,
    all20RowsUIDIndexStableKeyAnd13ExpectedExact=True, sourceResourceIdentityOnlyAccepted=True,
    source23ThreeSecondCrossesCardBoundarySoOneSecondControlsRequired=True, source32ReferenceNotExtrapolatedOffset=True,
    newAudioComputedOrListened=False, originalCSVFadeRestartGainLoopOffsetSTOPOrPhaseAccepted=False,
    controlledResourceMetadataDrift=drift, resourceRegistrationFinalReceipt=ref(A / 'p21-every07-registration-final-publication-receipt-v1.json'),
    resourceProductionReceipt=ref(A / 'p21-every07-registration-production-readback-v1/receipt.json'), resourceGuards=resources,
    dataGuards=snapshot, protectedFirstThree=protected, other139NativeReviewPairsGuarded=True, codeGuards=request['codeGuards'],
    beforeTargetNative=native, beforeTargetReview=review,
    rootMetadataErrorsPreserved=[ref(O / name) for name in ('root-preflight-first-error.json', 'root-preflight-second-error-and-control-diagnostics.json')],
    wholeSceneAccepted=False)
preflight_path = O / 'root-preflight.json'
preflight_path.open('x').write(json.dumps(preflight, ensure_ascii=False, indent=2) + '\n')
packet.update(rootConfirmed=True, executionAuthorized=True, installationAuthorized=False, installable=True, baseSha=head,
    status='root-approved-one-bare-resource-ID-for-normal-stage-audit-not-yet-apply', requiresFinalFreshRootBinding=False,
    resourceRegistrationPending=False, rootPreflight=ref(preflight_path), independentPeer=peer)
packet['changes'][0]['rootConfirmed'] = True
evidence = packet['changes'][0]['evidence']
evidence['rootReviewedMinimalResourceIdentityOnly'] = True
evidence['registrationPrerequisite'].update(appliedAndFreshPublishedHEADVerified=True,
    finalRegistrationReceipt=ref(A / 'p21-every07-registration-final-publication-receipt-v1.json'), installedResourceGuards=resources)
packet_path = O / 'node-fields.root-approved.json'
packet_path.open('x').write(json.dumps(packet, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(rootPreflight=ref(preflight_path), approvedPacket=ref(packet_path), guardedFiles=len(snapshot),
                     protected=len(protected), sourceIdentityOnly=True, stagingNotExecuted=True, baseHead=head)))
