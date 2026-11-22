"""Future root-released P30 face-only private native snapshot.

The caller supplies the final independently checked publication/global closure.
No business module, Worker, browser or media tool is imported here. Formal
native rows are read-only. One complete A-owned52-row staged file changes only
the root-requested node4 face CSV leaf; the canonical Worker parses it later.
This controlled candidate is not a formal motion or source-phase acceptance.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import re
import subprocess
import sys
from common import HERE, ROOT, DATA, SOURCE, load, sha, digest, write, field_differences, checked_guards, limits

TAP = HERE.parent / 'episode5-actor-private-read-tap-v2-20261121-v1/proposed-read-tap.v2.mjs'
TAP_SHA = 'cc191d0433def9fbcbb5b9b4e556ff7e92e6c46f366ab9151d4aef860fdbc8c1'
OWNER_SHA = 'cf74af705e98691eb2b66ca14d667598dc150dc6b77f9b9291ccd4e6ab32b57f'
CASE = 'p30-node4-face-bikkuri-only'
SCENE = 10450054

def merge_guards(target, source):
    """Reject inconsistent expectations instead of silently adopting drift."""
    for name, expected in source.items():
        path = str((ROOT / name).resolve())
        assert path not in target or target[path] == expected, path
        target[path] = expected

def required_saved_members(manifest):
    """Close actual ordinary resources, independently of the tested prefix.

    The complete API library and renderer resource sets have different owners.
    Preserve the established broad player/audio/image closure and all actual
    section1045 models. The canonical thumbnail route uses catalog members;
    completion/flow assets are normal dependencies even when this case stops
    before its chart. No loaded clip is chosen to force a baseline pose.
    """
    result = {'manifest.json', 'review/native-restoration.json', 'assets/catalog.json',
              'assets/package.json', 'assets/preview/catalog.json'}
    result.update(scene[key] for scene in manifest['scenes'] for key in ('path', 'reviewPath'))
    catalog = load(DATA / 'assets/catalog.json')
    models = set()
    for scene in manifest['scenes']:
        if scene['sectionId'] != 1045:
            continue
        result.add('assets/' + catalog['thumbnails']['scene'][str(scene['id'])])
        for row in load(DATA / scene['path'])['scenario_list']:
            if row['character']:
                models.add(row['character'].removeprefix('live2d/AC_'))
    patterns = ['assets/player/**/*', 'assets/preview/player/**/*',
                'assets/backgrounds/*', 'assets/preview/backgrounds/*',
                'assets/music/*', 'assets/preview/music/*',
                'assets/voices/**/*', 'assets/preview/voices/**/*',
                'assets/sounds/**/*', 'assets/preview/sounds/**/*',
                'assets/cutins/**/*', 'assets/preview/cutins/**/*',
                'assets/pictures/**/*', 'assets/preview/pictures/**/*',
                'assets/thumbnails/**/*', 'assets/preview/thumbnails/**/*',
                'assets/movies/adv_dive01_out.*', 'assets/preview/movies/adv_dive01_out.*']
    for model in models:
        patterns.extend([f'assets/models/{model}/**/*', f'assets/preview/models/{model}/**/*',
                         f'assets/portraits/{model}.*', f'assets/preview/portraits/{model}.*'])
    for pattern in patterns:
        result.update(str(path.relative_to(DATA)) for path in DATA.glob(pattern) if path.is_file())
    return result

parser = argparse.ArgumentParser()
parser.add_argument('--root-inputs', required=True)
parser.add_argument('--root-inputs-sha256', required=True)
args = parser.parse_args()
limits()
release_path = Path(args.root_inputs).resolve()
assert sha(release_path) == args.root_inputs_sha256
release = load(release_path)
for flag in ['rootConfirmed', 'freezeAuthorized', 'apiPreparationAuthorized', 'fullGlobalInventoryApproved']:
    assert release.get(flag) is True, flag
assert release['browserLaunchAuthorized'] is False
assert release['controlledNativeCandidateAuthorized'] is True
source_reviews = release['sourceReviewGuards']
assert len(source_reviews) == 2, 'Bind both completed source/actual review receipts'
assert release['browserOwner']
assert set(release['tools']) == {'firefox', 'xvfb', 'ffmpeg', 'node', 'python'}
assert Path(sys.executable).resolve() == Path(release['tools']['python']['binaryPath']).resolve()
assert sha(sys.executable) == release['tools']['python']['sha256']
for key in ['finalDataHead', 'finalSourceHead']:
    assert re.fullmatch('[a-f0-9]{40}', release[key] or ''), key
assert release['publicationGuards'], 'Final HEAD/ACK/source-status evidence must be separately root-bound'
global_ref = release['globalGuardsFile']
assert sha(global_ref['path']) == global_ref['sha256']
global_document = load(global_ref['path'])
guards = {}
merge_guards(guards, global_document.get('guards', global_document.get('globalGuards', {})))
assert guards
# Completeness is separate from matching listed digests. A pure-audit followup
# cannot vanish just because the previous listed files still match. Dist is
# the actual compiled program and all of its static modules, not only index.js.
for directory in [DATA / 'native', DATA / 'review', SOURCE / 'dist']:
    assert {str(path.resolve()) for path in directory.rglob('*') if path.is_file()} <= set(guards)
for relative in ['lib/preview.ts', 'lib/studio-api.ts', 'lib/studio-state.ts',
                 'public/player/player.js', 'public/player/native_tap_panel_close.js',
                 'public/studio/actor_animation.js', 'public/pairing/motion.js']:
    assert str(SOURCE / relative) in guards, relative
merge_guards(guards, release['publicationGuards'])
merge_guards(guards, source_reviews)
merge_guards(guards, release['kitGuards'])
protected = release['protectedFirstThree']
assert len(protected) == 22
for name, expected in protected.items():
    path = str((DATA / name).resolve())
    assert guards.get(path) == expected, path
assert sha(TAP) == TAP_SHA and sha(HERE / 'owner-events.mjs') == OWNER_SHA
for path, expected in [(TAP, TAP_SHA), (HERE / 'owner-events.mjs', OWNER_SHA)]:
    assert release['kitGuards'].get(str(path)) == expected, str(path)
for name in ['common.py', 'freeze.py', 'prepare.mjs', 'transport.mjs', 'server.mjs',
             'workers-private.mjs', 'node-guards.mjs', 'owner-events.mjs', 'curve-audit.mjs',
             'driver.mjs', 'run.py', 'README.md', 'plan.rootfalse.json', 'static-report.rootfalse.json']:
    assert release['kitGuards'].get(str(HERE / name)) == sha(HERE / name), name
for relative in ['artifacts/stella-local-deployment-3394828/d1-local.mjs',
                 'artifacts/stella-p30-firefox-20261120/bidi.mjs',
                 'artifacts/stella-p30-firefox-20261120/render-probe.mjs']:
    assert str(ROOT / relative) in release['kitGuards'], relative
guards[str(release_path)] = sha(release_path)
guards[global_ref['path']] = global_ref['sha256']
proposal = load(HERE / 'plan.rootfalse.json')
assert proposal['rootConfirmed'] is False and proposal['executionAuthorized'] is False
assert proposal['observedSnapshot']['finalDataHead'] is None
assert proposal['observedSnapshot']['finalSourceHead'] is None
assert proposal['controlledCandidatePreview'] is True
assert proposal['candidateNativeEdits'] == [{'path': '/scenario_list/3/motion', 'before': '', 'after': ',face_bikkuri'}]
for path, expected in proposal['evidenceReferences'].items():
    assert sha(path) == expected, path
    guards[path] = expected
manifest = load(DATA / 'manifest.json')
data_guards = {name: sha(DATA / name) for name in sorted(required_saved_members(manifest))}
merge_guards(guards, {str(DATA / name): expected for name, expected in data_guards.items()})
for tool in release['tools'].values():
    assert sha(tool['binaryPath']) == tool['sha256']
    report = subprocess.check_output(['file', tool['binaryPath']], text=True)
    assert 'ARM aarch64' in report, report
    tool['fileOutput'] = report
    guards[tool['binaryPath']] = tool['sha256']
    guards[tool['launchPath']] = sha(tool['launchPath'])
checked_guards(guards)
caps = {'caseWallSeconds': 120, 'totalWallSeconds': 1000, 'videoFramesPerCase': 3600,
        'videoBytesPerCase': 18000000, 'tapRowsPerCase': 12000, 'ownerEventRowsPerCase': 512,
        'consoleRowsPerCase': 6000, 'consoleBytesPerCase': 4000000, 'tapRawBytesPerCase': 160000000,
        'tapGzipBytesPerCase': 32000000, 'checkpointReadsPerCase': 8, 'httpRowsPerCase': 4000,
        'providerRowsTotal': 20000, 'providerBytesTotal': 12000000}
for key, cap in caps.items():
    assert type(release['budgets'][key]) is int and 0 < release['budgets'][key] <= cap, key
assert release['budgets']['screenshotsPerCase'] == 0
assert release['budgets']['checkpointReadsPerCase'] == 8
native_path, review_path = DATA / f'native/scenes/{SCENE}.json', DATA / f'review/scenes/{SCENE}.json'
assert sha(native_path) == proposal['observedSnapshot']['native']['sha256']
assert sha(review_path) == proposal['observedSnapshot']['review']['sha256']
native, review = load(native_path), load(review_path)
assert len(native['scenario_list']) == 52
rows = {row['scenario_id']: row for row in native['scenario_list']}
assert [step['scenario'] for step in proposal['steps']] == [3, 4, 5]
# Isolate the native input before invoking the unchanged canonical parser.
# Leading comma is deliberate: the body CSV slot is empty, face is requested,
# and no extra slot/talk/command/weight or physical parameter is supplied.
assert native_path.read_text() == __import__('json').dumps(native, ensure_ascii=False, indent=2) + '\n'
assert native['scenario_list'][3]['scenario_id'] == 4
assert native['scenario_list'][3]['uniq_id'] == 1045005400004
assert native['scenario_list'][3]['motion'] == ''
catalog = load(DATA / 'assets/catalog.json')
face_rows = [item for item in catalog['models']['live2d/AC_subaru_tshirt01']['motions']
             if item['token'] == 'face_bikkuri']
assert len(face_rows) == 1 and face_rows[0]['kind'] == 'face'
resource = proposal['requestedFaceResource']
assert resource['token'] == 'face_bikkuri'
assert resource['path'] == 'assets/' + face_rows[0]['url']
assert data_guards[resource['path']] == resource['sha256']
staged = deepcopy(native)
staged['scenario_list'][3]['motion'] = ',face_bikkuri'
expected_diff = [{'path': '/scenario_list/3/motion', 'before': '', 'after': ',face_bikkuri'}]
assert field_differences(native, staged) == expected_diff
restored = deepcopy(staged)
restored['scenario_list'][3]['motion'] = ''
assert restored == native
overlay_path = HERE / 'frozen' / CASE / '10450054.json'
base_guard_digest = digest(guards)
write(overlay_path, staged)
alias = digest({'case': CASE, 'dataHead': release['finalDataHead'],
                'sourceHead': release['finalSourceHead'], 'globalInputs': base_guard_digest,
                'overlayNative': sha(overlay_path)})[:40]
assert alias != release['finalDataHead']
guards[str(overlay_path)] = sha(overlay_path)
steps = []
for spec in proposal['steps']:
    scenario = spec['scenario']
    row = rows[scenario]
    assert row == spec['native'], scenario
    uid = str(review['scenarios'][str(scenario)].get('studioNodeId') or row['uniq_id'])
    node_id = f'node:{SCENE}:{uid}'
    assert node_id == spec['id']
    candidate_motion = ',face_bikkuri' if scenario == 4 else row['motion']
    assert candidate_motion == spec['candidateMotion']
    slots = candidate_motion.split(',')
    motion = {'body': slots[0], 'face': slots[1] if len(slots) > 1 else '', 'extras': slots[2:]}
    assert motion == spec['derivedMotion']
    steps.append({'scenario': scenario, 'id': node_id, 'native': row, 'kind': spec['expectedKind'],
                  'sourceText': spec['sourceText'], 'expectedModel': spec['expectedModel'],
                  'candidateMotion': candidate_motion, 'parsedMotion': motion, 'target': scenario == 4,
                  'expectedSuppressLipMotion': row['talk_chara'] == '0'})
assert rows[4]['character'] == 'live2d/AC_subaru_tshirt01' and rows[4]['motion'] == ''
assert rows[5]['character'] == 'live2d/AC_felt01' and rows[5]['motion'] == 'act_punpun'
links = []
for a, b, branch_id in zip(steps, steps[1:], [31, 41]):
    branch = next(row for row in a['native']['branch_list'] if row['branch_id'] == branch_id)
    transition = branch['transition_list']
    assert len(transition) == 1 and transition[0]['next_scenario_id'] == b['scenario']
    links.append({'source': a['id'], 'target': b['id'],
                  'id': f"edge:{a['id']}:{branch['uniq_id']}:{branch_id}",
                  'branchId': branch_id, 'native_transition': transition[0]})
for actual, spec in zip(links, proposal['links']):
    assert actual['id'] == spec['id'] and actual['native_transition'] == spec['native']
forbidden = next(row for row in rows[5]['branch_list'] if row['branch_id'] == 51)
assert len(forbidden['transition_list']) == 1 and forbidden['transition_list'][0]['next_scenario_id'] == 6
plan = {'schema': 'stella.p30.face-native-candidate-case.v1', 'rootConfirmed': False, 'id': CASE,
        'candidateOnly': True, 'alias': alias, 'aliasIsGitCommit': False,
        'overlay': {'path': str(overlay_path), 'sha256': sha(overlay_path)},
        'formalNative': {'path': str(native_path), 'sha256': sha(native_path)},
        'expectedSemanticDiff': expected_diff,
        'steps': steps, 'links': links, 'target': 4, 'start': steps[0]['id'], 'choices': {},
        'stop': {'node': steps[-1]['id'], 'scenario': 5, 'phase': 'ready',
                 'forbiddenNext': 6, 'forbiddenEdge': f"edge:{steps[-1]['id']}:{forbidden['uniq_id']}:51"},
        'ordinaryBaseline': False, 'controlledNativeCandidate': True, 'noProgramMutation': True,
        'observation': {'narrationNormalSeconds': 1, 'targetVisibleActorSeconds': 8,
                        'targetReadyActorSeconds': 2, 'maximumActorHoldChecks': 5},
        'motionAccepted': False, 'sourcePhaseAccepted': False}
write(HERE / 'frozen' / 'plan.json', plan)
guards[str(HERE / 'frozen' / 'plan.json')] = sha(HERE / 'frozen' / 'plan.json')
binding = {'schema': 'stella.p30.face-native-candidate-frozen-inputs.v1', 'rootConfirmed': False,
           'dataRoot': str(DATA), 'sourceRoot': str(SOURCE), 'finalDataHead': release['finalDataHead'],
           'finalSourceHead': release['finalSourceHead'], 'browserOwner': release['browserOwner'],
           'fileGuards': guards, 'dataGuards': data_guards, 'plans': [plan], 'tools': release['tools'],
           'budgets': release['budgets'], 'tap': {'path': str(TAP), 'sha256': TAP_SHA},
           'allLibraryNodes': sum(len(load(DATA / scene['path'])['scenario_list']) for scene in manifest['scenes']),
           'allLibraryEdges': sum(len(row['branch_list']) for scene in manifest['scenes']
                                  for row in load(DATA / scene['path'])['scenario_list']),
           'preparationRelease': {'path': str(release_path), 'sha256': sha(release_path)},
           'protectedFirstThree': protected, 'noProgramMutation': True, 'nativeOnlyOverlay': True,
           'controlledNativeCandidate': True, 'sourceReviewGuards': source_reviews,
           'browserOrServerStarted': False}
write(HERE / 'frozen' / 'binding.json', binding)
print(__import__('json').dumps({'status': 'frozen-face-native-candidate-not-executed', 'cases': 1,
                              'bindingSha256': sha(HERE / 'frozen' / 'binding.json')}))
