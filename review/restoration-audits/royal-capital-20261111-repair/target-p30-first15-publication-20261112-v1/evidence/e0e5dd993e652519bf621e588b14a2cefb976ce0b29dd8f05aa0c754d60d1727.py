"""Commit one audited package, verify its blobs, push and check exact remote ACK.

The prepared file list is an ownership boundary, not a broad `git add`. A failed
push leaves the existing commit for investigation; this program never retries,
resets, force pushes or changes SSH/Git configuration. Final receipts remain in
the repair evidence directory because their commit ID cannot be in that commit.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

DATA = Path('/home/rikka/Projects/stella/story_crowd_data')
SSH = 'ssh -oBatchMode=yes -oConnectTimeout=10 -oHostKeyAlias=github.com -oHostname=ssh.github.com -p443'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def git(*args):
    return subprocess.check_output(['git', '--no-optional-locks', *args], cwd=DATA)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--message', required=True)
    args = parser.parse_args()
    work = args.work.resolve()
    spec = json.loads((work / 'owned-files.json').read_bytes())
    files, base = spec['files'], spec['baseCommit']
    assert git('rev-parse', 'HEAD').decode().strip() == base
    assert git('branch', '--show-current').decode().strip() == 'main'
    assert git('remote', 'get-url', 'origin').decode().strip() == 'git@github.com:ayasa520/stella-story-crowd.git'
    staged = set(git('diff', '--cached', '--name-only').decode().splitlines())
    assert not staged or staged == set(files), 'Do not adopt another staged change'
    changed = set(git('diff', '--name-only').decode().splitlines())
    changed.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    changed.update(staged)
    assert changed == set(files), (changed - set(files), set(files) - changed)
    expected = {name: (DATA / name).read_bytes() for name in files}
    git('add', '--', *files)
    assert set(git('diff', '--cached', '--name-only').decode().splitlines()) == set(files)
    git('diff', '--cached', '--check')
    for name, raw in expected.items():
        assert git('show', ':' + name) == raw, name
    body = (args.message + '\n\n'
            'Install only independently reviewed character/costume identities using the guarded native importer. '
            'Preserve exact source/reference hashes, staging, resource audit and field readback. '
            'All other native fields, original 38 baseline files and Studio revision 2656 remain unchanged.\n\n'
            'Validation: exact staged native delta; resource/ownership dry-run; all 140 scenes audited; '
            'committed blobs verified. No new assets or playback visits; motion, face, geometry, timing '
            'and whole-part restoration remain unaccepted.\n')
    body_path = work / 'commit-message.txt'
    if body_path.exists():
        assert body_path.read_text() == body
    else:
        with body_path.open('x', encoding='utf-8') as stream:
            stream.write(body)
    # Migration intentionally avoids global Git settings. Reuse the repository's
    # established committer identity for this command only when target config is
    # absent; no global account or SSH configuration is written.
    name = git('show', '-s', '--format=%cn', base).decode().strip()
    email = git('show', '-s', '--format=%ce', base).decode().strip()
    assert name and email
    commit = git('-c', 'commit.gpgsign=false', '-c', 'user.name=' + name,
                 '-c', 'user.email=' + email, 'commit', '--file', str(body_path)).decode()
    head = git('rev-parse', 'HEAD').decode().strip()
    actual = set(git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').decode().splitlines())
    assert actual == set(files)
    verified = []
    for name, raw in expected.items():
        assert git('show', head + ':' + name) == raw, name
        verified.append(dict(path=name, bytes=len(raw), sha256=sha(raw)))
    write_new(work / 'committed-blobs.json', dict(head=head, baseCommit=base, files=verified, commitOutput=commit))
    result = subprocess.run(['git', '-c', 'core.sshCommand=' + SSH, 'push', 'origin', 'main'],
                            cwd=DATA, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    write_new(work / 'push.json', dict(head=head, exitCode=result.returncode,
        stdout=result.stdout.decode(), stderr=result.stderr.decode(), hostKeyVerificationKept=True))
    assert result.returncode == 0, 'Inspect push.json; do not repeat application or commit'
    remote = git('-c', 'core.sshCommand=' + SSH, 'ls-remote', 'origin', 'refs/heads/main').decode().strip()
    assert remote == head + '\trefs/heads/main', remote
    assert not git('status', '--porcelain')
    # Merge the local audit first, then set publication status. Both reports
    # contain a status/baseCommit; keyword expansion into dict() would reject
    # those duplicates after an otherwise successful push.
    receipt = {**spec['report'], 'status': 'published_remote_ack_verified',
        'baseCommit': base, 'head': head, 'remoteAck': head,
        'repository': str(DATA), 'committedBlobsVerified': len(verified), 'worktreeClean': True}
    write_new(work / 'final-publication-receipt.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
