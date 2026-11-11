"""Check the missing hall asset and delegated boundary without viewing images."""

import hashlib
import json
from pathlib import Path
import sys
import zlib

ROOT = Path('/home/rikka/Projects/stella')
R = Path(__file__).parent
BASE = ROOT / 'story_crowd_data/assets'
STAGED = ROOT / 'artifacts/repair-20261112-p27-hall-background-availability-v1'
REVIEW = R / 'visual-high/agent-reviewed-p27-background-boundary-v1'
sys.path.insert(0, str(ROOT))
from story_studio.recovery.native_repair import InstalledSnapshot


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


draft_path = REVIEW / 'p27-hall-bg-picture-only-draft.json'
receipt_path = REVIEW / 'p27-hall-boundary-direct-review.json'
require(sha(draft_path) == '15b858216a95066edc922ca74f8ae055e56ea279db2e85d60c3a1769cbb2d776',
        'Background draft changed')
require(sha(receipt_path) == 'b2abec80d44c97f39fab6fe8b10143fa942a6250e48325be126f8273409b33bd',
        'Delegated review changed')
draft, review = read(draft_path), read(receipt_path)
require(len(draft['changes']) == 1 and review['directImageReview'] is True and
        review['reviewer'] == '/root/felt_entry_offline_review', 'Review scope differs')
row = draft['changes'][0]
snapshot = InstalledSnapshot(ROOT, ROOT / 'story_crowd_data')
native, source = snapshot.node(row['sceneId'], row['scenarioId'], row['stableKey'])
require((row['sceneId'], row['scenarioId']) == (10200006, 8) and
        source['sourceText'] == row['sourceText'] and native['bg_picture'] == '' and
        row['fields'] == {'bg_picture': 'bg/bg096b_roswaal'}, 'Current node guard differs')
require(review['decision']['backgroundIdentityAccepted'] is True and
        review['decision']['firstObservedProviderSupported'] is True and
        review['decision']['installableNow'] is False, 'Historical review decision differs')
videos = {}
for witness in review['sourceWitnesses']:
    require(sha(Path(witness['frame'])) == witness['frameSha256'], 'Source frame changed')
    videos[witness['video']] = witness['videoSha256']
for path, digest in videos.items():
    require(sha(Path(path)) == digest, 'Original recording changed')
plate = row['evidence']['originalPlate']
raw = Path(plate['original']['file']).read_bytes()
require(hashlib.sha256(raw).hexdigest() == plate['original']['sha256'] and
        len(raw) == plate['archiveEntry']['bytes'] and
        f'{zlib.crc32(raw):08x}' == plate['archiveEntry']['crc32'], 'Original plate identity differs')

# Availability has its own explicit resource selector. No root-confirmed story
# patch was fabricated to request this export; the reviewed field stays pending
# until these exact bytes are integrated and its guard is checked again.
old, new = read(BASE / 'catalog.json'), read(STAGED / 'catalog.json')
require(set(new['backgrounds']) == set(old['backgrounds']) | {'bg/bg096b_roswaal'} and
        len(old['backgrounds']) == 44 and len(new['backgrounds']) == 45, 'Background scope differs')
for key, value in old.items():
    if key in ('backgrounds', 'members', 'asset_members'):
        require(all(new[key].get(identity) == item for identity, item in value.items()),
                f'Existing resource row changed: {key}')
    else:
        require(new[key] == value, f'Unrelated resource section changed: {key}')
url = new['backgrounds']['bg/bg096b_roswaal']['url']
require((STAGED / url).read_bytes() == raw, 'Staged background is not the reviewed original bytes')
plan = read(STAGED / 'integration-plan.json')
require({item['path'] for item in plan['changes']} == {url, 'catalog.json', 'package.json'},
        'Staged path scope differs')
for item in plan['changes']:
    path = STAGED / item['path']
    require(sha(path) == item['sha256'] and path.stat().st_size == item['bytes'], 'Staged file changed')
    current = BASE / item['path']
    require((sha(current) if current.exists() else None) == item['expectedSha256'],
            'Current integration guard changed')
before, after = read(BASE / 'package.json')['files'], read(STAGED / 'package.json')['files']
require(set(after) == set(before) | {url}, 'Indexed payload addition differs')
for name, item in before.items():
    current = BASE / name
    require(sha(current) == item['sha256'] and current.stat().st_size == item['bytes'],
            f'Baseline payload differs: {name}')
    require(name == 'catalog.json' or after[name] == item, 'Unrelated index row changed')
snapshot.unchanged_on_disk()
output = R / 'p27-hall-staging-root-preflight-v1.json'
require(not output.exists(), 'Use a fresh receipt path')
result = dict(status='passed_availability_staging_boundary_metadata_not_installed',
              planSha256=sha(STAGED / 'integration-plan.json'), stagedFiles=3,
              baselinePayloadsVerified=len(before), newPayloads=1, backgroundsBefore=44,
              backgroundsAfter=45, plateSha256=hashlib.sha256(raw).hexdigest(),
              sourceFramesVerified=len(review['sourceWitnesses']), sourceVideosVerified=len(videos),
              pendingNode='10200006:8', fieldInstalled=False, formalWrites=0,
              browserOpened=False, mainThreadViewedImages=False, originalTimingAccepted=False)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
