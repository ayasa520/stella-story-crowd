"""Prepare three unregistered cases, then optionally bind a later freeze.

Draft preparation freezes complete target/neighbour rows and the current
41-model aggregate metadata. It deliberately does not lock whole scene files
while unrelated P27 rows are still being restored. A later explicit --freeze
run rechecks those deep guards, adds whole-file/source/Studio guards and emits
new packets in a new directory. Neither mode edits a registry or formal data,
starts an adapter/browser, or installs a candidate.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
ROOT = R.parents[3]
DATA = ROOT / 'story_crowd_data'
SITE = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'
OLD = R / 'visual-high/butler-projection-three-frame-v1/n9-assembled-bounded-review-v1'
P27 = R / 'visual-high/agent-reviewed-p27-identity-v1'
IDS = ['roswaal13-character-only-model41-v1', 'n9-hohoemu-face-normal-assembled-v2-model41',
       'n9-hohoemu-face-normal02-assembled-v2-model41']


def digest(raw): return hashlib.sha256(raw).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def rec(path):
    path = Path(path); raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': digest(raw)}
def canonical(value): return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
def git(path, *args): return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


def scene_guard(scene, route):
    native = read(DATA / f'native/scenes/{scene}.json')['scenario_list']
    review = read(DATA / f'review/scenes/{scene}.json')['scenarios']
    rows = {row['scenario_id']: row for row in native}
    guarded = [{'scenarioId': n, 'nativeRow': rows[n],
        'reviewIdentity': {key: review[str(n)][key] for key in ['stableKey', 'sourceText', 'recordings', 'branches']}}
        for n in route]
    edges = []
    for a, b in zip(route, route[1:]):
        matches = [(branch, transition) for branch in rows[a]['branch_list']
                   for transition in branch['transition_list'] if transition['next_scenario_id'] == b]
        assert len(matches) == 1, ('Not a unique real edge', scene, a, b)
        branch, transition = matches[0]
        reviewed = next(row for row in review[str(a)]['branches'] if row['branchId'] == branch['branch_id'])
        assert reviewed['state'] == 'confirmed' and reviewed['verification'] == 'observed'
        edges.append({'from': a, 'to': b, 'branchId': branch['branch_id'], 'transition': transition})
    return {'sceneId': scene, 'route': route, 'rows': guarded, 'edges': edges}


def verify_rows(guard):
    assert scene_guard(guard['sceneId'], guard['route']) == guard, 'Target/neighbour deep equality changed'


def comparison_guards(proposals):
    """Bind reused local references, including all120 existing source PNGs.

    Embedded original-video receipts remain provenance rather than a request
    to rehash a large external video. The compiler's guard paths must stay
    inside this workspace; the already-decoded local comparison frames and
    their immutable source index supply the bounded pixel references.
    """
    records = {}
    def collect(value):
        if isinstance(value, list):
            for row in value: collect(row)
        elif isinstance(value, dict):
            name = value.get('file', value.get('path'))
            if name and value.get('sha256'):
                path = Path(name); path = path if path.is_absolute() else ROOT/path
                if path.is_relative_to(ROOT) and path.is_file():
                    actual = rec(path); assert actual['sha256'] == value['sha256'], str(path)
                    if 'bytes' in value: assert actual['bytes'] == value['bytes']
                    records[actual['path']] = actual
            for row in value.values(): collect(row)
    for proposal in proposals: collect(proposal['sourceComparison'])
    source_index = proposals[1]['sourceComparison']['all120FrameIndex']['file']
    frames = read(source_index)['frames']; assert len(frames) == 120
    collect(frames)
    return list(records.values())


def prepare():
    catalog = read(DATA / 'assets/catalog.json')
    assert len(catalog['models']) == 41
    assert catalog['models']['live2d/AC_roswaal01']['id'] == 'roswaal01'
    actor_manifest = read(DATA / 'assets/player/manifest.json')
    old = read(OLD / 'n9-hohoemu-face-normal-assembled-v1.json')
    # Reuse exact selected model/source bytes, but never inherit stale 40-model
    # aggregate hashes or a whole-scene hash from the older frozen packet.
    for row in old['fileGuards']:
        path = Path(row['file'])
        if '/assets/models/' in str(path) or str(path).startswith(str(SITE)):
            assert rec(path)['sha256'] == row['sha256'], ('Old selected resource/source changed', str(path))
    guards = [scene_guard(10200006, [12, 13, 14]), scene_guard(10150004, [8, 9, 10])]
    for guard, target in [(guards[0], 13), (guards[1], 9)]:
        row = next(row['nativeRow'] for row in guard['rows'] if row['scenarioId'] == target)
        assert row['character'] == row['motion'] == '' and row['command'] == ['', '', '']
    for old_row, row in zip(old['nodeGuards'], guards[1]['rows']):
        assert canonical(row['nativeRow']) == old_row['canonicalNativeRowSha256']
        assert row['reviewIdentity']['stableKey'] == old_row['stableKey']
        assert row['reviewIdentity']['sourceText'] == old_row['sourceText']
    metadata = [DATA / ('assets/' + name) for name in ['catalog.json', 'package.json',
        'player/manifest.json', 'player/animation.json', 'player/motion_states.json', 'player/effects.json']]
    resources = []
    for model in ['roswaal01', 'subaru_butler01']:
        resources.extend(rec(path) for path in sorted((DATA / f'assets/models/{model}').rglob('*')) if path.is_file())
    resource_proof = read(P27 / 'roswaal01-resource-availability-staging-proposal.json')
    assert rec(DATA / 'assets/models/roswaal01/ac/ac.moc3')['sha256'] == resource_proof['originalMocBindings'][0]['embeddedMocSha256']
    assert rec(DATA / 'assets/models/roswaal01/ac/textures/texture_00.png')['sha256'] == resource_proof['originalTextureBindings'][0]['extractedPng']['sha256']
    request = read(P27 / 'roswaal01-single-model-reference-capture-request.json')
    witness = request['pendingNodes'][0]
    assert witness['scenarioId'] == 13 and rec(witness['originalFullFrame']['file'])['sha256'] == witness['originalFullFrame']['sha256']
    proposals = []
    for index, identity in enumerate(IDS):
        roswaal = index == 0; model = 'roswaal01' if roswaal else 'subaru_butler01'
        guard = guards[0] if roswaal else guards[1]; target = guard['route'][1]
        fields = {'character': 'live2d/AC_' + model}
        if not roswaal: fields['motion'] = 'act_hohoemu,' + ('face_normal' if index == 1 else 'face_normal02')
        source = {'request': rec(P27 / 'roswaal01-single-model-reference-capture-request.json'),
            'resourceAudit': rec(P27 / 'roswaal01-original-resource-gap-audit.json'),
            'originalResourceIdentity': resource_proof['originalTextureBindings'] + resource_proof['originalMocBindings'],
            'originalFullFrame': witness['originalFullFrame']} if roswaal else old['comparisonSource']
        proposals.append({'id': identity, 'schema': 'stella.noninstallable.assembled-review.memory-v2',
            'installable': False, 'scopeApproved': False, 'browserAuthorized': False,
            'sceneId': guard['sceneId'], 'route': guard['route'], 'target': target, 'modelId': model,
            'guard': guard, 'fields': fields, 'expectedNativeRow': guard['rows'][1]['nativeRow'],
            'projection': {'mode': 'unchanged_default_original_ADV', 'actor': actor_manifest['actors'][model],
                'cameraOverride': None, 'offsetOverride': None, 'scaleOverride': None, 'placementOverride': None},
            'sourceComparison': source, 'modelCount': 41,
            'acceptanceScope': 'static_costume_identity_only_no_motion_or_geometry_signature' if roswaal else
                'numerical_face_candidate_only_full_entry_geometry_and_acting_pending',
            'originalIdUnique': False, 'originalCSVRecovered': False,
            'pendingCountsReduced': False, 'sourceProposalUnchanged': rec(OLD / ('n9-hohoemu-face-normal-assembled-v1.json' if index != 2 else 'n9-hohoemu-face-normal02-assembled-v1.json')) if not roswaal else None})
    # Every stable record is shared by proposals but retained in a separate lock
    # to avoid duplicating megabytes of catalog JSON or stale scene file guards.
    lock = {'modelCount': 41, 'metadata': [rec(path) for path in metadata], 'selectedModelResources': resources,
        'dataHeadInformationalOnly': git(DATA, 'rev-parse', 'HEAD'), 'siteCommit': git(SITE, 'rev-parse', 'HEAD'),
        'wholeSceneFileGuardsDeferredUntilRootFreeze': True}
    write(HERE / 'model41-lock.json', lock)
    write(HERE / 'target-deep-guards.json', guards)
    for proposal in proposals: write(HERE / (proposal['id'] + '.json'), proposal)
    return proposals


def emit_packets(output, proposals, frozen):
    output.mkdir()
    stable = read(HERE / 'model41-lock.json')
    for row in stable['metadata'] + stable['selectedModelResources']:
        assert rec(ROOT / row['path']) == row, ('Model41 lock changed', row['path'])
    for proposal in proposals: verify_rows(proposal['guard'])
    receipts = stable['metadata'] + stable['selectedModelResources'] + comparison_guards(proposals) + [rec(HERE / 'model41-lock.json'), rec(HERE / 'target-deep-guards.json')]
    if frozen:
        # Bind all native/review scene bytes only after root declares the final
        # freeze. Unrelated P27 work before that point cannot silently refresh
        # any guarded target row or fixed aggregate/model bytes above.
        manifest = read(DATA / 'manifest.json')
        paths = {DATA / 'manifest.json', DATA / 'review/native-restoration.json', DATA/'README.md',
            DATA/'review/restoration-audits/royal-capital-20261111-repair/progress.json', ROOT / 'data/story_studio/project.json'}
        for entry in manifest['scenes']: paths.update([DATA / entry['path'], DATA / entry['reviewPath']])
        for prefix in ['public/player', 'public/pairing', 'public/studio']:
            paths.update(path for path in (SITE / prefix).rglob('*') if path.is_file() and path.suffix in ['.js', '.html', '.css', '.json'])
        paths.update(path for path in (SITE/'lib').rglob('*') if path.is_file() and path.suffix in ['.ts','.js','.json'])
        paths.update([R/'playback/serve.py', R/'playback/compile.mjs', R/'playback/index.html', R/'playback/canary.json'])
        paths.update([HERE / 'capture_cases.js', HERE / 'instrument.js', HERE / 'owner.py', HERE / 'index_pixels.py', HERE / 'prepare_guards.py', HERE / 'PLAN.md'])
        receipts += [rec(path) for path in sorted(paths)]
    scopes = []
    for group in [proposals[:1], proposals[1:]]:
        scene = group[0]['sceneId']; packet = {'schema': 'stella.noninstallable.bounded-memory-packet.v2',
            'installable': False, 'registered': False, 'scopeApproved': False,
            'freezeComplete': frozen, 'guardReceipts': receipts + [rec(HERE / (proposal['id'] + '.json')) for proposal in group],
            'examples': [{'id': proposal['id'], 'changes': [{'scenarioId': proposal['target'],
                'expected': proposal['expectedNativeRow'], 'fields': proposal['fields']}]} for proposal in group]}
        path = output / ('roswaal-packet.json' if scene == 10200006 else 'butler-packet.json'); write(path, packet)
        scopes.append({'sceneId': scene, 'allowedStarts': [group[0]['route'][0]],
            'exampleIds': [proposal['id'] for proposal in group], 'allowedTargets': [group[0]['target']],
            'allowedFields': list(group[0]['fields']), 'packet': str(path.relative_to(R)), 'sha256': rec(path)['sha256']})
    write(output / 'registry-PROPOSAL.json', scopes)
    write(output / 'execution-input.json', {'status': 'frozen_unapproved_not_registered' if frozen else 'draft_not_executable_wholefile_guards_deferred',
        'freezeComplete': frozen, 'scopeApproved': False, 'singleBrowserOwnerAssigned': False,
        'maxCases': 3, 'dataHeadObservedNowInformationalOnly': git(DATA, 'rev-parse', 'HEAD'),
        'cases': [{'id': proposal['id'], 'scene': proposal['sceneId'], 'route': proposal['route'],
            'target': proposal['target'], 'model': proposal['modelId'], 'fields': proposal['fields'],
            'rgbaStaticReference': proposal['modelId'] == 'roswaal01'} for proposal in proposals],
        'registryProposal': rec(output / 'registry-PROPOSAL.json'), 'requiredScopes': scopes,
        'guardReceipts': receipts, 'sourceCommit': stable['siteCommit'], 'model41Lock': rec(HERE / 'model41-lock.json'),
        'policy': {'newPagePerCase': True, 'simultaneousPages': 1, 'everyNthFrame': 2,
            'maxCompositorFramesPerCase': 300, 'overflowOrMissingEarliestPositiveAlpha': 'pending_no_retry',
            'caseFailure': 'preserve_partial_stop_remaining_close_immediately', 'imageDataStdout': False}})
    print(json.dumps({'output': str(output), 'executionInput': rec(output / 'execution-input.json'), 'frozen': frozen}))


def main():
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19 and sorted(os.sched_getaffinity(0)) == [22, 23]
    parser = argparse.ArgumentParser(); parser.add_argument('--freeze', action='store_true'); parser.add_argument('--output')
    args = parser.parse_args()
    if args.freeze:
        assert args.output, 'Freeze needs a new explicit local output directory; root schedules this later'
        output = Path(args.output).resolve(); assert output.is_relative_to(HERE) and not output.exists()
        proposals = [read(HERE / (identity + '.json')) for identity in IDS]
    else:
        proposals = prepare(); output = HERE / 'draft'
    emit_packets(output, proposals, args.freeze)


if __name__ == '__main__': main()
