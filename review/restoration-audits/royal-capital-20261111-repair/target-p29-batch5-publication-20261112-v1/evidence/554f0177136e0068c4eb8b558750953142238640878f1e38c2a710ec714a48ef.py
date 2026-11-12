"""Rebind accepted P29 identity packets after the ARM migration.

This independent read-only audit checks historical evidence as immutable bytes,
then checks the current importer ownership and individual native row guards.
Historical whole-catalog digests are intentionally not treated as a current
freeze: each complete reviewed model row must match the current catalog instead.
No stage, installation, browser or Git mutation is performed by this program.
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
DATA = ROOT / 'story_crowd_data'
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from story_studio.recovery.native_repair import InstalledSnapshot


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_bytes())


checked = {}


def sha(path):
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    if str(path) not in checked:
        digest = hashlib.sha256()
        with path.open('rb') as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(chunk)
        checked[str(path)] = digest.hexdigest()
    return checked[str(path)]


def references(value):
    """Validate every explicitly paired path/digest, retaining old failures.

    A successful hash proves byte identity, not visual or performance acceptance.
    In particular, success:false in a historical capture stays false even when
    one of its exact raw model canvases is an accepted costume reference.
    """
    if isinstance(value, dict):
        for key, digest in [('file', 'sha256'), ('frame', 'frameSha256'),
                            ('video', 'videoSha256')]:
            if isinstance(value.get(key), str) and value.get(digest):
                require(sha(value[key]) == value[digest], f'Reference changed: {value[key]}')
        for child in value.values():
            references(child)
    elif isinstance(value, list):
        for child in value:
            references(child)


def git(*args):
    return subprocess.check_output(['git', '--no-optional-locks', *args], cwd=DATA).decode().strip()


def main():
    head = git('rev-parse', 'HEAD')
    require(head == 'c33057d059da46e35fad96a7f31a9665c23b5fa0', 'Use a fresh audit for a later HEAD')
    require(git('status', '--porcelain') == '', 'Initial formal worktree must be clean')
    old = read(R / 'p29-remaining-identities-root-preflight-v1.json')
    require(old['filesChecked'] == 160 and len(old['checkedFiles']) == 160, 'Historical preflight scope differs')
    for item in old['checkedFiles']:
        require(sha(item['file']) == item['sha256'], f'Historical preflight bytes changed: {item["file"]}')
    snapshot = InstalledSnapshot(ROOT, DATA)
    catalog = read(DATA / 'assets/catalog.json')
    model_bindings = []
    P = R / 'visual-high/agent-reviewed-p29-identity-v1'
    for model in ['rom01', 'felt01']:
        path = P / f'{model}-assembled-original-binding.json'
        binding = read(path)
        references(binding)
        row = catalog['models'][f'live2d/AC_{model}']
        canonical = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        require(hashlib.sha256(canonical).hexdigest() == binding['catalogModelEntryCanonicalSha256'], 'Current model row differs')
        require(row == read(binding['catalogModelEntryFile']['file']), 'Saved complete model row differs')
        actual = binding['actualAttribution']
        capture = read(binding['actualCaptureIndex']['file'])
        frame = capture['runs'][actual['run']]['actorPixelSequences'][actual['node']]['frames'][actual['frameIndex']]
        require(frame['instance'] == actual['instance'] and frame['actor'] == actual['actor'], 'Actual attribution differs')
        require(frame['actor']['model'] == model and frame['instance']['modelId'] == model, 'Historical raw canvas is another model')
        require(sha(frame['path']) == frame['sha256'] == binding['anchor']['sha256'], 'Historical anchor pixels differ')
        require(frame['opacity'] == actual['cssOpacity'], 'Historical CSS opacity differs')
        require(binding['identityAndCostumeOnly'] and binding['actorOriginalEqualsInstalled'], 'Binding scope differs')
        model_bindings.append(dict(model=model, bindingFile=str(path), bindingSha256=sha(path),
            actualNode=actual['node'], frameIndex=actual['frameIndex'], cssOpacity=actual['cssOpacity'],
            actorPngSha256=frame['sha256'], historicalTrialAccepted=False))
    full = read(P / 'full-part98-coverage-manifest.json')
    require(full['counts']['mappedNativeRows'] == 125 and len(full['outsidePart29ObservationScope']) == 27, 'Coverage boundaries differ')
    by_key = {(row['sceneId'], row['scenarioId']): row for row in full['decisions']}
    seen, packets, models = set(), [], Counter()
    for batch, count in [(3, 7), (4, 7), (5, 3), (6, 8), (7, 4)]:
        path = R / 'visual-high' / f'accepted-p29-batch{batch}-identities-20261112-v1.json'
        packet = read(path)
        references(packet)
        require(packet['rootConfirmed'] and packet['fieldGroups'] == ['character'], 'Packet scope differs')
        require(packet['fullPartIdentityAccepted'] is False and len(packet['changes']) == count, 'Packet acceptance/count differs')
        rows = []
        for change in packet['changes']:
            key = (change['sceneId'], change['scenarioId'])
            require(key not in seen, 'Duplicate target')
            seen.add(key)
            native, review = snapshot.node(*key, change['stableKey'])
            require(review['sourceText'] == change['sourceText'], 'Current Japanese source differs')
            require(change['expected'] == {'character': ''} and native['character'] == '', 'Current field is no longer blank')
            require(set(change['fields']) == {'character'}, 'Non-character field included')
            value = change['fields']['character']
            require(value in ['live2d/AC_rom01', 'live2d/AC_felt01'], 'Unexpected accepted model')
            decision = by_key[key]
            require(decision['classification'] == 'confirmed_identity_new_field' and 'live2d/AC_' + decision['candidateModel'] == value, 'Full coverage decision differs')
            evidence = change['evidence']
            require(evidence['directImageReview'] and evidence['fullFrameReview'] and evidence['motionAndExpressionVerified'] is False, 'Visual acceptance scope differs')
            witness = evidence['sourceWitness']
            require((witness['sceneId'], witness['scenarioId'], witness['stableKey'], witness['sourceText']) == (*key, change['stableKey'], change['sourceText']), 'Source witness identity differs')
            require(witness['recordingId'] == 'bili-capital-29' and witness['fullFrame'] and witness['crop'] is None, 'Source frame scope differs')
            models[value] += 1
            rows.append(dict(sceneId=key[0], scenarioId=key[1], stableKey=change['stableKey'],
                expectedCharacter='', acceptedCharacter=value, sourceFrame=witness['frame'],
                sourceFrameSha256=witness['frameSha256'], sourceTime=witness['time']))
        packets.append(dict(batch=batch, file=str(path), sha256=sha(path), targets=rows,
            changedFields=['character'], motionFaceGeometryTimingAccepted=False))
    outside = []
    for item in full['outsidePart29ObservationScope']:
        scene, node = item['sceneId'], item['scenarioId']
        current, review = snapshot.node(scene, node, item['stableKey'])
        old_native = read(P / f'full-part-source-snapshots/native-scene-{scene}.json')
        original = next(row for row in old_native['scenario_list'] if row['scenario_id'] == node)
        require(current == original, 'Outside-part native row changed since reviewed snapshot')
        outside.append(dict(sceneId=scene, scenarioId=node, nativeRowSha256=hashlib.sha256(json.dumps(current, ensure_ascii=False, sort_keys=True).encode()).hexdigest(), unchanged=True))
    snapshot.unchanged_on_disk()
    require(git('rev-parse', 'HEAD') == head and git('status', '--porcelain') == '', 'Formal state changed during audit')
    result = dict(schema='stella.target_p29_preflight.v1', status='passed_read_only_target_rebinding',
        createdUtc=datetime.now(timezone.utc).isoformat(), executedBy='/root/p29_packet_preflight',
        dataHead=head, ownershipSha256=hashlib.sha256(snapshot.ownership_raw).hexdigest(),
        manifestSha256=hashlib.sha256(snapshot.manifest_raw).hexdigest(), catalogSha256=sha(DATA/'assets/catalog.json'),
        historical160FilesRehashed=True, checkedFiles=[dict(file=path, sha256=digest) for path,digest in sorted(checked.items())],
        acceptedTargets=len(seen), acceptedByModel=dict(models), packets=packets, modelBindings=model_bindings,
        outsidePartRows=outside, pendingIdentityObservations=61, fullPartIdentityAccepted=False,
        motionFaceGeometryTimingAccepted=False, formalWrites=0, newPlaybackVisits=0, browserStarted=False,
        note='Each later package must be staged against its then-current ownership. This receipt binds only the stated HEAD.')
    with (OUT/'receipt.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps({key:value for key,value in result.items() if key not in ['checkedFiles','packets','outsidePartRows']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
