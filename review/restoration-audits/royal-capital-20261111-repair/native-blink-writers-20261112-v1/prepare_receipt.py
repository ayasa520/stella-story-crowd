"""Freeze a small, reproducible receipt for this offline investigation.

Repository status is an observed concurrent-work snapshot, not a clean-tree
precondition. Parent-owned resource changes are left untouched. Validate the
original binary, metadata, prefab and reused curve hashes independently;
list all local evidence without copying original programs or image sets.
"""

import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def record(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return {'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
            'sha256': digest.hexdigest()}


def repository(path):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()
    return {'path': str(path.relative_to(ROOT)), 'head': git('rev-parse', 'HEAD'),
            'statusShort': git('status', '--short').splitlines()}


def main():
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19
    assert sorted(os.sched_getaffinity(0)) == [22, 23]
    evidence = json.loads((HERE / 'blink-writer-update-evidence.json').read_text())
    inventory_path = HERE.parent / 'visual-low/p11-felt15-blink-local-review-v1/original-blink-inventory.json'
    inventory = json.loads(inventory_path.read_text())
    assert record(inventory_path) == evidence['priorSerializedInventory']
    for source in evidence['sources']:
        assert record(ROOT / source['path']) == source
    prefabs = []
    for source in inventory['prefabs']:
        current = record(ROOT / source['path'])
        assert current['sha256'] == source['sha256']
        prefabs.append(current)
    curves_path = inventory_path.with_name('entry-eye-curve-analysis.json')
    curves = json.loads(curves_path.read_text())
    curve_sources = []
    for source in curves['entries']:
        current = record(ROOT / source['file'])
        assert current['sha256'] == source['sha256']
        curve_sources.append(current)
    reused = [record(inventory_path), record(curves_path),
              record(inventory_path.with_name('local-review-result.json'))]
    # These drafts are referenced, never rewritten. A syntax-only HUD repair
    # remains separate from the native audit and is not a browser validation.
    draft_dir = HERE.parent / 'visual-high/butler-projection-three-frame-v1/n9-assembled-bounded-review-v1'
    old_draft = record(draft_dir / 'capture_assembled_draft.js')
    assert old_draft['sha256'] == 'c22f1994123e4f1768a9513baf490fc2000edcec9ad810577354b0d3e6dc5b41'
    new_draft = record(draft_dir / 'capture_assembled_draft_v2.js')
    assert new_draft['sha256'] == '804bf79f253f40fb4ce26ce34bf228eccaf8fc3a0182116032f52d9a7697fb14'
    syntax = []
    for path in sorted(HERE.glob('*.py')):
        ast.parse(path.read_text(), filename=str(path))
        syntax.append(str(path.relative_to(HERE)))
    files = []
    for path in sorted(HERE.iterdir()):
        if not path.is_file() or path.name == 'receipt.json':
            continue
        if path.suffix == '.json':
            json.loads(path.read_text())
        files.append(record(path))
    order = json.loads((HERE / 'update-controller-type-usage-slots.json').read_text())
    adjacent = json.loads((HERE / 'adjacent-channel-evidence.json').read_text())
    result = {
        'status': 'bounded_native_static_audit_complete_recorded_writer_and_cause_pending',
        'createdUtc': datetime.now(timezone.utc).isoformat(),
        'browserOpened': False, 'nativeGameRun': False, 'imagesOpened': False,
        'formalWrites': [], 'websiteWrites': [], 'registryOrAdapterWrites': [],
        'writesScope': str(HERE.relative_to(ROOT)),
        'compute': {'nice': os.getpriority(os.PRIO_PROCESS, 0),
                    'affinity': sorted(os.sched_getaffinity(0))},
        'originalSourcesVerifiedBeforeAfterDisassembly': evidence['sources'],
        'originalSourcesVerifiedAgainAtReceipt': True,
        'originalPrefabHashesReverified': prefabs,
        'reusedCurveSourceHashesReverified': curve_sources,
        'reusedEvidence': reused,
        'repositorySnapshots': [repository(ROOT / 'story_crowd_data'),
            repository(ROOT / 'artifacts/stella-site-repair-source/.sites-checkout')],
        'concurrentChanges': 'Parent reported root-owned Roswaal availability resource edits; this audit does not touch them. Clean data status is not a precondition.',
        'files': files,
        'boundedMethods': len(evidence['selectedMethods']) + len(adjacent['selectedMethods']),
        'rawTraceBytes': evidence['disassembly']['bytes'] + adjacent['disassembly']['bytes'],
        'conditionalDelegateOrder': order['conditionalAppendOrder'],
        'verdict': {
            'staticEyeOpeningWriter': 'established_at_0x167582c',
            'staticDestinationValueWriter': 'established_at_0x1675af4',
            'timeSource': 'original_UnityEngine.Time.get_deltaTime_calls_established',
            'serializedEyeOpeningOneModeTwo': 'multiplicative_identity_not_blink_generator',
            'recordedAutoEyeBlinkInputInvocation': 'unknown',
            'recordedDynamicComponentCreation': 'unknown_not_excluded',
            'recordedGlobalAnimatorOrderAndActiveFaceState': 'unknown',
            'felt15EarlyBlinkCause': 'unknown_no_attribution',
            'installationOrMotionSignature': 'none',
        },
        'commands': [
            'nice -n 19 taskset -c 22,23 uv run --offline --no-project --with UnityPy --with capstone python ' + str((HERE / name).relative_to(ROOT))
            for name in ['inspect_blink_writers.py', 'resolve_update_order.py',
                         'inspect_adjacent_channels.py', 'bind_delegate_calls.py']],
        'validation': {'pythonAstParsed': syntax, 'allEvidenceJsonParsed': True,
                       'originalInputsMatchPriorInventory': True,
                       'hashesAndLengthsListedForEveryNewEvidenceFileExceptThisReceipt': True},
        'separateHudRevision': {
            'oldFrozenDraft': old_draft, 'newUnexecutedDraft': new_draft,
            'receipt': record(draft_dir / 'capture-draft-v2-layout-receipt.json'),
            'runtimeValidated': False,
        },
        'limitations': [
            'Static callable sites are not logs of execution in the original recording.',
            'This bounded audit does not enumerate every possible runtime writer or AddComponent path.',
            'No generic MethodRef binding, unknown math-call name, global callback order or Felt15 cause is guessed.',
        ],
    }
    output = HERE / 'receipt.json'
    with output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'receipt': record(output),
                      'report': record(HERE / 'REPORT.md'), 'files': len(files),
                      'methods': result['boundedMethods'],
                      'rawTraceBytes': result['rawTraceBytes']}))


if __name__ == '__main__':
    main()
