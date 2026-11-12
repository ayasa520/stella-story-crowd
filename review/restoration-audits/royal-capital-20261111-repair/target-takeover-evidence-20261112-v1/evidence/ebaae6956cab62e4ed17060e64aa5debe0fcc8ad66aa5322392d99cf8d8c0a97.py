"""Read-only, independently parsed diagnosis of the applied P29 batch-five data.

The caller observed intermittent JSON decoder exceptions without a demonstrated
file change. This diagnostic records bytes, exception documents and character
windows rather than attributing a cause. The pure decoder explicitly replaces
BOTH the string parser and scanner; merely replacing make_scanner would leave
the C scanstring accelerator in use. ARM Node is admitted only after checking
its executable ELF machine field and its own process.arch report.

No importer, installation, formal-data mutation or browser is invoked. The
receipt separately reports byte integrity, semantic scope and parser outcomes.
"""

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import json.decoder
import json.scanner
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path('/home/rikka/Projects/stella')
R = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111'
DATA = ROOT / 'story_crowd_data'
SOURCE = R / 'target-p29-batch5-publication-20261112-v1'
STAGING = SOURCE / 'staging'
OUT = Path(__file__).parent
BASE = '8f808152e29c95bdc2f043ac96be63c0727bf661'
TARGET = 'e984012e561776e631ef2f096d72535ffd76f6e4'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git_raw(*args):
    return subprocess.check_output(['git', '-C', str(DATA), *args])


def data_read(name):
    # Root published batch5 and advanced to batch6 while this independent
    # diagnostic was being prepared. Audit immutable batch5 Git blobs rather
    # than confusing the later current worktree with the three-field batch.
    return git_raw('show', TARGET+':'+name)


pure_decoder = json.JSONDecoder()
pure_decoder.parse_string = json.decoder.py_scanstring
pure_decoder.scan_once = json.scanner.py_make_scanner(pure_decoder)
require(pure_decoder.parse_string is json.decoder.py_scanstring and
        pure_decoder.scan_once.__module__ == 'json.scanner', 'Pure parser not established')


def pure(raw):
    return pure_decoder.decode(raw.decode('utf-8') if isinstance(raw, bytes) else raw)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


head_before = git_raw('rev-parse', 'HEAD').decode().strip()
require(git_raw('rev-parse', TARGET+'^').decode().strip() == BASE, 'Batch5 parent differs')
names = ['manifest.json', 'assets/catalog.json', 'native/scenes/10040053.json',
         'review/scenes/10040053.json', 'review/native-restoration.json']
raws = {name: data_read(name) for name in names}
values = {name: pure(raw) for name, raw in raws.items()}
parser_results, errors = [], []


def error_evidence(error, name, engine, iteration, raw):
    doc = getattr(error, 'doc', '')
    pos = getattr(error, 'pos', None)
    window = doc[max(0, pos-96):pos+96] if isinstance(pos, int) else ''
    encoded_doc = doc.encode('utf-8', errors='surrogatepass')
    return dict(file=name, engine=engine, iteration=iteration, type=type(error).__name__,
                message=str(error), msg=getattr(error, 'msg', None), pos=pos,
                line=getattr(error, 'lineno', None), column=getattr(error, 'colno', None),
                sourceByteSha256=sha(raw), sourceBytes=len(raw), docCharacters=len(doc),
                exceptionDocUtf8Sha256=sha(encoded_doc), exceptionDocEqualsInput=doc==raw.decode('utf-8'),
                exceptionDocWindow=window, windowCodePoints=[ord(char) for char in window],
                sourceByteOffsetAtError=len(doc[:pos].encode('utf-8', errors='surrogatepass'))
                if isinstance(pos, int) else None)


# Re-read disk on every C-decoder attempt; successes are checked against the
# independent pure-decoder object, not merely counted as a successful parse.
for iteration in range(3):
    for name in names:
        raw = data_read(name)
        require(raw == raws[name], f'Committed bytes differ during parser diagnosis: {name}')
        try:
            parsed = json.loads(raw)
            equal = parsed == values[name]
            parser_results.append(dict(engine='cpython_standard_C_scanner', iteration=iteration,
                                       file=name, success=True, equalsPureConsensus=equal))
            require(equal, f'Standard decoder object differs: {name}')
        except json.JSONDecodeError as error:
            errors.append(error_evidence(error, name, 'cpython_standard_C_scanner', iteration, raw))
            parser_results.append(dict(engine='cpython_standard_C_scanner', iteration=iteration,
                                       file=name, success=False, errorIndex=len(errors)-1))

