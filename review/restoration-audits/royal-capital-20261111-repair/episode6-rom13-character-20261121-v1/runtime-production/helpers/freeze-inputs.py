"""Bind a future published ordinary save; never repair or seed its content.

The caller supplies a fresh root-confirmed preparation release after the normal
repair/install/publication gates pass. The current failed stage and an approved
character packet alone are deliberately insufficient. This script only reads
repositories, hashes resources and writes new private artifact files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = HERE.parent / 'data-checkout'
SOURCE = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'

def load(path):
    return json.loads(Path(path).read_text())

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()

def write(name, value):
    with (HERE / name).open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

parser = argparse.ArgumentParser()
parser.add_argument('--root-inputs', required=True)
parser.add_argument('--root-inputs-sha256', required=True)
args = parser.parse_args()
release_path = Path(args.root_inputs).resolve()
assert sha(release_path) == args.root_inputs_sha256
release = load(release_path)
assert release['rootConfirmed'] is True and release['preparationAuthorized'] is True
assert release['browserLaunchAuthorized'] is False
assert re.fullmatch('[0-9a-f]{40}', release['publishedRomHead'] or '')
assert git(DATA, 'rev-parse', 'HEAD') == release['publishedRomHead']
assert git(DATA, 'status', '--short') == '', 'Only a committed/pushed saved revision may be bound'
assert git(SOURCE, 'rev-parse', 'HEAD') == release['sourceHead']
assert git(SOURCE, 'status', '--short') == release['sourceStatus']
assert git(SOURCE, 'diff', '--name-only', 'HEAD') == ''
assert sha(SOURCE / 'dist/server/index.js') == release['expectedDistServerSha256']
for name, key in [('native', 'expectedNativeSha256'), ('review', 'expectedReviewSha256')]:
    assert sha(DATA / f'{name}/scenes/10020037.json') == release[key]
packet_ref = release['approvedPacket']
assert sha(packet_ref['path']) == packet_ref['sha256']
packet = load(packet_ref['path'])
assert packet['rootConfirmed'] is True and len(packet['changes']) == 1
change = packet['changes'][0]
assert change['rootConfirmed'] is True
assert (change['sceneId'], change['scenarioId'], change['fields']) == (10020037, 13, {'character': 'live2d/AC_rom01'})
assert release['postapplyAndPublicationGuards'], 'A failed stage receipt is not postapply/publication proof'
guards = {str(release_path): sha(release_path), packet_ref['path']: packet_ref['sha256']}
guards.update(release['postapplyAndPublicationGuards'])
guards.update(release['additionalEvidenceGuards'])
for ref in change.get('evidence', {}).values():
    if isinstance(ref, dict) and 'path' in ref and 'sha256' in ref:
        guards[ref['path']] = ref['sha256']
for path, expected in guards.items():
    assert sha(ROOT / path) == expected, path

native = load(DATA / 'native/scenes/10020037.json')
review = load(DATA / 'review/scenes/10020037.json')
rows = {row['scenario_id']: row for row in native['scenario_list']}
assert len(rows) == len(native['scenario_list']) == 19
assert rows[13]['character'] == 'live2d/AC_rom01'
assert all(rows[13][key] == value for key, value in change['expected'].items() if key != 'character')
assert next(b for b in rows[13]['branch_list'] if b['branch_id'] == 133)['transition_list'] == []
steps = []
for scenario, model, branch in [(11, 'rom01', 111), (12, 'subaru01', 121), (13, 'rom01', 132), (14, 'rom01', 141)]:
    row = rows[scenario]
    assert row['character'] == 'live2d/AC_' + model
    uid = review['scenarios'][str(scenario)].get('studioNodeId') or row['uniq_id']
    edge = next(b for b in row['branch_list'] if b['branch_id'] == branch)
    assert len(edge['transition_list']) == 1
    transition = edge['transition_list'][0]
    assert transition['next_scenario_id'] == scenario + 1
    steps.append({'id': f'node:10020037:{uid}', 'scenario': scenario, 'native': row,
                  'expectedModel': model, 'expectedTransition': transition, 'branchId': branch})
assert steps[0]['id'] == 'node:10020037:1002003700011'
manifest = load(DATA / 'manifest.json')
paths = {'manifest.json', 'review/native-restoration.json', 'assets/catalog.json'}
paths.update(s[key] for s in manifest['scenes'] for key in ('path', 'reviewPath'))
# Bind every available member for both actors, including compressed textures,
# controllers, portraits and all motion files. Choosing a preview URL remains
# the normal Worker's job; the adapter may not substitute another model.
for pattern in ['assets/models/rom01/**/*', 'assets/models/subaru01/**/*',
                'assets/preview/models/rom01/**/*', 'assets/preview/models/subaru01/**/*',
                'assets/player/**/*', 'assets/portraits/rom01.*', 'assets/portraits/subaru01.*',
                'assets/preview/portraits/rom01.*', 'assets/preview/portraits/subaru01.*',
                'assets/backgrounds/*', 'assets/preview/backgrounds/*',
                'assets/music/*', 'assets/preview/music/*']:
    paths.update(str(p.relative_to(DATA)) for p in DATA.glob(pattern) if p.is_file())
prior = load(HERE.parent / 'p42-six-visual-saved-runtime-v1/input-binding.json')
protected = prior['protectedFirstThree']
assert {p: sha(DATA / p) for p in protected} == protected
source_files = {p: sha(SOURCE / p) for p in sorted(git(SOURCE, 'ls-files').splitlines()) if (SOURCE / p).is_file()}
dist_files = {str(p.relative_to(SOURCE / 'dist')): sha(p) for p in sorted((SOURCE / 'dist').rglob('*')) if p.is_file()}
plan = {'schema': 'stella.rom13.saved-plan.v1', 'rootConfirmed': False, 'sceneId': 10020037,
        'start': steps[0]['id'], 'steps': steps, 'sceneRows': 19,
        'allLibraryNodes': sum(len(load(DATA / s['path'])['scenario_list']) for s in manifest['scenes']),
        'recordedChoice': {'scenario': 13, 'branchId': 132, 'label': '零食？'},
        'unknownBranch': {'scenario': 13, 'branchId': 133},
        'stop': {'scenario': 14, 'phase': 'ready', 'forbiddenBranch': 141, 'forbiddenScenario': 15},
        'captureFormat': {'type': 'image/jpeg', 'quality': 0.9, 'viewport': {'width': 440, 'height': 900},
                          'count': 4, 'maximumCaptureBytes': 1000000},
        'acceptanceScope': 'Four saved actor identities and ordinary111/121/132 route only. No motion, face, extra layers, timing, FX, audio, unknown133,141,15, full glyphs, whole scene/episode/goal or production equivalence acceptance.'}
write('capture-plan.json', plan)
binding = {'schema': 'stella.rom13.saved-inputs.v1', 'rootConfirmed': False,
           'dataRoot': str(DATA), 'sourceRoot': str(SOURCE), 'dataHead': release['publishedRomHead'],
           'dataStatus': '', 'revision': release['publishedRomHead'], 'revisionMeaning': 'Published real Git commit',
           'dataInputs': {p: sha(DATA / p) for p in sorted(paths)}, 'protectedFirstThree': protected,
           'resourceAndSourceGuards': guards, 'browserOwner': release['browserOwner'],
           'source': {'head': release['sourceHead'], 'status': release['sourceStatus'],
                      'sourceFiles': source_files, 'distFiles': dist_files},
           'planSha256': sha(HERE / 'capture-plan.json'), 'browserOrServerStarted': False}
write('input-binding.json', binding)
print(json.dumps({'status': 'frozen-not-executed', 'dataHead': binding['dataHead'],
                  'sourceHead': release['sourceHead'], 'nodes': 4, 'dataInputs': len(paths)}))
