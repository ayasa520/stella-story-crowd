"""Independently audit an additive, still uninstalled model package.

This receipt checks availability and preservation only. Resource identity in a
recording requires a separate assembled-image review; this audit cannot grant
character, motion, expression, geometry or playback acceptance.
"""

import hashlib
import json
from pathlib import Path


ROOT = Path('/home/rikka/Projects/stella')
BASE = ROOT / 'story_crowd_data/assets'
STAGED = ROOT / 'artifacts/repair-20261112-reinhard-reference-availability-v1'
R = Path(__file__).parent


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


plan = read(STAGED / 'integration-plan.json')
old, new = read(BASE / 'catalog.json'), read(STAGED / 'catalog.json')
before, after = read(BASE / 'package.json')['files'], read(STAGED / 'package.json')['files']
require(plan['target'] == str(BASE), 'Unexpected integration target')
require(set(new['models']) == set(old['models']) | {'live2d/AC_reinhard01'},
        'Model addition scope differs')
require(len(old['models']) == 41 and len(new['models']) == 42, 'Model counts differ')
for key, value in old.items():
    if key in ('models', 'members', 'asset_members'):
        require(all(new[key].get(identity) == row for identity, row in value.items()),
                f'Existing catalog records changed: {key}')
    else:
        require(new[key] == value, f'Unrelated catalog section changed: {key}')
for name, digest in plan['sourceMetadataLocks'].items():
    require(sha(BASE / name) == digest, f'Current asset metadata changed: {name}')
require(sha(ROOT / 'data/story_studio/project.json') == plan['sourceProjectSha256'],
        'Studio changed')

changes = {row['path']: row for row in plan['changes']}
require(len(changes) == len(plan['changes']) == 48, 'Duplicate or unexpected staged paths')
for name, row in changes.items():
    staged = STAGED / name
    require(staged.resolve().is_relative_to(STAGED.resolve()), 'Unsafe staged relative path')
    require(str(staged) == row['source'] and staged.stat().st_size == row['bytes'] and
            sha(staged) == row['sha256'], f'Staged file differs: {name}')
    require((sha(BASE / name) if (BASE / name).is_file() else None) == row['expectedSha256'],
            f'Integration precondition differs: {name}')

# Re-read every baseline payload instead of trusting the previous package index.
# Only four aggregate index records may differ; package.json is guarded by the
# integration plan rather than recursively recording its own digest.
metadata = {'catalog.json', 'player/manifest.json', 'player/animation.json',
            'player/motion_states.json'}
require(set(before) <= set(after) and len(after) - len(before) == 43,
        'Existing payload was removed or addition count differs')
changed_old, originals = [], []
for name, row in before.items():
    path = BASE / name
    require(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'],
            f'Baseline payload/index mismatch: {name}')
    if after[name] != row:
        require(name in metadata, f'Existing payload record changed: {name}')
        changed_old.append(name)
for name in sorted(set(after) - set(before)):
    row = after[name]
    path = STAGED / name
    require(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'],
            f'New indexed payload differs: {name}')
    if row.get('source') and row.get('source_sha256'):
        source = Path(row['source'])
        source = source if source.is_absolute() else ROOT / source
        require(sha(source) == row['source_sha256'], f'Original source changed: {name}')
        originals.append(name)
for filename, key in [('manifest.json', 'actors'), ('animation.json', 'models'),
                      ('motion_states.json', 'models')]:
    prior, staged = read(BASE / 'player' / filename), read(STAGED / 'player' / filename)
    require(set(staged[key]) == set(prior[key]) | {'reinhard01'},
            f'Player inventory scope differs: {filename}')
    require(all(staged[key][identity] == row for identity, row in prior[key].items()),
            f'Existing player model record changed: {filename}')
    require({k: v for k, v in staged.items() if k != key} ==
            {k: v for k, v in prior.items() if k != key},
            f'Player non-model metadata changed: {filename}')

output = R / 'reinhard-staging-root-preflight-v1.json'
require(not output.exists(), 'Use a fresh receipt path')
receipt = dict(status='passed_staging_availability_only_not_integrated',
               staging=str(STAGED), integrationPlanSha256=sha(STAGED / 'integration-plan.json'),
               baselinePayloadsVerified=len(before), newPayloadsVerified=len(after) - len(before),
               stagedFilesVerified=len(changes), newOriginalSourceReceiptsVerified=len(originals),
               changedExistingIndexRecords=sorted(changed_old), modelsBefore=41, modelsAfter=42,
               productionWrites=0, browserOpened=False, mainThreadViewedImages=False,
               storyIdentityAccepted=False, motionAccepted=False, geometryAccepted=False,
               nativeEmbeddedMocEquivalenceCoveredByThisAudit=False)
output.write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
