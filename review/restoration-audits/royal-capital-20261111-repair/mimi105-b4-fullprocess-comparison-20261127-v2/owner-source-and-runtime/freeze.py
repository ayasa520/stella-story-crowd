"""Future root-released full-scene private overlays; never a formal writer.

This source is not executed during preparation. It cannot approve its inputs,
call a Worker, start a browser, or convert a candidate into an accepted field.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import re
from common import HERE, DATA, SOURCE, digest, differences, inventory_view, limits, load, sha, verify, write

parser = argparse.ArgumentParser()
parser.add_argument('--release', required=True)
parser.add_argument('--release-sha256', required=True)
args = parser.parse_args()
limits()
release_path = Path(args.release).resolve()
release = load(release_path, args.release_sha256)
for flag in ('rootConfirmed', 'freezeAuthorized', 'apiPreparationAuthorized',
             'controlledNativeCandidateAuthorized', 'fullInventoryApproved', 'candidateSourcePeerAccepted'):
    assert release.get(flag) is True, flag
assert release['browserLaunchAuthorized'] is False
assert release['browserOwner'] == '/root/ui_browser_owner'
for key in ('finalDataHead', 'finalSourceHead'):
    assert re.fullmatch('[a-f0-9]{40}', release[key] or ''), key
assert release['publicationGuards']
for name in ('common.py','context.mjs','freeze.py','prepare.mjs','transport.mjs','server.mjs',
             'workers-private.mjs','curve-audit.mjs','driver.mjs','run.py','plan.rootfalse.json','README.md'):
    assert release['kitGuards'].get(str(HERE/name)) == sha(HERE/name), name
peer = release['candidatePeer']
assert peer['sha256'] == '79bf242239cf8dc2ab13db092717aace609f1fe3d25b6647654cddae57eb1dbc'
assert sha(peer['path']) == peer['sha256']
caps = {'caseWallSeconds':120,'totalWallSeconds':1000,'videoFramesPerCase':3600,
        'videoBytesPerCase':18000000,'tapRowsPerCase':12000,'ownerEventRowsPerCase':512,
        'consoleRowsPerCase':6000,'consoleBytesPerCase':4000000,'tapRawBytesPerCase':160000000,
        'tapGzipBytesPerCase':32000000,'checkpointReadsPerCase':8,'httpRowsPerCase':4000,
        'providerRowsTotal':20000,'providerBytesTotal':12000000,'nodeHeapMiB':512,
        'maximumOwnedRssBytes':3221225472,'maximumOutputBytes':268435456}
for key, cap in caps.items():
    assert isinstance(release['budgets'][key],int) and 0 < release['budgets'][key] <= cap, key
# This separate resource policy changes the conservative summed-RSS ceiling
# only. Enforce the root-bound 512 MiB-or-higher system MemAvailable floor here
# and again in run.py; missing, zero and weaker values cannot authorize B4.
assert isinstance(release['budgets']['minimumAvailableMemoryBytes'], int)
assert release['budgets']['minimumAvailableMemoryBytes'] >= 536870912
assert release['budgets']['screenshotsPerCase'] == release['budgets']['audioCaptures'] == 0
packet_ref = release['candidateInputs']
assert packet_ref['sha256'] == '50c5f2275b4df75fb3a10c061381f07a0f4daeaf499a403bba9216f8ff5c0b34'
packet = load(packet_ref['path'], packet_ref['sha256'], packet_ref.get('bytes'))
assert packet['rootConfirmed'] is False and packet['installationAuthorized'] is False
assert packet['sceneId'] == 10040043 and packet['targetScenarioId'] == 105
assert packet['targetArrayIndex'] == 104 and packet['targetUID'] == 1004004300105
expected_cases = [
    ('mimi105-B1F0', 'act_banzai_w', ''),
    ('mimi105-B1F1', 'act_banzai_w', 'face_egao'),
    ('mimi105-B2F0', 'act_egao', ''),
    ('mimi105-B2F1', 'act_egao', 'face_egao'),
]
assert [case['variant'] for case in packet['variants']] == [row[0] for row in expected_cases]
binding = {key: release[key] for key in ('finalDataHead', 'finalSourceHead', 'browserOwner',
           'inventory', 'ownerCore', 'tools', 'budgets', 'kitGuards')}
binding['sourceGuards'] = {**release['publicationGuards'], **release['sourceGuards'],
                         str(release_path): args.release_sha256,
                         packet_ref['path']: packet_ref['sha256'],peer['path']:peer['sha256']}
for tool in binding['tools'].values():
    assert Path(tool['launchPath']).resolve() == Path(tool['binaryPath']).resolve()
    assert sha(tool['binaryPath']) == tool['sha256']
    binding['sourceGuards'][tool['binaryPath']] = tool['sha256']
    binding['sourceGuards'][tool['launchPath']] = sha(tool['launchPath'])
assert not (HERE / 'frozen').exists(), 'Never reuse a prior freeze'
(HERE / 'frozen').mkdir()
write(HERE / 'frozen' / 'inputs-before.json', verify(binding, HERE / 'frozen'))
inventory = inventory_view(binding)
native_path, review_path = 'native/scenes/10040043.json', 'review/scenes/10040043.json'
native = load(DATA / native_path, inventory['dataInputs'][native_path])
review = load(DATA / review_path, inventory['dataInputs'][review_path])
manifest = load(DATA / 'manifest.json', inventory['dataInputs']['manifest.json'])
semantics = load(SOURCE / 'config/semantics.json', inventory['sourceFiles']['config/semantics.json'])
# These are equality checks against the original, independently reviewed
# controller/index definitions. Meta.Loop is deliberately not used to decide
# whether the one-shot entry states loop. No state is edited or normalized.
parameter_ref = packet['parameterEvidence']
parameter_path = HERE.parents[2] / parameter_ref['path']
parameters = load(parameter_path, parameter_ref['sha256'], parameter_ref['bytes'])
controller = load(DATA / 'assets/player/animation.json', inventory['dataInputs']['assets/player/animation.json'])
motion_index = load(DATA / 'assets/player/motion_states.json', inventory['dataInputs']['assets/player/motion_states.json'])
assert digest(controller['models']['mimi01']) == parameters['originalController']['modelDefinitionCanonicalSHA256']
assert digest(motion_index['models']['mimi01']) == parameters['normalMotionIndex']['modelCanonicalSHA256']
binding['sourceGuards'][str(parameter_path)] = parameter_ref['sha256']
for ref in [parameters['originalModel']['descriptor'],parameters['originalModel']['moc'],
            *parameters['originalModel']['textures'],*parameters['originalModel']['motionReferenceBindings']]:
    original = Path(ref['path'])
    marker = original.parts.index('ac_mimi01')
    relative = 'assets/models/mimi01/' + Path(*original.parts[marker+1:]).as_posix()
    assert inventory['dataInputs'][relative] == ref['sha256'], relative
assert native['scenario_list'][104]['scenario_id'] == 105
assert native['scenario_list'][104]['uniq_id'] == 1004004300105
assert native['scenario_list'][104]['character'] == 'live2d/AC_mimi01'
assert native['scenario_list'][104]['motion'] == ''
anchors = packet['sealedAnchorsForFreshMatchingOnly']
assert [row['scenarioId'] for row in anchors] == [104, 105, 106]
steps = []
for anchor in anchors:
    row = native['scenario_list'][anchor['arrayIndex']]
    sidecar = review['scenarios'][str(anchor['scenarioId'])]
    node = 'node:10040043:' + str(sidecar.get('studioNodeId') or row['uniq_id'])
    assert node == anchor['nodeId']
    assert row['scenario_id'] == anchor['scenarioId'] and row['uniq_id'] == anchor['UID']
    assert row['msg_text'] == anchor['ChineseGuard'] and sidecar['sourceText'] == anchor['sourceJapanese']
    assert row['command'] == anchor['sealedCommand'] and row['branch_list'] == anchor['sealedBranchList']
    assert row['character'] == 'live2d/AC_' + anchor['model']
    steps.append({'scenario': row['scenario_id'], 'id': node, 'native': row,
                  'expectedModel': anchor['model'], 'target': row['scenario_id'] == 105,
                  'kind': next(item['kind'] for item in semantics['scenario_types']
                               if item['value'] == row['scenario_type'])})
links = []
for before, after in zip(steps, steps[1:]):
    branch = before['native']['branch_list'][0]
    assert len(before['native']['branch_list']) == len(branch['transition_list']) == 1
    transition = branch['transition_list'][0]
    assert transition['next_scenario_id'] == after['scenario'] and transition['next_scenario_label'] == ''
    links.append({'id': 'edge:' + before['id'] + ':' + str(branch['uniq_id']) + ':' + str(branch['branch_id']),
                  'source': before['id'], 'target': after['id'], 'native_transition': transition})
last_branch = steps[-1]['native']['branch_list'][0]
assert last_branch['branch_id'] == 1061 and last_branch['transition_list'][0]['next_scenario_id'] == 107
plans = []
for candidate, (name, body, face) in zip(packet['variants'], expected_cases):
    motion = ','.join([body, face]) if face else body
    assert candidate['targetNativeMotion'] == motion
    assert candidate['targetParsedMotion'] == {'body': body, 'face': face, 'extras': []}
    expected_diff = [{'path': '/scenario_list/104/motion', 'before': '', 'after': motion}]
    assert candidate['expectedSemanticDiff'] == expected_diff
    assert candidate['expectedNativeCheckChanges'] == [
        {'path': 'scenario_list[104].motion', 'scenarioId': 105, 'before': '', 'after': motion}]
    overlay = deepcopy(native)
    overlay['scenario_list'][104]['motion'] = motion
    assert differences(native, overlay) == expected_diff
    undo = deepcopy(overlay)
    undo['scenario_list'][104]['motion'] = ''
    assert undo == native, 'Complete independent undo equality is required'
    path = HERE / 'frozen' / name / '10040043.json'
    write(path, overlay)
    alias = digest({'case': name, 'formalHead': binding['finalDataHead'],
                    'sourceHead': binding['finalSourceHead'], 'inventory': binding['inventory'],
                    'overlay': sha(path)})[:40]
    assert alias != binding['finalDataHead']
    case_steps = deepcopy(steps)
    for step in case_steps:
        value = motion if step['target'] else step['native']['motion']
        slots = value.split(',')
        step.update(candidateMotion=value, parsedMotion={'body': slots[0],
                    'face': slots[1] if len(slots) > 1 else '', 'extras': slots[2:]},
                    expectedSuppressLipMotion=step['native']['talk_chara'] == '0')
    plan = {'id': name, 'alias': alias, 'aliasIsGitCommit': False, 'candidateOnly': True,
            'motionAccepted': False, 'bodyAccepted': False, 'faceAccepted': False,
            'overlay': {'path': str(path), 'sha256': sha(path)},
            'formalNative': {'path': str(DATA / native_path), 'sha256': inventory['dataInputs'][native_path]},
            'expectedSemanticDiff': expected_diff,
            'expectedNativeCheckChanges': [{'path': 'scenario_list[104].motion', 'scenarioId': 105,
                                            'before': '', 'after': motion}],
            'steps': case_steps, 'links': links, 'target': 105, 'start': steps[0]['id'], 'choices': {},
            'stop': {'node': steps[-1]['id'], 'scenario': 106, 'phase': 'ready', 'forbiddenNext': 107,
                     'forbiddenEdge': 'edge:' + steps[-1]['id'] + ':' + str(last_branch['uniq_id']) + ':1061'},
            'expectedSettledTokens': {'motion': 'act_banzai_w' if body == 'act_banzai_w' else 'act_egao_w',
                                      'face': 'face_egao_w' if face else None},
            'observation': {'flankReadyActorSeconds': 1, 'settleProbeNormalSeconds': 2,
                            'settledActorSeconds': 4, 'maximumActorHoldChecks': 1}}
    write(HERE / 'frozen' / name / 'plan.json', plan)
    plans.append(plan)
    binding['sourceGuards'][str(path)] = sha(path)
    binding['sourceGuards'][str(path.parent / 'plan.json')] = sha(path.parent / 'plan.json')
counts = {'nodes': 0, 'edges': 0}
for scene in manifest['scenes']:
    document = load(DATA / scene['path'], inventory['dataInputs'][scene['path']])
    counts['nodes'] += len(document['scenario_list'])
    counts['edges'] += sum(len(row['branch_list']) for row in document['scenario_list'])
binding.update(schema='stella.mimi105.private-four-case-frozen.v1', rootConfirmed=False,
               nativeOnlyOverlay=True, controlledNativeCandidate=True, noProgramMutation=True,
               sceneRows=len(native['scenario_list']), plans=plans,
               allLibraryNodes=counts['nodes'], allLibraryEdges=counts['edges'],
               candidateInputs=packet_ref,
               preparationRelease={'path': str(release_path), 'sha256': args.release_sha256},
               shared=release['shared'])
binding['tap'] = binding['shared']['tap']
assert {'tap','ownerEvents','bidi','renderProbe','uiGuards','d1Shim'} <= set(binding['shared'])
for name, ref in binding['shared'].items():
    assert sha(ref['path']) == ref['sha256'], name
    binding['sourceGuards'][ref['path']] = ref['sha256']
write(HERE / 'frozen' / 'binding.json', binding)
write(HERE / 'frozen' / 'inputs-after.json', verify(binding, HERE / 'frozen'))
print(__import__('json').dumps({'frozenCases': 4, 'bindingSha256': sha(HERE / 'frozen' / 'binding.json'),
                              'browserStarted': False, 'apiCalled': False, 'formalDataWritten': False}))
