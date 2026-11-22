"""Verify complete saved documents and ownership for one approved field batch."""
from pathlib import Path
import argparse
import copy
import gzip
import hashlib
import json
import subprocess

A = Path('/home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121')
D = A / 'data-checkout'
parser = argparse.ArgumentParser()
parser.add_argument('--preparation', required=True)
parser.add_argument('--staging', required=True)
parser.add_argument('--parent', required=True)
parser.add_argument('--field', choices=['voice', 'character'], required=True)
args = parser.parse_args()
O, S = Path(args.preparation), Path(args.staging)
assert O.parent == S.parent == A
CAPTURE = O / 'saved-verification-inputs-v1'
CAPTURE.mkdir()
inputs = []


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def parsed(raw, label):
    # Preserve the exact held bytes before parsing, including the actual
    # exception document on failure. Verification never reruns a business gate.
    p = CAPTURE / (str(len(inputs) + 1).zfill(2) + '.raw.gz')
    p.write_bytes(gzip.compress(raw, mtime=0))
    item = dict(label=label, bytes=len(raw), sha256=digest(raw), archive=p.name,
                archiveSHA256=digest(p.read_bytes()))
    inputs.append(item)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        doc = error.doc.encode('utf-8', 'surrogatepass')
        (CAPTURE / 'actual-exception-doc.gz').write_bytes(gzip.compress(doc, mtime=0))
        (CAPTURE / 'failure.json').write_text(json.dumps(dict(input=item,
            error=str(error), position=error.pos, docSHA256=digest(doc), cause='unknown'), indent=2) + '\n')
        raise


def current(name):
    return parsed((D / name).read_bytes(), 'saved:' + name)


def before(name):
    raw = subprocess.check_output(['git', '-C', str(D), 'show', args.parent + ':' + name])
    assert digest(raw) == approval['all285GlobalSceneMetadataAndAssetGuards'][str(D / name)]
    return parsed(raw, 'parent-git:' + name)


approval = parsed((O / 'preflight.root-approved.json').read_bytes(), 'root-preflight')
assert approval['dataHead'] == args.parent
packet = parsed((O / 'node-fields.root-approved.json').read_bytes(), 'root-packet')
stage = parsed((S / 'manifest.json').read_bytes(), 'stage-manifest')
assert packet['baseSha'] == args.parent
assert all(set(change['fields']) == {args.field} for change in packet['changes'])
saved_files = {}
for name, expected_sha in stage['files'].items():
    if name.startswith(('native/', 'review/')):
        raw = (D / name).read_bytes()
        assert digest(raw) == expected_sha
        saved_files[name] = expected_sha
scenes = {change['sceneId'] for change in packet['changes']}
for scene in scenes:
    name = f'native/scenes/{scene}.json'
    old, new = before(name), current(name)
    undo = copy.deepcopy(new)
    for change in packet['changes']:
        if change['sceneId'] != scene:
            continue
        row = undo['scenario_list'][change['arrayIndex']]
        assert row['scenario_id'] == change['scenarioId'] and row['uniq_id'] == change['uniqueId']
        assert row[args.field] == change['fields'][args.field]
        row[args.field] = change['expected'][args.field]
    assert undo == old
    name = f'review/scenes/{scene}.json'
    assert current(name) == parsed((S / name).read_bytes(), 'reviewed-stage:' + name)
old, saved = before('manifest.json'), current('manifest.json')
expected = copy.deepcopy(old)
summaries = {row['id']: row for row in stage['scenes']}
expected['scenes'] = [copy.deepcopy(summaries.get(row['id'], row)) for row in old['scenes']]
assert saved == expected
old, saved = before('review/native-restoration.json'), current('review/native-restoration.json')
expected = copy.deepcopy(old)
expected['files'].update(saved_files)
for scene, summary in summaries.items():
    expected['scenes'][str(scene)] = digest((json.dumps(summary, ensure_ascii=False, indent=2) + '\n').encode())
batch = digest((S / 'manifest.json').read_bytes())[:20]
assert batch not in old['batches']
expected['batches'].append(batch)
assert saved == expected
apply_report = parsed((O / 'apply.original.stdout.log').read_bytes(), 'original-apply')
batch_name = f'review/restoration-batches/{batch}.json'
assert current(batch_name) == {key: value for key, value in apply_report.items() if key != 'applied'}
changed = set(saved_files) | {'manifest.json', 'review/native-restoration.json'}
for path, expected_sha in approval['all285GlobalSceneMetadataAndAssetGuards'].items():
    if str(Path(path).relative_to(D)) not in changed:
        assert digest(Path(path).read_bytes()) == expected_sha
for name, expected_sha in approval['protectedFirstThree'].items():
    assert digest((D / name).read_bytes()) == expected_sha
for name in changed | {batch_name}:
    saved_files[name] = digest((D / name).read_bytes())
(CAPTURE / 'parse-inputs.json').write_text(json.dumps(inputs, indent=2) + '\n')
result = dict(rootConfirmed=True, parentHead=args.parent, batchId=batch,
    field=args.field, exactNativeLeafChanges=len(packet['changes']),
    completeNativeRowsOtherFieldsBranchesAndOrderExact=True,
    savedReviewsEqualFullyReviewedStagingBytes=True,
    completeManifestOnlyTargetSummaryReplacements=True,
    completeOwnershipOnlyTargetHashesSummaryTokensAndOneBatchAppend=True,
    oldBatches=len(old['batches']), newBatches=len(saved['batches']),
    otherDataGuardsUnchanged=285-len(changed), all22ProtectedExact=True,
    actualParseInputsPreserved=True, savedFiles=saved_files,
    fullEntryMotionFaceGeometryTimingOrSavedGameplayAccepted=False,
    wholeSceneOrEpisodeAccepted=False)
(O / 'root-saved-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(batchId=batch, field=args.field,
    nativeLeaves=len(packet['changes']), savedFiles=len(saved_files))))
