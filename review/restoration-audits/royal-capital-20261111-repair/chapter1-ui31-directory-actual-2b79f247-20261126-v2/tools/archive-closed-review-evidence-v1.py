"""Copy a sealed, closed evidence plan to one new data-repository audit folder.

This writer changes no existing file and executes no restoration or browser
helper. Optional gzip is a lossless storage representation: both original and
stored byte digests are recorded and every written payload is read back.
"""
from pathlib import Path, PurePosixPath
import argparse
import gzip
import hashlib
import json
import subprocess

ROOT = Path('/home/rikka/Projects/stella')
DATA = ROOT / 'artifacts/stella-script-continuation-20261121/data-checkout'
PREFIX = PurePosixPath('review/restoration-audits/royal-capital-20261111-repair')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_relative(value):
    path = PurePosixPath(value)
    assert not path.is_absolute() and '..' not in path.parts and '.' not in path.parts
    assert path.as_posix() == value
    return path


parser = argparse.ArgumentParser()
parser.add_argument('--plan', required=True)
parser.add_argument('--plan-sha256', required=True)
parser.add_argument('--writer-sha256', required=True)
args = parser.parse_args()
assert sha(Path(__file__).read_bytes()) == args.writer_sha256
plan_raw = Path(args.plan).read_bytes()
assert sha(plan_raw) == args.plan_sha256
plan = json.loads(plan_raw)
assert plan['rootConfirmed'] is True and plan['archiveAuthorized'] is True
assert Path(plan['dataRoot']).resolve() == DATA
git_head = subprocess.check_output(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false',
    '-C', str(DATA), 'rev-parse', 'HEAD'], text=True).strip()
assert git_head == plan['expectedHead']
for name, expected in plan['savedDataFiles'].items():
    path = DATA / safe_relative(name)
    assert sha(path.read_bytes()) == expected, name
relative = safe_relative(plan['targetRelativeDirectory'])
assert relative.parent == PREFIX and relative.name
output = DATA / relative
assert not output.exists()
destinations, sources = set(), []
for entry in plan['entries']:
    source = Path(entry['source'])
    target = safe_relative(entry['destination'])
    assert target.as_posix() not in destinations
    assert source.is_absolute() and source.is_file() and not source.is_symlink()
    assert source.resolve() == source
    raw = source.read_bytes()
    assert len(raw) == entry['sourceBytes'] and sha(raw) == entry['sourceSHA256'], str(source)
    assert entry['encoding'] in ['identity', 'gzip']
    destinations.add(target.as_posix())
    sources.append((entry, raw))
assert not {'INDEX.json', 'README.md', 'ARCHIVE-PLAN.json'} & destinations

# Every source and target precondition is checked before the first repository
# write. A partial write remains failed evidence; no retry overwrites it.
output.mkdir(parents=True)
rows = []
for entry, raw in sources:
    stored = gzip.compress(raw, mtime=0) if entry['encoding'] == 'gzip' else raw
    path = output / entry['destination']
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(stored)
    check = path.read_bytes()
    assert check == stored
    decoded = gzip.decompress(check) if entry['encoding'] == 'gzip' else check
    assert decoded == raw
    rows.append(dict(entry, storedBytes=len(stored), storedSHA256=sha(stored)))
(output / 'ARCHIVE-PLAN.json').write_bytes(plan_raw)
(output / 'README.md').write_text(plan['readme'], encoding='utf-8')
index = dict(schema='stella.closed-review-evidence.archive.v1',
    rootConfirmed=True, originalAndStoredHashesVerified=True,
    expectedHead=git_head, planSHA256=args.plan_sha256, writerSHA256=args.writer_sha256,
    originalRunStatus=plan.get('originalRunStatus'), entries=rows)
(output / 'INDEX.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')
for entry, raw in sources:
    assert sha(Path(entry['source']).read_bytes()) == entry['sourceSHA256']
assert subprocess.check_output(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false',
    '-C', str(DATA), 'rev-parse', 'HEAD'], text=True).strip() == git_head
print(json.dumps(dict(output=str(output), payloadFiles=len(rows),
    totalFiles=len(rows) + 3, storedPayloadBytes=sum(row['storedBytes'] for row in rows),
    indexSHA256=sha((output / 'INDEX.json').read_bytes()),
    existingDataFilesChanged=False)))
