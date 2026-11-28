"""Delete only an explicit reviewed manifest, retaining compact retirement records.

Source files, formal checkouts, open files and the current successful recording
are excluded independently of the manifest.  Paths are never followed through
symlinks, and all selected objects are validated before the first unlink.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

ROOT = Path('/home/rikka/Projects/stella')
A = ROOT / 'artifacts/stella-script-continuation-20261121'
D = A / 'data-checkout'
C = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'
OUT = Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git(base, *args):
    return subprocess.check_output(['git', '-C', str(base), *args])


def snapshot():
    return {
        'dataHead': git(D, 'rev-parse', 'HEAD').decode().strip(),
        'dataStatus': git(D, 'status', '--porcelain').decode(),
        'sourceHead': git(C, 'rev-parse', 'HEAD').decode().strip(),
        'sourceStatus': git(C, 'status', '--porcelain').decode(),
        'rootTrackedStatus': git(ROOT, 'status', '--porcelain', '-uno').decode(),
        'rootTrackedDiffSHA256': hashlib.sha256(git(ROOT, 'diff', '--binary', 'HEAD')).hexdigest(),
        'legacyHead': git(ROOT / 'story_crowd', 'rev-parse', 'HEAD').decode().strip(),
        'legacyTrackedStatus': git(ROOT / 'story_crowd', 'status', '--porcelain', '-uno').decode(),
        'legacyTrackedDiffSHA256': hashlib.sha256(git(ROOT / 'story_crowd', 'diff', '--binary', 'HEAD')).hexdigest(),
    }


def available():
    value = os.statvfs(ROOT)
    return value.f_bavail * value.f_frsize


def identity(path):
    info = path.lstat()
    return [info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_nlink, info.st_blocks * 512]


def save(path, value):
    raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode() + b'\n'
    with path.open('xb') as stream:
        stream.write(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)


def main():
    manifest = Path(sys.argv[1])
    batch = sys.argv[2]
    assert batch.isalnum()
    plan = json.loads(manifest.read_bytes())
    assert plan['rootReviewed'] is True and plan['entries']
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19
    assert sorted(os.sched_getaffinity(0)) == [0, 1]
    before = snapshot()
    assert before['dataStatus'] == ''
    paths = [row['path'] for row in plan['entries']]
    assert len(paths) == len(set(paths))
    tracked = {str(ROOT / name) for name in git(ROOT, 'ls-files', '-z').decode().split('\0') if name}
    pinned = {row['path']: sha(Path(row['path'])) for row in plan.get('retained', [])}
    observed = []
    for row in plan['entries']:
        path = Path(row['path'])
        assert path.is_absolute() and path.parent.resolve() == path.parent
        assert path.is_relative_to(ROOT) and '.git' not in path.parts
        assert not path.is_relative_to(D) and not path.is_relative_to(C)
        assert not path.is_relative_to(ROOT / '.venv-video-ocr')
        assert str(path) not in tracked and str(path) not in pinned
        value = identity(path)
        assert value == row['identity'], path
        assert stat.S_ISREG(value[2]) or stat.S_ISLNK(value[2])
        assert value[5] == 1, ('hardlink would distort release accounting', path)
        if row.get('sha256'):
            assert sha(path) == row['sha256'], path
        observed.append(value)

    # Do not unlink outputs still held by any process that this user can inspect.
    wanted = set(paths)
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            descriptors = list((process / 'fd').iterdir())
        except OSError:
            continue
        for descriptor in descriptors:
            try:
                target = os.readlink(descriptor)
            except OSError:
                continue
            assert target not in wanted, (process.name, target)
    free_before = available()
    save(OUT / f'{batch}-retirement-manifest.json.gz', {
        'plan': plan, 'planSHA256': sha(manifest), 'stateBefore': before,
        'retainedSHA256': pinned, 'noReadableOpenDescriptorMatches': True,
    })
    deleted = []
    try:
        for row, value in zip(plan['entries'], observed):
            path = Path(row['path'])
            assert identity(path) == value
            path.unlink()
            deleted.append(str(path))
    except BaseException:
        save(OUT / f'{batch}-partial.json', {'deleted': deleted})
        raise
    assert all(not os.path.lexists(path) for path in paths)
    # Only remove directories that became empty; never discover new candidates.
    for name in sorted(plan.get('pruneEmptyDirectories', []), key=lambda s: len(Path(s).parts), reverse=True):
        path = Path(name)
        assert path.is_relative_to(ROOT) and '.git' not in path.parts
        try:
            path.rmdir()
        except OSError:
            pass
    assert snapshot() == before
    assert all(sha(Path(name)) == value for name, value in pinned.items())
    groups = {}
    for row in plan['entries']:
        group = groups.setdefault(row['category'], {'files': 0, 'allocatedBytes': 0})
        group['files'] += 1
        group['allocatedBytes'] += row['identity'][6]
    report = {
        'status': 'deleted_and_verified', 'batch': batch, 'deletedFiles': len(deleted),
        'releasedFileAllocationBytes': sum(value[6] for value in observed),
        'availableBefore': free_before, 'availableAfter': available(), 'groups': groups,
        'dataCanonicalAndRootTrackedWorkUnchanged': True,
        'retainedFilesHashVerified': len(pinned), 'noReplacementMediaBackupCreated': True,
        'manifestSHA256': sha(OUT / f'{batch}-retirement-manifest.json.gz'),
    }
    save(OUT / f'{batch}-receipt.json', report)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
