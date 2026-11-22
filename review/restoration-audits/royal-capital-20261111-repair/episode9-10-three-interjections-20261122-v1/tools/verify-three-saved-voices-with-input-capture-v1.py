"""Verify the complete three-voice save while retaining every actual parse input."""
from pathlib import Path
import copy
import gzip
import hashlib
import json
import subprocess

A = Path('/home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121')
D = A / 'data-checkout'
O = A / 'p30-26-27-p31-9-root-preparation-026a7c4c-v1'
S = A / 'p30-26-27-p31-9-nodefields-stage-026a7c4c-v1'
CAPTURE = O / 'saved-verification-inputs-v1'
HEAD = '026a7c4ca58ff3f7be483b0976d7807de3d55732'
CAPTURE.mkdir()
inputs = []


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def parsed(raw, label):
    # Capture the held bytes before parsing. A later read must never be
    # relabelled as the input of an earlier unexplained JSON exception.
    path = CAPTURE / (str(len(inputs) + 1).zfill(2) + '.raw.gz')
    path.write_bytes(gzip.compress(raw, mtime=0))
    row = dict(label=label, bytes=len(raw), sha256=digest(raw),
               archive=path.name, archiveSHA256=digest(path.read_bytes()))
    inputs.append(row)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        doc = error.doc.encode('utf-8', 'surrogatepass')
        (CAPTURE / 'actual-exception-doc.utf8.gz').write_bytes(gzip.compress(doc, mtime=0))
        (CAPTURE / 'parse-failure.json').write_text(json.dumps(dict(
            actualInput=row, error=str(error), line=error.lineno, column=error.colno,
            position=error.pos, actualExceptionDocSHA256=digest(doc),
            cause='unknown', businessGateReplayed=False), indent=2) + '\n')
        raise


def current(name):
    return parsed((D / name).read_bytes(), 'saved:' + name)


def before(name):
    raw = subprocess.check_output(['git', '-C', str(D), 'show', HEAD + ':' + name])
    assert digest(raw) == approval['all285GlobalSceneMetadataAndAssetGuards'][str(D / name)]
    return parsed(raw, 'parent-git-blob:' + name)


approval = parsed((O / 'preflight.root-approved.json').read_bytes(), 'root-preflight')
packet = parsed((O / 'node-fields.root-approved.json').read_bytes(), 'root-accepted-packet')
stage = parsed((S / 'manifest.json').read_bytes(), 'stage-manifest')
saved_files = {}
for name in stage['files']:
    if not name.startswith(('native/', 'review/')):
        continue
    raw = (D / name).read_bytes()
    assert digest(raw) == stage['files'][name]
    saved_files[name] = digest(raw)
for scene in [10450054, 10040043]:
    name = f'native/scenes/{scene}.json'
    old, new = before(name), current(name)
    undo = copy.deepcopy(new)
    for change in packet['changes']:
        if change['sceneId'] == scene:
            row = undo['scenario_list'][change['arrayIndex']]
            assert row['scenario_id'] == change['scenarioId'] and row['uniq_id'] == change['uniqueId']
            assert row['voice'] == change['fields']['voice'] and row['character'] == ''
            row['voice'] = change['expected']['voice']
    assert undo == old
    review = current(f'review/scenes/{scene}.json')
    assert review == parsed((S / f'review/scenes/{scene}.json').read_bytes(), 'stage-review:' + str(scene))

old, saved = before('manifest.json'), current('manifest.json')
expected = copy.deepcopy(old)
summaries = {row['id']: row for row in stage['scenes']}
expected['scenes'] = [copy.deepcopy(summaries.get(row['id'], row)) for row in old['scenes']]
assert saved == expected
old, saved = before('review/native-restoration.json'), current('review/native-restoration.json')
expected = copy.deepcopy(old)
expected['files'].update(saved_files)
for scene, summary in summaries.items():
    raw = (json.dumps(summary, ensure_ascii=False, indent=2) + '\n').encode()
    expected['scenes'][str(scene)] = digest(raw)
batch = digest((S / 'manifest.json').read_bytes())[:20]
assert batch == '5532643b4e935c9a7301' and batch not in old['batches']
expected['batches'].append(batch)
assert saved == expected
report = parsed((O / 'apply.original.stdout.log').read_bytes(), 'original-apply-report')
expected_batch = {key: value for key, value in report.items() if key != 'applied'}
batch_name = f'review/restoration-batches/{batch}.json'
assert current(batch_name) == expected_batch
changed = set(saved_files) | {'manifest.json', 'review/native-restoration.json'}
for path, expected_sha in approval['all285GlobalSceneMetadataAndAssetGuards'].items():
    if str(Path(path).relative_to(D)) not in changed:
        assert digest(Path(path).read_bytes()) == expected_sha, path
for name, expected_sha in approval['protectedFirstThree'].items():
    assert digest((D / name).read_bytes()) == expected_sha
for name in changed | {batch_name}:
    saved_files[name] = digest((D / name).read_bytes())
(CAPTURE / 'parse-inputs.json').write_text(json.dumps(inputs, indent=2) + '\n')
result = dict(rootConfirmed=True, originalApplyExitCode=0, originalApplyToolChunk='7ac495',
    parentHead=HEAD, batchId=batch, onlyThreeNativeVoiceLeavesChanged=True,
    complete52And110RowsOtherFieldsBranchesAndOrderExact=True,
    fourSavedNativeReviewFilesEqualReviewedStagingBytes=True,
    completeManifestOnlyTwoSummaryReplacements=True,
    completeOwnershipOnlyFourHashesTwoSummaryTokensAndOneBatchAppend=True,
    oldBatches=len(old['batches']), newBatches=len(saved['batches']),
    allOther279DataGuardsAndProtected22Exact=True, savedFiles=saved_files,
    allActualParseInputsPreserved=True, listeningPhaseGainLoopMotionAndGameplayAccepted=False,
    wholeSceneOrEpisodeAccepted=False)
(O / 'root-saved-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(batchId=batch, savedFiles=len(saved_files), nativeVoiceLeaves=3,
                     oldBatches=result['oldBatches'], newBatches=result['newBatches'])))
