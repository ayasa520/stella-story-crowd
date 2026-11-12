"""Archive the verified target checkpoint without changing story/runtime data.

Publication receipts necessarily follow their commits. This bounded evidence
package makes the completed eight-package ACK chain, independent full readback,
source-entry review and retained failure boundaries reviewable in the data repo.
Unreleased capture/adapter authoring is deliberately outside this checkpoint.
"""
import json
from pathlib import Path
import subprocess

from target_identity_publication_v1 import archive_files, file_sha, read, write_new

ROOT = Path('/home/rikka/Projects/stella')
R = Path(__file__).parent
DATA = ROOT / 'story_crowd_data'
NAME = 'target-takeover-evidence-20261112-v1'


def metadata(folder):
    return {p for p in folder.rglob('*') if p.is_file() and
            p.suffix in ('.json', '.py', '.cjs', '.md', '.log', '.txt', '.bin') and
            'node_modules' not in p.parts and 'npm-cache' not in p.parts}


def main():
    def git(*args):
        return subprocess.check_output(['git', '--no-optional-locks', *args], cwd=DATA)
    assert not git('status', '--porcelain')
    head = git('rev-parse', 'HEAD').decode().strip()
    audit = read(R / 'target-identity-cumulative-audit-20261112-v1.json')
    assert audit['head'] == head and len(audit['changedNativeFields']) == 45
    packages = [f'target-p29-batch{n}-publication-20261112-v1' for n in range(3, 8)] + [
        'target-p30-first15-publication-20261112-v1',
        'target-p30-ord15to29-publication-20261112-v1',
        'target-p30-ord30to44-publication-20261112-v3']
    receipts = [read(R / package / 'final-publication-receipt.json') for package in packages]
    assert all(row['status'] == 'published_remote_ack_verified' and row['head'] == row['remoteAck']
               for row in receipts)
    assert sum(row['newCharacterFields'] for row in receipts) == 45
    assert receipts[-1]['head'] == head
    selected = {Path(__file__), R / 'PROGRESS.md', R / 'audit_v20_publication.py'}
    selected.update(R.glob('target_*.py'))
    selected.update(R.glob('target_*.cjs'))
    selected.update(R.glob('target-*.json'))
    # Select only review/diagnostic artifacts, never an installed dependency tree,
    # a not-yet-reviewed execution kit, session credentials or unrelated work.
    for name in ['target-p29-preflight-20261112-v1',
                 'target-p30-first15-preflight-20261112-v1',
                 'target-p30-extra9-independent-preflight-20261112-v1',
                 'target-p29-batch5-independent-readback-20261112-v1',
                 'target-json-decode-independent-review-20261112-v1',
                 'target-json-audit-observations-v1', 'target-json-module-observations-v1',
                 'target-utf8-roundtrip-observations-v1',
                 'target-p30-ord15to29-root-binding-20261112-v1',
                 'target-p30-ord30to44-root-binding-20261112-v1']:
        selected.update(metadata(R / name))
    selected.update(metadata(R / 'visual-low/p30-felt5-target-independent-review-20261112-v1'))
    for name in ['target-reviewed-p30-ord15to29-20261112-v1',
                 'target-reviewed-p30-ord30to44-20261112-v1']:
        selected.update(metadata(R / 'visual-high' / name))
    for package in packages:
        for name in ['preconditions.json', 'committed-blobs.json', 'push.json',
                     'final-publication-receipt.json', 'readback.json']:
            selected.add(R / package / name)
    # Failed attempts are terminal pre-write observations, not alternative
    # successful installs. Preserve their complete command receipts and plans.
    for version in (1, 2):
        folder = R / f'target-p30-ord30to44-publication-20261112-v{version}'
        selected.update(folder.glob('*.json'))
        selected.update((folder / 'staging').glob('*.json'))
    tool = R / 'target-arm-tools-20261112-v1'
    for name in ['toolchain-receipt.json', 'package.json', 'package-lock.json', 'README.md']:
        if (tool / name).is_file():
            selected.add(tool / name)
    # The toolchain receipt's explicit file/digest references preserve pinned
    # metadata and command logs; tarballs/binaries stay local verified payloads.
    from target_identity_publication_v1 import references
    for path, digest in references(read(tool / 'toolchain-receipt.json')):
        path = path if path.is_absolute() else ROOT / path
        assert file_sha(path) == digest
        if 'node_modules' not in path.parts and path.suffix not in ('.tgz', '.gz'):
            selected.add(path)
    destination = DATA / 'review/restoration-audits/royal-capital-20261111-repair' / NAME
    work = R / NAME
    assert not destination.exists() and not work.exists()
    work.mkdir()
    copied, local = archive_files(destination, selected)
    report = dict(status='verified_evidence_only_checkpoint', baseCommit=head,
        explicitFields=audit['explicitFields'], characterFieldsPublished=45,
        publishedPackages=[dict(package=name, head=row['head'], remoteAck=row['remoteAck'])
                           for name, row in zip(packages, receipts)],
        nativeFieldsChangedByThisCheckpoint=0, protectedFiles=38,
        protectedStudioSha256=audit['studioSha256'], resourcesUnchanged=True,
        mainThreadViewedImages=False, browserStarted=False, newPlaybackVisits=0,
        motionFaceGeometryTimingOrWholePartAccepted=False, fullRestorationAccepted=False)
    write_new(destination / 'MANIFEST.json', dict(schema='stella.exact_evidence_archive.v1',
        **report, copiedFiles=copied, localOnlyEvidence=local))
    files = [str(p.relative_to(DATA)) for p in sorted(destination.rglob('*')) if p.is_file()]
    assert not git('diff', '--name-only')
    assert set(git('ls-files', '--others', '--exclude-standard').decode().splitlines()) == set(files)
    write_new(work / 'owned-files.json', dict(baseCommit=head, files=files, report=report))
    print(json.dumps(dict(work=str(work), copiedSources=len(copied), localOnly=len(local),
                         gitFiles=len(files), baseCommit=head)))


if __name__ == '__main__':
    main()
