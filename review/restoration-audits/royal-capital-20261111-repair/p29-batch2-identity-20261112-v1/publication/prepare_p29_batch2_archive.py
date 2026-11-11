"""Archive the accepted two-character P29 packet and prove its narrow delta.

Original full98 and raw snapshot bytes are immutable historical evidence.
Current installation is audited separately: seven new identities across the
first two packets, one shared prior identity,29 confirmed uninstalled,61 pending
and27 outside-scope rows. No pose, motion, geometry or original CSV is signed.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/home/rikka/Projects/stella')
R = Path(__file__).resolve().parent
DATA = ROOT / 'story_crowd_data'
EVIDENCE = R / 'visual-high/agent-reviewed-p29-identity-v1'
BASE = 'f7c3bd6dbd66d18d5c56502dc7489de456f0c11d'
AUDITS = DATA / 'review/restoration-audits/royal-capital-20261111-repair'
DEST = AUDITS / 'p29-batch2-identity-20261112-v1'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def before(name):
    return json.loads(subprocess.check_output(['git', '--no-optional-locks', 'show', f'{BASE}:{name}'], cwd=DATA))


def audit_current():
    full_path = EVIDENCE / 'full-part98-coverage-manifest.json'
    full = read(full_path)
    packet_path = R / 'visual-high/accepted-p29-batch2-identities-20261112-v1.json'
    packet = read(packet_path)
    first = read(R / 'visual-high/accepted-p29-batch1-identities-20261112-v1.json')
    new_keys = {(row['sceneId'], row['scenarioId']) for row in packet['changes']}
    installed_keys = new_keys | {(row['sceneId'], row['scenarioId']) for row in first['changes']}
    assert new_keys == {(10040051, 18), (10040051, 20)} and len(installed_keys) == 7
    current, old, reviews = {}, {}, {}
    for scene in [10040002, 10040051, 10040052, 10040053]:
        name = f'native/scenes/{scene}.json'
        current[scene] = {row['scenario_id']: row for row in read(DATA / name)['scenario_list']}
        old[scene] = {row['scenario_id']: row for row in before(name)['scenario_list']}
        reviews[scene] = read(DATA / f'review/scenes/{scene}.json')['scenarios']
    installed, uninstalled, shared, pending, keys, ordinals = [], [], [], [], [], []
    for row in full['decisions']:
        scene, node = row['sceneId'], row['scenarioId']
        key = (scene, node)
        review = reviews[scene][str(node)]
        assert (review['stableKey'], review['sourceText']) == (row['stableKey'], row['sourceText'])
        actual, previous = current[scene][node], old[scene][node]
        if key in new_keys:
            assert previous['character'] == '' and actual['character'] == 'live2d/AC_subaru01'
            assert {k: v for k, v in actual.items() if k != 'character'} == {k: v for k, v in previous.items() if k != 'character'}
        else:
            assert actual == previous, key
        entry = dict(sceneId=scene, scenarioId=node, ordinal=row['ordinal'], stableKey=row['stableKey'], sourceText=row['sourceText'])
        if row['classification'] == 'confirmed_identity_new_field':
            expected = 'live2d/AC_' + row['candidateModel']
            if key in installed_keys:
                assert actual['character'] == expected
                installed.append(dict(entry, character=expected, thisBatch=key in new_keys, exactMatch=True))
            else:
                assert not actual['character']
                uninstalled.append(dict(entry, confirmedCharacter=expected, unchanged=True))
        elif row['classification'] == 'already_installed_identity_reconfirmed':
            assert actual['character'] == 'live2d/AC_' + row['candidateModel']
            shared.append(dict(entry, character=actual['character'], unchanged=True))
        else:
            pending.append(dict(entry, classification=row['classification'], unchanged=True))
        keys.append(key)
        ordinals.append(row['ordinal'])
    assert sorted(ordinals) == list(range(98)) and len(set(keys)) == 98
    assert (len(installed), len(uninstalled), len(shared), len(pending)) == (7, 29, 1, 61)
    outside = []
    for row in full['outsidePart29ObservationScope']:
        scene, node = row['sceneId'], row['scenarioId']
        assert current[scene][node] == old[scene][node]
        outside.append(dict(sceneId=scene, scenarioId=node, classification=row['classification'], unchanged=True))
    assert len(outside) == 27 and sum(map(len, current.values())) == 125

    # Manifest warning refresh is a derived sidecar update, not another native
    # field repair. Require exactly the two removed character warnings while
    # preserving every other scene entry and issue property/order.
    manifest, old_manifest = read(DATA / 'manifest.json'), before('manifest.json')
    assert {k: v for k, v in manifest.items() if k != 'scenes'} == {k: v for k, v in old_manifest.items() if k != 'scenes'}
    removals = []
    for entry, previous in zip(manifest['scenes'], old_manifest['scenes']):
        if entry['id'] != 10040051:
            assert entry == previous
            continue
        assert {k: v for k, v in entry.items() if k != 'issues'} == {k: v for k, v in previous.items() if k != 'issues'}
        assert len(entry['issues']) == len(previous['issues'])
        for issue, old_issue in zip(entry['issues'], previous['issues']):
            if issue != old_issue:
                assert old_issue['scenarioId'] in [18, 20] and old_issue['code'] == 'performance_unrecovered'
                assert {k: v for k, v in issue.items() if k != 'fields'} == {k: v for k, v in old_issue.items() if k != 'fields'}
                assert issue['fields'] == [value for value in old_issue['fields'] if value != 'character']
                removals.append(old_issue['scenarioId'])
    assert sorted(removals) == [18, 20]
    report = dict(status='passed7_new_installed29_uninstalled1_shared61_pending', executedBy='/root/multi_actor_geometry_review',
        createdUtc=datetime.now(timezone.utc).isoformat(), baseCommit=BASE, thisBatchNewCharacterFields=2,
        newlyInstalledCharacterFields=7, confirmedButUninstalled=29, preexistingSharedIdentity=1,
        totalInstalledAssignmentsWithinObservationScope=8, mappedNativeRows=125, allocatedObservations=98,
        uniqueOrdinals=98, installedByModel=dict(Counter(row['character'] for row in installed)),
        installedExactMatches=installed, uninstalledConfirmedRows=uninstalled, sharedExistingRows=shared,
        pendingUnchanged=pending, pendingByClassification=dict(Counter(row['classification'] for row in pending)),
        outsideScopeUnchanged=outside, manifestCharacterWarningRemovals=removals,
        historicalCoverage=dict(file=str(full_path), sha256=sha(full_path.read_bytes())),
        acceptedPacket=dict(file=str(packet_path), sha256=sha(packet_path.read_bytes())),
        nodeIdsStableKeysJapaneseSourceAndAllOtherNativeFieldsProtected=True,
        outsideScopeAuthorizesDeletionOrActorClearing=False, historicalSnapshotBytesRewritten=False,
        motionFaceGeometryOriginalCsvOrFullPartAccepted=False, newBrowserOpened=False, newPlaybackVisits=0)
    path = R / 'p29-current-install-batch2-v1.json'
    write_new(path, report)
    return path


def main():
    assert not DEST.exists(), 'Never replace an existing archive'
    audit = audit_current()
    catalog_path = DATA / 'assets/catalog.json'
    catalog = read(catalog_path)
    original_row = read(EVIDENCE / 'subaru01-current-catalog-row.json')
    current_row = catalog['models']['live2d/AC_subaru01']
    assert current_row == original_row and len(catalog['models']) == 43
    binding = read(EVIDENCE / 'subaru01-assembled-original-binding.json')
    model_report = dict(status='passed_current_subaru_row_equals_historical_row', models=43,
        currentCatalogSha256=sha(catalog_path.read_bytes()),
        historicalWholeCatalogSha256=binding['currentCatalogSnapshotSha256'],
        historicalWholeCatalogIsNotCurrent=True,
        currentSubaruRowCanonicalSha256=sha(json.dumps(current_row, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()),
        existingBinding=dict(file=str(EVIDENCE / 'subaru01-assembled-original-binding.json'), sha256=sha((EVIDENCE / 'subaru01-assembled-original-binding.json').read_bytes())),
        newAssetsAdded=False, motionContextAccepted=False)
    model_path = R / 'p29-batch2-current-model-binding-v1.json'
    write_new(model_path, model_report)
    files = [(R / 'visual-high/accepted-p29-batch2-identities-20261112-v1.json', 'identity/accepted.json')]
    for name in ['batch2-two-character-only-draft.json', 'batch2-ord15to29-coverage.json',
                 'batch2-ord15to29-direct-review-receipt.json', 'batch2-delivery-receipt.json',
                 'batch2-source-snapshot-provenance.json', 'batch2-static-reference-requests-delivery.json',
                 'batch2-static-reference-request-attempt1-failure.json']:
        files.append((EVIDENCE / name, 'identity/' + name))
    files += [(p, 'batch2-source-snapshots/' + p.name) for p in sorted((EVIDENCE / 'batch2-source-snapshots').iterdir()) if p.is_file()]
    for change in read(files[0][0])['changes']:
        witness = change['evidence']['sourceWitness']
        source = Path(witness['frame'])
        assert sha(source.read_bytes()) == witness['frameSha256']
        files.append((source, 'images/' + source.name))
    for name in ['p29-batch2-owner-preflight-v1.json', 'p29-batch2-owner-repair-v1.json',
                 'p29-batch2-owner-dryrun-v1.json', 'p29-batch2-owner-apply-v1.json',
                 'p29-batch2-publication-audit-v1.json', 'p29-batch2-root-readback-v1.json',
                 audit.name, model_path.name, Path(__file__).name]:
        files.append((R / name, 'publication/' + name))
    for name in ['p29-batch2-owner-repair-v1.stderr.log', 'p29-batch2-owner-dryrun-v1.stderr.log',
                 'p29-batch2-owner-apply-v1.stderr.log', 'p29-batch2-publication-audit-v1.stderr.log']:
        files.append((R / name, 'publication/' + name))
    for name in ['plan.json', 'repair-report.json']:
        files.append((R / 'staging-p29-batch2-20261112-v1' / name, 'staging/' + name))
    archive = dict(schema='stella.exact_evidence_archive.v1', package='p29-batch2-identity-20261112-v1',
        executedBy='/root/multi_actor_geometry_review', baseCommit=BASE, thisBatchNewCharacterFields=2,
        cumulativeP29NewInstalled=7, confirmedButUninstalled=29, preexistingSharedInstalled=1,
        pending=61, outsideScopeNativeRows=27, newAssetsBrowserSourceRegistryOrPlayback=False,
        motionFaceGeometryCsvOrFullPartAccepted=False, copiedFiles=[], existingSharedEvidence=[], localOnlyEvidence=[])
    for source, relative in files:
        raw = source.read_bytes()
        if source.suffix == '.json':
            assert b'data:image/' not in raw
        # Preserve text containing trailing spaces or log CR bytes through an
        # exact UTF-8 raw_text envelope. Never normalize the original source.
        is_text = source.suffix in ['.json', '.py', '.md', '.log', '.txt']
        trailing = is_text and any(line.rstrip(b'\r\n').endswith((b' ', b'\t')) for line in raw.splitlines(keepends=True))
        envelope = trailing or source.suffix in ['.log', '.txt']
        original = None
        if envelope:
            text = raw.decode('utf-8')
            value = dict(schema='stella.exact_raw_text.v1', source=str(source), sourceBytes=len(raw), sourceSha256=sha(raw), raw_text=text)
            encoded = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
            assert json.loads(encoded)['raw_text'].encode('utf-8') == raw
            original = dict(source=str(source), bytes=len(raw), sha256=sha(raw), rawTextRoundtrip=True)
            wrapped = R / 'p29-batch2-exact-raw-text-v1' / (Path(relative).name + '.raw-text.json')
            wrapped.parent.mkdir(parents=True, exist_ok=True)
            with wrapped.open('xb') as stream:
                stream.write(encoded)
            source, raw, relative = wrapped, encoded, relative + '.raw-text.json'
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
        assert target.read_bytes() == raw
        archive['copiedFiles'].append(dict(source=str(source), archive=relative, bytes=len(raw), sha256=sha(raw),
            crlfLines=raw.count(b'\r\n'), originalRawText=original))
    shared_files = ['identity/full-part98-coverage-manifest.json', 'identity/full-part98-delivery-receipt.json',
                    'identity/subaru01-assembled-original-binding.json', 'identity/subaru01-current-catalog-row.json',
                    'identity/subaru01-original-controller.json', 'identity/p29-scene-recording-mapping.json',
                    'publication/p29-batch2-root-reference-preflight-v1.json']
    for relative in shared_files:
        source = AUDITS / 'p29-batch1-identity-20261112-v1' / relative
        archive['existingSharedEvidence'].append(dict(archive='../p29-batch1-identity-20261112-v1/' + relative,
            bytes=source.stat().st_size, sha256=sha(source.read_bytes()), historicalBytesPreserved=True))
    anchor = Path(binding['anchor']['file'])
    committed_anchor = AUDITS / 'p28-batch2-identity-v48/images/reference-subaru01-anchor.png'
    assert anchor.read_bytes() == committed_anchor.read_bytes() and sha(anchor.read_bytes()) == binding['anchor']['sha256']
    archive['existingSharedEvidence'].append(dict(archive='../p28-batch2-identity-v48/images/reference-subaru01-anchor.png',
        bytes=anchor.stat().st_size, sha256=sha(anchor.read_bytes()), historicalBytesPreserved=True))
    archive['localOnlyEvidence'].append(dict(binding['capture'], copied=False,
        reason='Historical embedded-pixel capture; exact anchor already archived; body/face context is not acceptance.'))
    write_new(DEST / 'MANIFEST.json', archive)
    print(json.dumps(dict(status='archived', copiedFiles=len(files), sharedReferences=len(archive['existingSharedEvidence']),
        manifestSha256=sha((DEST / 'MANIFEST.json').read_bytes()), currentAudit=str(audit)), ensure_ascii=False))


if __name__ == '__main__':
    main()
