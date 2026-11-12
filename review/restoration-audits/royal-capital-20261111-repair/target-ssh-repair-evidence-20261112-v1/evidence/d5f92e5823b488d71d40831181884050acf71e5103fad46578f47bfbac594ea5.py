"""Archive the scoped SSH repair and exact successful publication evidence.

Only the repository's SSH route and author configuration changed. Private Git
configuration backups and all key/known_hosts contents stay outside this public
evidence package. Verified source files, route snapshots and transport receipts
are copied exactly; no story field or runtime acceptance changes in this commit.
"""
from pathlib import Path
import subprocess
import json

from target_identity_publication_v1 import archive_files, read, write_new

ROOT = Path('/home/rikka/Projects/stella')
R = Path(__file__).parent
DATA = ROOT / 'story_crowd_data'
NAME = 'target-ssh-repair-evidence-20261112-v1'


def main():
    def git(*args):
        return subprocess.check_output(['git', '--no-optional-locks', *args], cwd=DATA)
    assert not git('status', '--porcelain')
    head = git('rev-parse', 'HEAD').decode().strip()
    repair = read(R / 'target-ssh-repair-20261112-v1/final-repair-receipt.json')
    assert repair['head'] == repair['remoteAck'] == head
    assert repair['actualNewCommitPushed'] and repair['ordinaryGitPushExitCode'] == 0
    paths = {R / 'github_ssh_route_v1.py', R / 'target_identity_publish_git_v3.py',
             R / 'target_identity_publish_git_v2.py', R / 'PROGRESS.md', Path(__file__)}
    folder = R / 'target-ssh-repair-20261112-v1'
    paths.update(p for p in folder.iterdir() if p.is_file() and p.suffix in ('.json', '.jsonl'))
    for name in ['target-p30-ord45to59-publication-20261112-v1',
                 'target-p30-ord60to74-publication-20261112-v1',
                 'target-arm-baseline-evidence-20261112-v1']:
        for file in ['push.json', 'final-publication-receipt.json', 'committed-blobs.json',
                     'push-attempt2.json', 'remote-probe-before-retry-v2.json']:
            candidate = R / name / file
            if candidate.is_file():
                paths.add(candidate)
    destination = DATA / 'review/restoration-audits/royal-capital-20261111-repair' / NAME
    work = R / NAME
    assert not destination.exists() and not work.exists()
    work.mkdir()
    copied, local = archive_files(destination, paths)
    assert not local
    report = dict(status='ssh443_repair_verified_by_actual_push_and_remote_ack',
        baseCommit=head, nativeFieldsChangedByThisCheckpoint=0,
        lastPublishedCharacterFields=5, cumulativeTargetCharacterFields=62,
        repositoryLocalChangesOnly=True, strictHostKeyVerificationKept=True,
        globalGitOrSshConfigChanged=False, systemDnsChanged=False,
        knownHostsUnchangedSha256=repair['knownHostsUnchangedSha256'],
        privateConfigurationOrKeysArchived=False, browserStarted=False,
        newPlaybackVisits=0, fullRestorationAccepted=False)
    write_new(destination / 'MANIFEST.json', dict(schema='stella.exact_evidence_archive.v1',
        **report, copiedFiles=copied, localOnlyEvidence=[]))
    files = [str(p.relative_to(DATA)) for p in sorted(destination.rglob('*')) if p.is_file()]
    assert not git('diff', '--name-only')
    assert set(git('ls-files', '--others', '--exclude-standard').decode().splitlines()) == set(files)
    write_new(work / 'owned-files.json', dict(baseCommit=head, files=files, report=report))
    print(json.dumps(dict(work=str(work), sources=len(copied), files=len(files), baseCommit=head)))


if __name__ == '__main__':
    main()
