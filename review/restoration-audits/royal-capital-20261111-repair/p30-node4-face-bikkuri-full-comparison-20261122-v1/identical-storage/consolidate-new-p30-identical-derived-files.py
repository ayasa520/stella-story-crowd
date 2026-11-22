"""Share identical closed P30 derivatives while preserving every evidence path."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import os
import stat

A = Path('/home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121')
K = A / 'p30-node4-face-bikkuri-owner-kit-rootfalse-v1'
FRAMES = A / 'p30-node4-face-bikkuri-actual-decode-preparation-rootfalse-v1/run-1/p30-node4-face-bikkuri-only'
OUT = A / 'p30-new-derived-identical-storage-consolidation-v1'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def metadata(path):
    value = path.lstat()
    assert stat.S_ISREG(value.st_mode) and not path.is_symlink()
    return dict(path=str(path), bytes=value.st_size, sha256=digest(path),
                device=value.st_dev, inode=value.st_ino, links=value.st_nlink,
                mode=value.st_mode, uid=value.st_uid, gid=value.st_gid,
                mtimeNs=value.st_mtime_ns, ctimeNs=value.st_ctime_ns,
                allocatedBytes=value.st_blocks * 512)


# Scope is deliberately limited to this newly closed attempt. Original video,
# source frames, legacy runs, repository files and environments are excluded.
assert not Path('/proc/22318').exists() and not Path('/proc/22332').exists()
index = json.loads((FRAMES / 'frames-index.json').read_text())
groups = defaultdict(list)
for row in index['frames']:
    path = FRAMES / row['file']
    assert path.parent == FRAMES / 'frames'
    assert path.stat().st_size == row['bytes'] and digest(path) == row['sha256']
    groups[(row['bytes'], row['sha256'])].append(path)
selected = [paths for paths in groups.values() if len(paths) > 1]
selected += [[K / 'attempt-1/inputs-before.json', K / 'attempt-1/inputs-after.json'],
             [K / 'prepared/p30-node4-face-bikkuri-only.raw.json.gz',
              K / 'attempt-1/p30-node4-face-bikkuri-only/normal-http-program.json.gz']]
snapshots = [[metadata(path) for path in paths] for paths in selected]
for rows in snapshots:
    assert len({(row['bytes'], row['sha256']) for row in rows}) == 1
    assert len({(row['device'], row['mode'], row['uid'], row['gid']) for row in rows}) == 1
    assert all(row['links'] == 1 for row in rows)
    assert len({row['inode'] for row in rows}) == len(rows)

OUT.mkdir()
(OUT / 'original-filesystem-metadata.json').write_text(json.dumps(snapshots, indent=2) + '\n')
free_before = os.statvfs(A).f_bavail * os.statvfs(A).f_frsize
changed = 0
with (OUT / 'operations.jsonl').open('x') as journal:
    for paths, rows in zip(selected, snapshots):
        canonical = paths[0]
        for target, before in zip(paths[1:], rows[1:]):
            assert metadata(target) == before and digest(canonical) == before['sha256']
            # A same-directory temporary hard link plus atomic replace keeps
            # the target path continuously present. No pixel/JSON bytes change.
            # Hard links intentionally share inode/mtime and alter ctime/nlink;
            # the original per-path stat evidence is retained above, not claimed
            # unchanged. These sealed derivative files must remain immutable.
            temporary = target.with_name(target.name + '.p30-consolidation-link')
            assert not temporary.exists()
            journal.write(json.dumps(dict(target=str(target), canonical=str(canonical), before=before)) + '\n')
            journal.flush()
            os.fsync(journal.fileno())
            os.link(canonical, temporary)
            os.replace(temporary, target)
            assert digest(target) == before['sha256'] and target.stat().st_ino == canonical.stat().st_ino
            changed += 1

for rows in snapshots:
    for before in rows:
        path = Path(before['path'])
        assert path.stat().st_size == before['bytes'] and digest(path) == before['sha256']
for row in index['frames']:
    assert digest(FRAMES / row['file']) == row['sha256']
free_after = os.statvfs(A).f_bavail * os.statvfs(A).f_frsize
receipt = dict(groups=len(selected), replacedStorageEntries=changed,
               conservativeAllocatedBytesReleased=sum(row['allocatedBytes'] for rows in snapshots for row in rows[1:]),
               freeBefore=free_before, freeAfter=free_after, observedFreeChange=free_after-free_before,
               all484FramePathsAndBytesPreserved=True, allSelectedBytesPreserved=True,
               originalVideoSourceLegacyRunsRepositoriesEnvironmentsUntouched=True,
               physicalInodeLayoutChanged=True, originalPerPathStatMetadataRetained=True,
               perPathMtimeAndInodeUnchanged=False, pixelsDecodedOrEdited=False)
(OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
