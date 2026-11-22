"""Future root-authorized snapshot only; never execute this draft during design.

This P22 case requires a newly reviewed inventory and final published heads.
Library counts are independently derived from every saved native array, then
matched to both root-approved counts and inventory counts. An older P21 count
or release cannot authorize this four-node suffix.
No business restoration module is imported, no API is called and no D/C file is
written. Only a new private input-binding.json is emitted after all checks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
def load(path):
    return json.loads(Path(path).read_text())
def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()
def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
def verify(files):
    for name, expected in files.items():
        assert sha(name) == expected, name

def required_saved_members(data, manifest):
    """Derive the ordinary API and section resources without executing it.

    Whole-library native/review bodies are distinct from renderer resources.
    Include all current section models/providers plus player assets and music,
    so a correct listed hash cannot disguise an omitted dependency. A genuinely
    new API-before dependency still fails closed after its raw response is kept.
    """
    result = {'manifest.json', 'review/native-restoration.json', 'assets/catalog.json',
              'assets/package.json', 'assets/preview/catalog.json'}
    result.update(entry[key] for entry in manifest['scenes'] for key in ('path', 'reviewPath'))
    catalog = load(data / 'assets/catalog.json')
    models, backgrounds, pictures, movies = {'subaru01'}, {'bg/bg001_black'}, set(), set()
    for entry in manifest['scenes']:
        if entry['sectionId'] != 1003:
            continue
        # Completing this section opens the normal flowchart, which requests
        # each scene's /scene-thumbnail/<id> after the final script node. The
        # canonical endpoint resolves this catalog member beneath assets/;
        # these are actual dependencies of the same ordinary completion route.
        result.add('assets/' + catalog['thumbnails']['scene'][str(entry['id'])])
        for row in load(data / entry['path'])['scenario_list']:
            if row['character']:
                models.add(row['character'].removeprefix('live2d/AC_'))
            if row['bg_picture']:
                backgrounds.add(row['bg_picture'])
            if row['character_image']:
                pictures.add(row['character_image'])
            if row['video']:
                movies.add(row['video'])
    directories = ['assets/player', 'assets/music', 'assets/preview/music', 'review/restoration-batches']
    directories += [prefix + model for model in models for prefix in ('assets/models/', 'assets/preview/models/')]
    for name in directories:
        directory = data / name
        if directory.exists():
            result.update(str(p.relative_to(data)) for p in directory.rglob('*') if p.is_file())
    for name in ('assets/portraits', 'assets/preview/portraits'):
        for p in (data / name).glob('*'):
            if p.is_file() and any(p.name.startswith(model + '.') for model in models):
                result.add(str(p.relative_to(data)))
    for values, name in ((backgrounds, 'backgrounds'), (pictures, 'pictures'), (movies, 'movies')):
        for value in values:
            stem = value.replace('bg/', 'ADV_', 1) if name == 'backgrounds' else value
            for prefix in ('assets/', 'assets/preview/'):
                result.update(str(p.relative_to(data)) for p in (data / (prefix + name)).glob(stem + '.*') if p.is_file())
    return result

parser = argparse.ArgumentParser()
parser.add_argument('--root-inputs', required=True)
parser.add_argument('--root-inputs-sha256', required=True)
args = parser.parse_args()
release_path = Path(args.root_inputs).resolve()
assert sha(release_path) == args.root_inputs_sha256
release = load(release_path)
assert release['rootConfirmed'] is True and release['preparationAuthorized'] is True
assert release['browserLaunchAuthorized'] is False
assert release['freshSourceAfterPanelCloseApproved'] is True
assert re.fullmatch('[a-f0-9]{40}', release['publishedHead'] or '')
assert re.fullmatch('[a-f0-9]{40}', release['sourceHead'] or '')
inventory_ref = release['guardInventory']
assert sha(inventory_ref['path']) == inventory_ref['sha256']
inventory = load(inventory_ref['path'])
data, source = Path(inventory['dataRoot']), Path(inventory['sourceRoot'])
assert data.resolve() == (HERE.parent / 'data-checkout').resolve()
assert source.resolve() == (ROOT / 'artifacts/stella-site-repair-source/.sites-checkout').resolve()
assert git(data, 'rev-parse', 'HEAD') == release['publishedHead']
assert git(data, 'status', '--short') == ''
assert git(source, 'rev-parse', 'HEAD') == release['sourceHead']
assert git(source, 'status', '--short') == release['sourceStatus']
assert git(source, 'diff', '--name-only', 'HEAD') == ''
assert isinstance(release['browserOwner'], str) and release['browserOwner'].startswith('/root/')
# Counts are a fresh root input, never an inherited5622 or a guessed5624.
# Three independent representations must agree before a normal API is called.
approved_counts = release['libraryCounts']
assert set(approved_counts) == {'libraryScenes', 'libraryNodes', 'libraryEdges'}
assert all(type(value) is int and value > 0 for value in approved_counts.values())
assert {key: inventory['counts'][key] for key in approved_counts} == approved_counts
assert len(inventory['protectedFirstThree']) == 22
assert sha(HERE / 'capture-plan.json') == release['planSha256']
assert inventory['routeSource']['sha256'] == '1ab1479b757c15b9e97a58171bf0da512c9b7aa1fd8e4794da006a7d8063758f'
assert sha(inventory['routeSource']['path']) == inventory['routeSource']['sha256']
data_inputs = inventory['dataInputs']
for name, digest in data_inputs.items():
    assert sha(data / name) == digest, name
source_files, dist_files = inventory['sourceFiles'], inventory['distFiles']
assert set(source_files) == {p for p in git(source, 'ls-files').splitlines() if (source / p).is_file()}
assert set(dist_files) == {str(p.relative_to(source / 'dist')) for p in (source / 'dist').rglob('*') if p.is_file()}
for base, files in [(source, source_files), (source / 'dist', dist_files)]:
    for name, digest in files.items():
        assert sha(base / name) == digest, name
# Review/audit additions must not disappear just because an older inventory's
# listed hashes still match. Completeness is checked separately from content.
globals_ = inventory['globalGuards']
for directory in ['native', 'review']:
    assert {str(p.resolve()) for p in (data / directory).rglob('*') if p.is_file()} <= set(globals_)
verify(globals_)
protected = inventory['protectedFirstThree']
assert {name: sha(data / name) for name in protected} == protected
resource_guards = {**inventory['sharedClosure'], **inventory['evidenceGuards'],
                   str(release_path): sha(release_path), inventory_ref['path']: inventory_ref['sha256']}
shared_names = ['artifacts/stella-local-deployment-3394828/serve-local.mjs',
    'artifacts/stella-local-deployment-3394828/workers-local.mjs',
    'artifacts/stella-local-deployment-3394828/d1-local.mjs',
    'artifacts/stella-local-deployment-3394828/preview.sqlite',
    'artifacts/stella-p30-firefox-20261120/bidi.mjs',
    'artifacts/stella-p30-firefox-20261120/render-probe.mjs',
    'artifacts/stella-script-continuation-20261121/episode5-silent54-saved-runtime-v2/ending-observer.mjs',
    'artifacts/stella-script-continuation-20261121/episode5-silent54-saved-runtime-v2/capture-readiness.mjs']
assert {str(ROOT / name) for name in shared_names} <= set(inventory['sharedClosure'])
verify(resource_guards)
verify(inventory['toolFiles'])
verify(release['kitGuards'])
required_kit = ['run.py', 'play.mjs', 'guards.mjs', 'prepare-normal.mjs',
                'freeze-inputs.py', 'worktree-upstream.mjs', 'capture-plan.json',
                'README.md', 'CHANGE_BOUNDARIES.md', 'static-report.rootfalse.json']
assert {str((HERE / name).resolve()) for name in required_kit} <= set(release['kitGuards'])
plan = load(HERE / 'capture-plan.json')
for name, digest in plan['expectedSectionFiles'].items():
    assert sha(data / name) == digest, name
assert len(plan['cases']) == 1 and len(plan['cases'][0]['steps']) == 4
assert plan['cases'][0]['id'] == 'p22-ending23-to26'
assert plan['allLibraryNodes'] is None and plan['countsFromFreshBinding'] is True
manifest = load(data / 'manifest.json')
assert required_saved_members(data, manifest) <= set(data_inputs)
documents = {str(entry['id']): load(data / entry['path']) for entry in manifest['scenes']}
scene_counts = {scene: len(document['scenario_list']) for scene, document in documents.items()}
derived_counts = {'libraryScenes': len(manifest['scenes']),
    'libraryNodes': sum(scene_counts.values()),
    'libraryEdges': sum(len(row['branch_list']) for document in documents.values()
                        for row in document['scenario_list'])}
# The ordinary compiler emits one edge for every raw branch, including missing
# branches. Counting only reachable edges would silently slice this contract.
assert derived_counts == approved_counts
assert scene_counts['10030006'] == 26
for case in plan['cases']:
    for step in case['steps']:
        native = load(data / ('native/scenes/' + str(step['scene']) + '.json'))
        actual = next(row for row in native['scenario_list'] if row['scenario_id'] == step['scenario'])
        assert actual == step['native'], step['id']
assert all(c == '' for step in plan['cases'][0]['steps'] for c in step['native']['command'])
assert plan['closeCoverage']['expectedPositiveWitnesses'] == 0
assert plan['closeCoverage']['positiveEdges'] == []
binding = {'schema': 'stella.p22.ending-normal-qa.saved-inputs.v1', 'rootConfirmed': False,
    'libraryCounts': derived_counts, 'sceneCounts': scene_counts,
    'dataRoot': str(data), 'sourceRoot': str(source), 'dataHead': release['publishedHead'], 'dataStatus': '',
    'revision': release['publishedHead'], 'browserOwner': release['browserOwner'],
    'dataInputs': data_inputs, 'protectedFirstThree': protected,
    'protectedFirstThreeAbsolute': {str(data / p): digest for p, digest in protected.items()},
    'globalGuards': globals_, 'resourceAndSourceGuards': resource_guards,
    'toolFiles': inventory['toolFiles'], 'kitGuards': release['kitGuards'],
    'source': {'head': release['sourceHead'], 'status': release['sourceStatus'],
               'sourceFiles': source_files, 'distFiles': dist_files}}
with (HERE / 'input-binding.json').open('x') as handle:
    handle.write(json.dumps(binding, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': 'frozen-not-api-or-browser', 'head': binding['revision'],
                  'sourceHead': binding['source']['head'], 'dataInputs': len(data_inputs),
                  'globalGuards': len(globals_)}))
