"""Rebind the independently viewed P30 ord60--74 character-only draft.

The reviewer owns image interpretation. Root accepts only the enumerated model
identities after byte/reference checks and fresh installed-node preconditions.
The original draft stays rootConfirmed:false; the accepted derivative and its
binding receipt preserve the exact independent packet and review receipt hashes.
No action/face/geometry/timing or whole-part claim is introduced here.
"""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from story_studio.recovery.native_repair import InstalledSnapshot
from target_identity_publication_v1 import references, file_sha, write_new
from target_verified_utf8_v1 import decode_verified

ROOT = Path('/home/rikka/Projects/stella')
R = Path(__file__).parent
DATA = ROOT / 'story_crowd_data'
PACKETS = {
    'ord60to74': dict(folder='target-reviewed-p30-ord60to74-20261112-v1',
        draft='five-character-only-draft.json',
        sha256='a67747335b674003b20188da8bab27cfc51adff7ac24565524e94dafa24173a8',
        startOrdinal=60, sceneId=10450055,
        targets={16: 'felt01', 17: 'felt01', 18: 'rom01', 19: 'felt01', 20: 'rom01'}),
}

# Keep the original binder immutable: earlier accepted packets bind its exact
# source hash. This separate CLI installs only a process-local JSON ingress
# strategy, covering InstalledSnapshot's byte inputs as well as this binder's
# metadata. Verified UTF-8 roundtrip precedes one unchanged JSON parse; no data
# file or installed Python configuration is rewritten.
_standard_loads = json.loads


def verified_loads(value, *args, **kwargs):
    if isinstance(value, (bytes, bytearray)):
        value = decode_verified(bytes(value), 'P30 ord60--74 root binding')
    return _standard_loads(value, *args, **kwargs)


json.loads = verified_loads


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', choices=PACKETS, required=True)
    args = parser.parse_args()
    spec = PACKETS[args.packet]
    draft_path = R / 'visual-high' / spec['folder'] / spec['draft']
    assert file_sha(draft_path) == spec['sha256']
    draft = json.loads(draft_path.read_bytes())
    assert draft['rootConfirmed'] is False and draft['fieldGroups'] == ['character']
    review_path = Path(draft['reviewReceipt']['file'])
    assert file_sha(review_path) == draft['reviewReceipt']['sha256']
    review = json.loads(review_path.read_bytes())
    assert review['fullPartReviewed'] is False and review['fullPartIdentityAccepted'] is False
    assert review['actingAccepted'] is False and review['geometryAccepted'] is False
    assert sorted(review['directlyViewedOrdinals']) == list(range(spec['startOrdinal'], spec['startOrdinal'] + 15))
    checked = {}
    for path, digest in references(draft):
        path = path if path.is_absolute() else ROOT / path
        assert path not in checked or checked[path] == digest
        checked[path] = digest
    for path, digest in checked.items():
        assert file_sha(path) == digest, str(path)
    # Only existing exact Felt/Rom references are admitted. Compare the complete
    # current model rows to the prior independently signed target preflight,
    # rather than treating a speaker name or a partial resource row as identity.
    initial_preflight = R / 'target-p30-first15-preflight-20261112-v1/receipt.json'
    prior = json.loads(initial_preflight.read_bytes())
    assert prior['status'].startswith('passed_')
    assert file_sha(DATA / 'assets/catalog.json') == prior['currentCatalogSha256']
    snapshot = InstalledSnapshot(ROOT, DATA)
    expected = {node: 'live2d/AC_' + model for node, model in spec['targets'].items()}
    assert {row['scenarioId']: row['fields']['character'] for row in draft['changes']} == expected
    accepted = deepcopy(draft)
    accepted.update(status='delegated_image_review_accepted_for_guarded_install', rootConfirmed=True)
    integration = dict(reviewer='/root', mainThreadViewedImages=False,
        sourceDraft=dict(file=str(draft_path), sha256=file_sha(draft_path)),
        independentReview=deepcopy(draft['reviewReceipt']),
        currentResourcePreflight=dict(file=str(initial_preflight), sha256=file_sha(initial_preflight)),
        binder=dict(file=str(Path(__file__).resolve()), sha256=file_sha(Path(__file__))),
        acceptance='character_and_costume_only', motionAndExpressionAccepted=False)
    for row in accepted['changes']:
        assert row['sceneId'] == spec['sceneId'] and row['expected'] == {'character': ''}
        assert set(row['fields']) == {'character'}
        assert row['evidence']['directImageReview'] is True
        assert row['evidence']['motionAndExpressionVerified'] is False
        native, current_review = snapshot.node(row['sceneId'], row['scenarioId'], row['stableKey'])
        assert native['character'] == '' and current_review['sourceText'] == row['sourceText']
        row['rootConfirmed'] = True
        row['evidence']['rootIntegration'] = integration
    snapshot.unchanged_on_disk()
    accepted_path = R / 'visual-high' / f'accepted-p30-{args.packet}-identities-target-20261112-v1.json'
    receipt_path = R / f'target-p30-{args.packet}-root-binding-20261112-v1/receipt.json'
    assert not accepted_path.exists() and not receipt_path.exists()
    write_new(accepted_path, accepted)
    receipt = dict(status='passed_root_rebinding_of_independent_identity_review',
        packet=dict(file=str(accepted_path), sha256=file_sha(accepted_path)),
        originalDraft=integration['sourceDraft'], independentReview=integration['independentReview'],
        currentCatalogSha256=prior['currentCatalogSha256'],
        dataHead=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=DATA).decode().strip(),
        ownershipSha256=hashlib.sha256(snapshot.ownership_raw).hexdigest(),
        targets=[dict(sceneId=spec['sceneId'], scenarioId=n, character=v) for n, v in expected.items()],
        referencesChecked=len(checked), formalWrites=0, mainThreadViewedImages=False,
        actingAccepted=False, fullPartIdentityAccepted=False, fullRestorationAccepted=False)
    write_new(receipt_path, receipt)
    print(json.dumps(dict(packet=str(accepted_path), receipt=str(receipt_path),
                         sha256=file_sha(accepted_path), targets=len(expected))))


if __name__ == '__main__':
    main()
