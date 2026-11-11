"""Resolve the reviewed background's availability prerequisite, without images.

The visual review predates packaging and remains immutable. This adapter only
binds the now-published exact original bytes and projects the plate reference
into the existing integration gate's flat id/file/sha256 schema. Root's later
acceptance must still verify the current node, Japanese text and field guard.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/home/rikka/Projects/stella')
R = Path(__file__).parent
DATA = ROOT / 'story_crowd_data'
source = R / 'visual-high/agent-reviewed-p27-background-boundary-v1/p27-hall-bg-picture-only-draft.json'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
assert digest == '15b858216a95066edc922ca74f8ae055e56ea279db2e85d60c3a1769cbb2d776'
assert subprocess.check_output(['git', '-C', str(DATA), 'rev-parse', 'HEAD'], text=True).strip() == \
       '971dd12667c161ff3e709c6551c4bd48654d12d7'
packet = deepcopy(json.loads(source.read_text()))
row = packet['changes'][0]
assert len(packet['changes']) == 1 and row['fields'] == {'bg_picture': 'bg/bg096b_roswaal'}
catalog_path = DATA / 'assets/catalog.json'
catalog = json.loads(catalog_path.read_text())
record = catalog['backgrounds'][row['fields']['bg_picture']]
payload = DATA / 'assets' / record['url']
original = row['evidence']['originalPlate']
raw = Path(original['original']['file']).read_bytes()
assert payload.read_bytes() == raw
assert hashlib.sha256(raw).hexdigest() == original['original']['sha256']

row['evidence']['originalPlateProvenance'] = original
row['evidence']['originalPlate'] = dict(id=original['resourceId'],
                                       file=original['original']['file'],
                                       sha256=original['original']['sha256'])
row['evidence']['rootAvailabilityResolution'] = dict(
    executedBy='/root', visualReviewChanged=False, mainThreadViewedImages=False,
    originalDraft=dict(file=str(source), sha256=digest),
    availabilityCommit='971dd12667c161ff3e709c6551c4bd48654d12d7',
    catalogSha256=hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
    packagedPayload=dict(file=str(payload), sha256=hashlib.sha256(raw).hexdigest()),
    exactOriginalBytesPublished=True,
    historicalInstallableNowFalsePreservedInOriginalReview=True,
)
packet['status'] = 'background_only_availability_resolved_root_field_guard_required'
packet['rootPreparation'] = dict(schemaProjectionOnly=True, noNewVisualDecision=True,
                                 resourcePrerequisiteResolved=True)
output = R / 'visual-high/p27-hall-background-availability-resolved-v1.json'
assert not output.exists()
output.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(output=str(output), sha256=hashlib.sha256(output.read_bytes()).hexdigest())))
