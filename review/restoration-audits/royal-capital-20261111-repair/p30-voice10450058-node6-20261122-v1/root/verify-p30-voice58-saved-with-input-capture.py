"""Verify the saved voice leaf, retaining each exact metadata parse input."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import subprocess
import traceback

ROOT = Path('/home/rikka/Projects/stella')
A = ROOT / 'artifacts/stella-script-continuation-20261121'
DATA = A / 'data-checkout'
HERE = A / 'p30-voice58-6-root-preparation-a1ea68ee-v1'
STAGE = HERE / 'normal-stage'
CAPTURE = HERE / 'saved-verification-input-capture-v1'
CAPTURE.mkdir()
sequence = 0


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(label, raw):
    global sequence
    sequence += 1
    stem = CAPTURE / f'{sequence:03d}'
    # Capture the same bytes and decoded string used by this parse. A later
    # successful read cannot replace the failed historical exception document.
    text = raw.decode('utf-8')
    stem.with_suffix('.raw.gz').write_bytes(gzip.compress(raw, mtime=0))
    stem.with_suffix('.decoded.gz').write_bytes(gzip.compress(text.encode(), mtime=0))
    info = dict(label=label, bytes=len(raw), sha256=sha(raw), decodedCharacters=len(text))
    stem.with_suffix('.json').write_text(json.dumps(info, indent=2) + '\n')
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        document = error.doc.encode('utf-8', errors='surrogatepass')
        stem.with_suffix('.actual-exception-document.gz').write_bytes(gzip.compress(document, mtime=0))
        info.update(originalError=str(error), traceback=traceback.format_exc(),
                    exceptionDocumentSHA256=sha(document), position=error.pos,
                    line=error.lineno, column=error.colno, cause='unknown', retry=False)
        stem.with_suffix('.failure.json').write_text(json.dumps(info, indent=2) + '\n')
        raise


def read(path):
    return parse(str(path), path.read_bytes())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


preflight = read(HERE / 'preflight.root-approved.json')
audit = read(HERE / 'audit.original.stdout.log')
applied = read(HERE / 'apply.original.stdout.log')
assert applied == {**audit, 'applied': True}
assert (HERE / 'apply.original.stderr.log').stat().st_size == 0
parent = preflight['dataHead']
for name in ['native/scenes/10450058.json', 'review/scenes/10450058.json']:
    assert (DATA / name).read_bytes() == (STAGE / name).read_bytes()

incoming = read(STAGE / 'manifest.json')
old_manifest_raw = subprocess.check_output(['git', '-C', str(DATA), 'show', parent + ':manifest.json'])
expected_manifest = parse('original HEAD manifest git-show bytes', old_manifest_raw)
assert sha(old_manifest_raw) == preflight['all284GlobalSceneMetadataAndAssetGuards'][str(DATA / 'manifest.json')]
expected_manifest['scenes'] = [incoming['scenes'][0] if row['id'] == 10450058 else row
                               for row in expected_manifest['scenes']]
assert (DATA / 'manifest.json').read_bytes() == encoded(expected_manifest)

owner_raw = subprocess.check_output(['git', '-C', str(DATA), 'show', parent + ':review/native-restoration.json'])
expected_owner = parse('original HEAD ownership git-show bytes', owner_raw)
assert sha(owner_raw) == preflight['all284GlobalSceneMetadataAndAssetGuards'][str(DATA / 'review/native-restoration.json')]
old_batches = len(expected_owner['batches'])
for name in ['native/scenes/10450058.json', 'review/scenes/10450058.json']:
    expected_owner['files'][name] = sha((DATA / name).read_bytes())
expected_owner['scenes']['10450058'] = sha(encoded(incoming['scenes'][0]))
expected_owner['batches'].append(audit['batchId'])
assert (DATA / 'review/native-restoration.json').read_bytes() == encoded(expected_owner)
expected_batch = dict(audit)
del expected_batch['applied']
batch_path = f"review/restoration-batches/{audit['batchId']}.json"
assert (DATA / batch_path).read_bytes() == encoded(expected_batch)

changed = {'manifest.json', 'review/native-restoration.json',
           'native/scenes/10450058.json', 'review/scenes/10450058.json'}
for path, expected in preflight['all284GlobalSceneMetadataAndAssetGuards'].items():
    if str(Path(path).relative_to(DATA)) not in changed:
        assert sha(Path(path).read_bytes()) == expected, path
for name, expected in preflight['protectedFirstThree'].items():
    assert sha((DATA / name).read_bytes()) == expected, name
actual_changed = set(subprocess.check_output(['git', '-C', str(DATA), 'diff', '--name-only'], text=True).splitlines())
assert actual_changed == changed
untracked = subprocess.check_output(['git', '-C', str(DATA), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
assert untracked == [batch_path]
result = dict(rootConfirmed=True, stageSession=34852, stageExitCode=0,
              auditToolChunk='24e21e', auditExitCode=0, applyToolChunk='5bb8d9', applyExitCode=0,
              parentHead=parent, batchId=audit['batchId'], onlyNativeVoiceLeafChanged=True,
              all37RowsAndOtherLeavesExact=True, fullReviewEqualsExpectedVoiceOnly=True,
              wholeManifestOnlyTargetSummaryReplacement=True,
              wholeOwnershipOnlyTwoFileHashesOneSceneDigestAndOneBatchAppend=True,
              oldBatches=old_batches, newBatches=len(expected_owner['batches']),
              allOther280DataGuardsAnd22ProtectedExact=True,
              savedFiles={name: sha((DATA / name).read_bytes()) for name in sorted(changed | {batch_path})},
              listeningPerformed=False, sourceIdentityAndLinePlacementOnly=True,
              savedOrdinaryPlaybackPending=True, wholeSceneAccepted=False,
              priorRootMetadataJSONErrorCause='unknown; its actual exception document was not retained',
              currentParseInputsCaptured=True,
              freeBytes=os.statvfs(A).f_bavail * os.statvfs(A).f_frsize)
with (HERE / 'root-saved-verification.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(result))
