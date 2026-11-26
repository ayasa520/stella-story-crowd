"""Delete only hash-bound, reviewed investigation outputs selected by root.

This is a one-shot maintenance task, not a recursive filename-based cleaner.
The complete allowlist is checked before the first unlink. Original source
material, formal repositories and the current failed capture are excluded.
Small text conclusions and the exact deletion ledger remain on disk; deleted
render dumps are intentionally not copied into another large backup.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

ROOT = Path('/home/rikka/Projects/stella')
A = ROOT / 'artifacts/stella-script-continuation-20261121'
R = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111'
D = A / 'data-checkout'
C = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'
OUT = Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git(root, *arguments):
    return subprocess.check_output(['git', '-C', str(root), *arguments])


def write(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def retained_file_proofs(value):
    """Accept both flat and case-grouped reports without dropping guards.

    UI reports group recording, decoder and review references by case. Every
    nested file proof must survive flattening, including the retained original
    recording and its already committed copy; group objects are not files.
    """
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= value.keys():
            yield value
        else:
            for child in value.values():
                yield from retained_file_proofs(child)
    elif isinstance(value, list):
        for child in value:
            yield from retained_file_proofs(child)


def main():
    assert len(sys.argv) >= 3 and len(sys.argv) % 2 == 1
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19
    assert sorted(os.sched_getaffinity(0)) == [0, 1]
    reports, entries, proofs = [], {}, {}
    for name, expected in zip(sys.argv[1::2], sys.argv[2::2]):
        path = Path(name)
        assert sha(path) == expected, path
        report = json.loads(path.read_bytes())
        assert report['deletionPerformed'] is False
        reports.append({'path': str(path), 'sha256': expected})
        for proof in retained_file_proofs(report.get('keptProofRefs', [])):
            proofs[proof['path']] = proof
        for entry in report['entries']:
            assert entry['path'] not in entries, entry['path']
            entries[entry['path']] = entry
    assert entries
    forbidden = [D, C, OUT, A / 'mimi105-four-case-owner-source-rootfalse-20261127-v2',
                 A / 'mimi105-four-case-root-preparation-deb3093e-20261127-v1',
                 A / 'mimi67-audio-attribution-rootfalse-20261127-v1']
    snapshots = {}
    inodes = {}
    for name, entry in entries.items():
        path = Path(name)
        assert path.is_absolute() and path.resolve() == path
        assert path.is_relative_to(A) or path.is_relative_to(R), path
        assert not any(path.is_relative_to(base) for base in forbidden), path
        assert path.suffix.lower() in {'.gz', '.png', '.jpg', '.jpeg', '.log', '.txt', '.jsonl'}, path
        info = path.lstat()
        assert stat.S_ISREG(info.st_mode) and not path.is_symlink()
        assert info.st_size == entry['bytes'] and info.st_blocks * 512 == entry['allocatedBytes']
        assert sha(path) == entry['sha256'], path
        snapshots[name] = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
        key = (info.st_dev, info.st_ino)
        inode = inodes.setdefault(key, {'selectedLinks': 0, 'totalLinks': info.st_nlink,
                                      'allocatedBytes': info.st_blocks * 512})
        inode['selectedLinks'] += 1
        for retained in entry['retainedReviewPaths']:
            assert retained not in entries and Path(retained).is_file(), retained
    for name, proof in proofs.items():
        path = Path(name)
        assert name not in entries and path.stat().st_size == proof['bytes']
        assert sha(path) == proof['sha256'], name

    # Never remove a selected output while another process still has it open.
    # Inspect descriptor targets only; unrelated application arguments and
    # environment variables are neither collected nor published.
    opened = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            for descriptor in (proc / 'fd').iterdir():
                try:
                    target = os.readlink(descriptor)
                    if target in entries:
                        opened.append({'pid': int(proc.name), 'path': target})
                except (OSError, PermissionError):
                    pass
        except (OSError, PermissionError):
            pass
    assert not opened, opened
    before = {'dataHead': git(D, 'rev-parse', 'HEAD').decode().strip(),
              'dataStatus': git(D, 'status', '--porcelain=v1').decode(),
              'sourceHead': git(C, 'rev-parse', 'HEAD').decode().strip(),
              'sourceStatus': git(C, 'status', '--porcelain=v1').decode()}
    assert before['dataHead'] == 'deb3093e88f0004ad385cdec7b61ea91f5f2c2e2'
    assert before['dataStatus'] == ''
    assert before['sourceHead'] == '6630ac70f17332efa031d021af00532d42307568'
    assert before['sourceStatus'] == '?? scripts/__pycache__/\n'
    available_before = os.statvfs(ROOT).f_bavail * os.statvfs(ROOT).f_frsize
    ledger = {'schema': 'stella.reviewed-investigation-cleanup.v3',
              'rootConfirmed': True, 'deletionAuthorizedByUser': True,
              'sourceReports': reports, 'before': before, 'keptProofRefs': list(proofs.values()),
              'entries': list(entries.values()), 'filesOpenByProcesses': opened}
    write('deletion-manifest.root-approved.json', ledger)

    # Recheck each inode immediately before unlink; stop on any replacement.
    # Only selected files are removed, leaving directory structure and every
    # unselected source, review, environment and pending package untouched.
    removed = []
    try:
        for name in entries:
            path = Path(name)
            info = path.lstat()
            assert (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) == snapshots[name]
            path.unlink()
            removed.append(name)
    except BaseException:
        write('partial-deletion.json', {'removed': removed})
        raise
    assert all(not os.path.lexists(name) for name in entries)
    assert git(D, 'status', '--porcelain=v1').decode() == before['dataStatus']
    assert git(C, 'status', '--porcelain=v1').decode() == before['sourceStatus']
    for name, proof in proofs.items():
        assert sha(Path(name)) == proof['sha256']
    report = {'schema': 'stella.investigation-cleanup.receipt.v3', 'status': 'deleted_and_verified',
              'deletedFiles': len(removed),
              'deletedLogicalBytes': sum(v['bytes'] for v in entries.values()),
              'selectedAllocatedBytes': sum(v['allocatedBytes'] for v in entries.values()),
              'allocatedBytesReleasedFromUnlinkedInodes': sum(v['allocatedBytes'] for v in inodes.values()
                  if v['selectedLinks'] == v['totalLinks']),
              'availableBytesBefore': available_before,
              'availableBytesAfter': os.statvfs(ROOT).f_bavail * os.statvfs(ROOT).f_frsize,
              'dataAndCanonicalSourceUnchanged': True, 'retainedConclusionsHashVerified': len(proofs),
              'originalVideoFramesOcrModelsAudioScriptsArmEnvironmentPreserved': True,
              'noBrowserStarted': True, 'noWholeRestorationAcceptance': True,
              'deletionManifestSHA256': sha(OUT / 'deletion-manifest.root-approved.json'),
              'generatedOutputsHaveNoReplacementBackup': True,
              'historicalReferencesToDeletedPathsAreIntentionallyRetired': True}
    write('receipt.json', report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
