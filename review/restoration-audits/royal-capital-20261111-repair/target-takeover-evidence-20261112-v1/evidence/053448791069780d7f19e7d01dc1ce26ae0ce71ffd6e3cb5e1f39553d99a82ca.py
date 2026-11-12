"""Rebind two bounded delegated P30 identity drafts without changing formal data.

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

ROOT = Path('/home/rikka/Projects/stella')
R = Path(__file__).parent
DATA = ROOT / 'story_crowd_data'
PACKETS = {
    'ord15to29': dict(folder='target-reviewed-p30-ord15to29-20261112-v1',
        draft='six-character-only-draft.json',
        sha256='8d6071b5c12c130c4e21f5a7849cb202a4f2691b2709bb51036a120368a8e2e4',
        targets={20: 'rom01', 21: 'felt01', 23: 'felt01', 31: 'felt01', 32: 'rom01', 33: 'felt01'}),
    'ord30to44': dict(folder='target-reviewed-p30-ord30to44-20261112-v1',
        draft='three-character-only-draft.json',
        sha256='aaf9eb2ebd819b15ca114ecdb76e9ea4194ff8d856ebf947e9271962c8cb8286',
        targets={41: 'felt01', 42: 'rom01', 43: 'felt01'}),
}


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
    assert sorted(review['directlyViewedOrdinals']) == (
        list(range(15, 30)) if args.packet == 'ord15to29' else list(range(30, 45)))
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
        assert row['sceneId'] == 10450054 and row['expected'] == {'character': ''}
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
        targets=[dict(sceneId=10450054, scenarioId=n, character=v) for n, v in expected.items()],
        referencesChecked=len(checked), formalWrites=0, mainThreadViewedImages=False,
        actingAccepted=False, fullPartIdentityAccepted=False, fullRestorationAccepted=False)
    write_new(receipt_path, receipt)
    print(json.dumps(dict(packet=str(accepted_path), receipt=str(receipt_path),
                         sha256=file_sha(accepted_path), targets=len(expected))))


if __name__ == '__main__':
    main()