for iteration in range(3):
    for name in names:
        try:
            parsed = pure(raws[name])
            equal = parsed == values[name]
            parser_results.append(dict(engine='cpython_true_pure_python', iteration=iteration,
                                       file=name, success=True, equalsPureConsensus=equal))
            require(equal, f'Pure decoder object differs: {name}')
        except json.JSONDecodeError as error:
            errors.append(error_evidence(error, name, 'cpython_true_pure_python', iteration, raws[name]))
            parser_results.append(dict(engine='cpython_true_pure_python', iteration=iteration,
                                       file=name, success=False, errorIndex=len(errors)-1))

node = Path('/usr/bin/node')
with node.open('rb') as stream:
    elf_header = stream.read(64)
require(elf_header[:4] == b'\x7fELF' and elf_header[4] == 2 and elf_header[5] == 1,
        'Node is not a little-endian ELF64 executable')
require(struct.unpack('<H', elf_header[18:20])[0] == 183, 'Node ELF is not AArch64')
node_arch = subprocess.check_output([str(node), '-p', 'process.arch'], text=True).strip()
require(node_arch == 'arm64', 'Installed Node does not report ARM64')
node_version = subprocess.check_output([str(node), '--version'], text=True).strip()
node_code = """
const fs = require('fs');
const crypto = require('crypto');
const child = require('child_process');
const records = [];
const [repository, commit, ...files] = process.argv.slice(1);
for (const file of files) {
  const raw = child.execFileSync('git', ['-C', repository, 'show', commit+':'+file], {maxBuffer: 32*1024*1024});
  records.push({file, sha256: crypto.createHash('sha256').update(raw).digest('hex'),
    value: JSON.parse(raw.toString('utf8'))});
}
process.stdout.write(JSON.stringify(records));
"""
node_runs = []
for iteration in range(1):
    process = subprocess.run([str(node), '-e', node_code, str(DATA), TARGET, *names],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    require(process.returncode == 0, 'ARM Node JSON.parse failed: '+process.stderr.decode(errors='replace'))
    records = pure(process.stdout)
    for record in records:
        name = record['file']
        require(record['sha256'] == sha(raws[name]) and record['value'] == values[name],
                f'ARM Node parsed object differs: {name}')
    node_runs.append(dict(iteration=iteration, exitCode=process.returncode,
                          outputSha256=sha(process.stdout), outputBytes=len(process.stdout),
                          stderr=process.stderr.decode(), files=names, equalsPureConsensus=True))

manifest = values['manifest.json']
ownership = values['review/native-restoration.json']
catalog = values['assets/catalog.json']
incoming_raw = (STAGING/'manifest.json').read_bytes()
incoming = pure(incoming_raw)
packet_path = R/'visual-high/accepted-p29-batch5-identities-20261112-v1.json'
packet_raw = packet_path.read_bytes()
packet = pure(packet_raw)
require(sha(packet_raw) == '63f74a8c3edea283ffae0af6691fd7ba48d8c2ab2e04b6c6a36701efe91b022f',
        'Accepted packet bytes differ')
stage_equal = []
for name, expected in incoming['files'].items():
    staged_raw = (STAGING/name).read_bytes()
    require(sha(staged_raw) == expected, 'Staged input hash differs: '+name)
    if not name.startswith(('native/scenes/', 'review/scenes/')):
        continue
    require(staged_raw == data_read(name),
            f'Installed scene differs from staged bytes: {name}')
    require(ownership['files'][name] == expected, 'Current ownership does not bind staged scene')
    stage_equal.append(dict(file=name, sha256=expected, bytes=len(staged_raw)))

old_manifest_raw = git_raw('show', BASE+':manifest.json')
old_manifest = pure(old_manifest_raw)
expected_manifest = deepcopy(old_manifest)
incoming_by_id = {entry['id']:entry for entry in incoming['scenes']}
expected_manifest['scenes'] = [deepcopy(incoming_by_id.get(entry['id'], entry))
                               for entry in old_manifest['scenes']]
require(not incoming.get('directoryEntryUpdates'), 'Unexpected directory updates')
require(not incoming.get('recordings'), 'Unexpected recording changes')
require(manifest == expected_manifest and raws['manifest.json'] == encoded(expected_manifest),
        'Full installed manifest differs from independent expected bytes')

old_ownership = pure(git_raw('show', BASE+':review/native-restoration.json'))
expected_ownership = deepcopy(old_ownership)
expected_ownership['files'].update({name:value for name,value in incoming['files'].items()
                                     if name.startswith(('native/scenes/','review/scenes/'))})
for entry in incoming['scenes']:
    expected_ownership['scenes'][str(entry['id'])] = sha(encoded(entry))
batch_id = sha(incoming_raw)[:20]
expected_ownership['batches'].append(batch_id)
require(ownership == expected_ownership and raws['review/native-restoration.json'] == encoded(expected_ownership),
        'Ownership differs from independently reconstructed expected bytes')
ownership_files_checked = []
for name, expected in ownership['files'].items():
    raw = data_read(name)
    require(sha(raw) == expected, f'Owned file hash differs: {name}')
    ownership_files_checked.append(dict(file=name, sha256=expected, bytes=len(raw)))

field_counts = Counter()
protected, native_changes = [], []
library_nodes, owned_nodes = 0, 0
expected_targets = {(change['sceneId'],change['scenarioId']):change for change in packet['changes']}
for entry in manifest['scenes']:
    name = entry['path']
    raw = data_read(name)
    old_raw = git_raw('show', BASE+':'+name)
    document = pure(raw)
    old = pure(old_raw)
    require(len(document['scenario_list']) == entry['nodeCount'], 'Scene node count differs')
    library_nodes += len(document['scenario_list'])
    if str(entry['id']) not in ownership['scenes']:
        for protected_name in [entry['path'],entry['reviewPath']]:
            protected_raw = data_read(protected_name)
            require(protected_raw == git_raw('show', BASE+':'+protected_name), 'Protected baseline differs')
            protected.append(dict(file=protected_name, sha256=sha(protected_raw)))
        continue
    owned_nodes += len(document['scenario_list'])
    require({key:value for key,value in document.items() if key!='scenario_list'} ==
            {key:value for key,value in old.items() if key!='scenario_list'}, 'Non-row native data differs')
    require(len(document['scenario_list']) == len(old['scenario_list']), 'Native rows added/removed')
    for current, before in zip(document['scenario_list'],old['scenario_list']):
        for field in ['character','motion','bg_picture','bg_music','voice']:
            field_counts[field] += bool(current.get(field))
        if current != before:
            identity = (entry['id'],current['scenario_id'])
            require(identity in expected_targets, 'Unexpected changed native node')
            change = expected_targets[identity]
            require(change['expected'] == {'character':''} and before['character']=='' and
                    current['character']==change['fields']['character'] and
                    {key:value for key,value in current.items() if key!='character'} ==
                    {key:value for key,value in before.items() if key!='character'},
                    'Native change exceeds exact accepted character field')
            review = pure(data_read(entry['reviewPath']))['scenarios'][str(current['scenario_id'])]
            require(review['stableKey']==change['stableKey'] and review['sourceText']==change['sourceText'],
                    'Current target stable key or Japanese differs')
            require(current['character'] in catalog['models'], 'Character has no packaged model')
            native_changes.append(dict(sceneId=identity[0],scenarioId=identity[1],stableKey=change['stableKey'],
                                       before='',after=current['character']))
require(len(native_changes)==3 and len(protected)==38 and len(ownership['scenes'])==121 and
        owned_nodes==4998 and library_nodes==5599, 'Library counts differ')
require(dict(field_counts)==dict(character=1823,motion=5,bg_picture=146,bg_music=32,voice=12),
        'Explicit field counts differ')
studio_raw = (ROOT/'data/story_studio/project.json').read_bytes()
require(sha(studio_raw)=='ebd974d90f89088fa3a504c1f419ae01c352a24e6bd80209c5ec651295d38522',
        'Protected Studio bytes differ')
require(data_read('assets/catalog.json')==git_raw('show', BASE+':assets/catalog.json'),
        'Catalog differs from base Git bytes')
require(data_read('assets/package.json')==git_raw('show', BASE+':assets/package.json'),
        'Asset package differs from base Git bytes')

reported_failure = pure((SOURCE/'audit-command.json').read_bytes())
reported_position = 868156
doc = raws['manifest.json'].decode('utf-8')
window = doc[reported_position-96:reported_position+96]
failure_location = dict(archivedAuditCommandSha256=sha((SOURCE/'audit-command.json').read_bytes()),
    archivedExitCode=reported_failure['exitCode'], reportedChar=reported_position,
    currentManifestByteSha256=sha(raws['manifest.json']), currentWindow=window,
    currentWindowCodePoints=[ord(char) for char in window],
    currentUtf8ByteOffset=len(doc[:reported_position].encode('utf-8')),
    sourceOfPosition='Archived C-decoder JSONDecodeError; archived exception document itself was not captured.')
head_after = git_raw('rev-parse','HEAD').decode().strip()
for name, raw in raws.items():
    require(data_read(name)==raw, 'Committed guarded bytes differ during readback')
result = dict(schema='stella.independent_batch5_readback.v1',
    status='passed_exact_data_integrity_and_independent_parser_consensus',
    createdUtc=datetime.now(timezone.utc).isoformat(), reviewer='/root/p30_packet_preflight',
    observedRepositoryHeadBefore=head_before,observedRepositoryHeadAfter=head_after,
    auditedCommit=TARGET,baseCommit=BASE,batchId=batch_id,
    dataReadScope='Immutable committed batch5 Git blobs. Current worktree may contain later authorized batches and is not represented as batch5 state.',
    parserEnvironment=dict(pythonVersion=sys.version, platform=sys.platform,
        standardScanOnceType=type(json.JSONDecoder().scan_once).__name__,
        pureScanOnceModule=pure_decoder.scan_once.__module__, pureScanStringName=pure_decoder.parse_string.__name__,
        nodeExecutable=str(node),nodeElfMachine=183,nodeArch=node_arch,nodeVersion=node_version),
    guardedFiles=[dict(file=name,sha256=sha(raw),bytes=len(raw)) for name,raw in raws.items()],
    standardAttempts=15,standardSuccesses=sum(x['success'] for x in parser_results if x['engine']=='cpython_standard_C_scanner'),
    pureAttempts=15,pureSuccesses=sum(x['success'] for x in parser_results if x['engine']=='cpython_true_pure_python'),
    observedErrors=errors,parserAttempts=parser_results,nodeRuns=node_runs,
    archivedFailureLocation=failure_location,
    independentFullManifestExpectedBytesEqual=True,independentOwnershipExpectedBytesEqual=True,
    stagingExactlyEqualsInstalled=stage_equal,ownershipFilesChecked=ownership_files_checked,
    exactNativeChanges=native_changes,explicitFields=dict(field_counts),protectedBaseline=protected,
    protectedStudioSha256=sha(studio_raw),protectedStudioRevision=pure(studio_raw).get('revision'),
    libraryScenes=len(manifest['scenes']),libraryNodes=library_nodes,ownedScenes=len(ownership['scenes']),ownedNodes=owned_nodes,
    resourceCounts=dict(models=len(catalog['models']),backgrounds=len(catalog['backgrounds']),music=len(catalog['music'])),
    catalogEqualsBaseGitBytes=True,assetPackageEqualsBaseGitBytes=True,
    cause='Undetermined. This receipt records observations and data consensus; it assigns no installation, cache, runtime or hardware cause.',
    formalWrites=0,importerReruns=0,browserOpened=False,actingAccepted=False,fullRestorationAccepted=False)
output = OUT/'receipt.json'
require(not output.exists(),'Use a fresh receipt path')
output.write_bytes(encoded(result))
print(json.dumps(dict(status=result['status'],receipt=str(output),receiptSha256=sha(output.read_bytes()),
    standardSuccesses=result['standardSuccesses'],pureSuccesses=result['pureSuccesses'],
    observedErrors=len(errors),nodeRuns=1,exactNativeChanges=native_changes,explicitFields=dict(field_counts))))
