"""Independently close this one actual UI31 run after its original terminal.

This never launches a browser, signals a foreign process, rewrites inputs, or
reclassifies a failed run. It verifies every unique frozen path, repository and
source membership, actual owned process groups, announced port and profile.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import socket
import subprocess
from urllib.parse import urlparse

ROOT = Path('/home/rikka/Projects/stella')
A = ROOT / 'artifacts/stella-script-continuation-20261121'
O = Path(__file__).resolve().parent
K = A / 'ui31-runtime-source-kit-rootfalse-20261126-v2/attempt-1'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    raw = path.read_bytes()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        # Retain the actual first read, never a later read of the pathname.
        with (O / 'closure-json-failure.raw.gz').open('xb') as stream:
            stream.write(gzip.compress(raw, mtime=0))
        with (O / 'closure-json-failure.doc.gz').open('xb') as stream:
            stream.write(gzip.compress(error.doc.encode('utf8', 'surrogatepass'), mtime=0))
        raise


parser = argparse.ArgumentParser()
parser.add_argument('--exit-code', type=int, required=True)
parser.add_argument('--completion-chunk', required=True)
args = parser.parse_args()
release_path = O / 'runtime.root-approved.json'
assert digest(release_path) == 'a00fb1245dad2961929841d9f7fc96ca9c0e568e947e02a5a2bf283dda31d1e8'
release = read(release_path)
inventory_path = Path(release['guardInventory']['path'])
assert digest(inventory_path) == release['guardInventory']['sha256']
inv = read(inventory_path)
D, C = Path(inv['dataRoot']), Path(inv['sourceRoot'])
expected = {}


def add(path, sha):
    path = str(path)
    assert path not in expected or expected[path] == sha, path
    expected[path] = sha


for name in ['globalGuards', 'toolFiles', 'sharedClosure', 'evidenceGuards']:
    for path, sha in inv[name].items():
        add(path, sha)
for name, base in [('dataInputs', D), ('protectedFirstThree', D), ('sourceFiles', C), ('distFiles', C / 'dist')]:
    for path, sha in inv[name].items():
        add(base / path, sha)
for path, sha in release['runtimeBindings'].items():
    add(ROOT / path, sha)
for path, sha in release['additionalGuards'].items():
    add(path, sha)
add(release_path, digest(release_path))
add(inventory_path, digest(inventory_path))
for path, sha in expected.items():
    assert digest(Path(path)) == sha, path


def git(root, *args):
    return subprocess.check_output(['/usr/bin/git', '-C', str(root), *args])


assert set(git(D, 'ls-files', '-z').decode().split('\0')[:-1]) == set(inv['dataInputs'])
assert set(git(C, 'ls-files', '-z').decode().split('\0')[:-1]) == set(inv['sourceFiles'])
assert {str(p.relative_to(C / 'dist')) for p in (C / 'dist').rglob('*') if p.is_file()} == set(inv['distFiles'])
for name in ['native', 'review']:
    assert {str(p.relative_to(D)) for p in (D / name).rglob('*') if p.is_file()} == {
        p for p in inv['dataInputs'] if p.startswith(name + '/')}
for path, head, status in [(D, release['publishedHead'], ''), (C, release['sourceHead'], release['sourceStatus'])]:
    assert git(path, 'rev-parse', 'HEAD').decode().strip() == head
    assert git(path, 'status', '--short').decode().strip() == status
owner = read(K / 'process-exit.json')
assert owner['supervisorExitCode'] == args.exit_code
assert owner['beforeGuardsVerified'] and owner['afterGuardsVerified'] and owner['inputsUnchanged']
assert owner['cleanupErrors'] == []
pids = [owner['supervisorPid'], *[p['pid'] for p in owner['owned']]]
groups = {p['pgid'] for p in owner['owned']}
assert all(not Path('/proc', str(pid)).exists() for pid in pids), pids
ps = subprocess.check_output(['/usr/bin/ps', '-eo', 'pid,ppid,pgid,comm,args'], text=True).splitlines()[1:]
assert not [row for row in ps if len(row.split()) >= 4 and int(row.split()[2]) in groups]
profile = owner['profileCleanup']['path']
assert profile and not Path(profile).exists()
assert not [row for row in ps if profile in row]
port = urlparse(owner['announcedPortProof']['address']).port
assert port is not None
with socket.socket() as sock:
    sock.settimeout(.5)
    code = sock.connect_ex(('127.0.0.1', port))
assert code == 111, code
result_path = K / 'sweep.result.json'
result = read(result_path) if result_path.exists() else {}
receipt = dict(rootConfirmed=True, originalSession=7407, originalExitCode=args.exit_code,
    originalCompletionChunk=args.completion_chunk, fullUniqueExpectedPathsFreshExact=len(expected),
    all32903TrackedDataAndCSourceDistToolsAndRefsExact=True,
    exactDataTrackedAndNativeReviewAndSourceDistMembership=True,
    all22ProtectedExact=True, ownedPIDsAndPGIDsAbsent=pids, escapedProfileProcesses=[],
    actualAnnouncedPort=port, connectEx=code, ownedProfileAbsent=True, cleanupErrors=[],
    completedSections=result.get('completed', []),
    all31ApiDomChecksPassed=result.get('all31ApiDomChecksPassed', False),
    actualEdgeMeasurements=result.get('actualEdgeMeasurements'),
    originalFailureRetained=args.exit_code != 0,
    DWriteHoldReleasedAfterThisClosure=True, fullActingOrGameplayAccepted=False)
with (O / 'runtime.root-closure.json').open('x') as stream:
    json.dump(receipt, stream, indent=2)
    stream.write('\n')
print(json.dumps(receipt))
