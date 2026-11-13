"""Publish one normal-exported voice bank without rebuilding installed assets.

The candidate contains original, unmodified WAVs and the existing exporter's
index. This operation accepts resource availability only. Individual story cue
placement and actual media playback require their own evidence and publication.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import tempfile

from story_studio.crowd_assets import AssetWriter

HERE = Path(__file__).resolve().parent
R = HERE.parent
sys.path.insert(0, str(R))
from target_verified_utf8_v1 import decode_verified

ROOT = R.parents[3]
ASSETS = ROOT / 'story_crowd_data/assets'
CANDIDATE = R / 'p30-elsa-voice-bank-resource-candidate-20261113-v1'
BANK = 'vo_adv_elsa'
AUDIT = (ROOT / 'story_crowd_data/review/restoration-audits/'
         'royal-capital-20261111-repair/p30-elsa-voice-bank-resource-20261113-v1')


def read(path):
    # Reuse the established target UTF-8 ingress boundary. Earlier receipts
    # contain a real decoded-text mismatch; do not invent a different cause or
    # reread/rewrite any installed data to recover such a host-runtime failure.
    return json.loads(decode_verified(path.read_bytes(), 'elsa-bank:' + path.name))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def publish(source, destination):
    """Atomically replace one descriptor after its payloads are available."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
        temporary = Path(stream.name)
        with source.open('rb') as incoming:
            shutil.copyfileobj(incoming, stream)
    os.replace(temporary, destination)


def main():
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19
    assert sorted(os.sched_getaffinity(0)) == [0, 1]
    resource.setrlimit(resource.RLIMIT_NICE, (1, 1))
    authorization = read(HERE / 'root-acceptance.json')
    assert authorization['rootConfirmed'] is True
    assert authorization['normalExporterAndOriginalBankReviewed'] is True
    assert not (HERE / 'installed-readback.json').exists()
    before = read(ASSETS / 'catalog.json')
    package_before = read(ASSETS / 'package.json')
    addition = read(CANDIDATE / 'catalog-additions.json')['additions']
    exported = read(CANDIDATE / 'exported-files.json')
    assert set(addition) == {'voices', 'members', 'asset_members'}
    assert set(addition['voices']) == {BANK}
    assert addition['members'] == addition['asset_members']
    assert BANK not in before['voices']
    bank = addition['voices'][BANK]
    assert bank['detail_url'] == f'voices/{BANK}/index.json'
    assert bank['cues'] and len(bank['cues']) == authorization['cueCount']
    assert {row['cue'] for row in bank['cues']} == {
        Path(row['url']).stem for row in bank['cues']}
    expected_files = {bank['detail_url'], *(row['url'] for row in bank['cues'])}
    assert set(exported) == expected_files
    assert addition['members'] == {row['member']: row['url'] for row in bank['cues']}
    assert read(CANDIDATE / 'assets' / bank['detail_url']) == bank['cues']
    for table, rows in addition.items():
        assert not set(rows) & set(before[table]), table
    for name in exported:
        assert name.startswith(f'voices/{BANK}/') and '..' not in Path(name).parts
        assert not (ASSETS / name).exists(), name
    shutil.copyfile(ASSETS / 'catalog.json', HERE / 'catalog.before.json')
    shutil.copyfile(ASSETS / 'package.json', HERE / 'package.before.json')
    catalog = deepcopy(before)
    for table, rows in addition.items():
        catalog[table].update(deepcopy(rows))
    restored = deepcopy(catalog)
    for table, rows in addition.items():
        for key in rows:
            del restored[table][key]
    assert restored == before
    with tempfile.TemporaryDirectory(prefix='stella-elsa-bank-', dir=ROOT / 'artifacts') as directory:
        writer = AssetWriter(Path(directory), ROOT)
        writer.json('catalog.json', catalog)
        # Verify only the newly exported bank, retaining the exporter's source
        # provenance. Existing packages and waveforms are never enumerated or
        # rehashed. All new payloads precede their public catalog descriptor.
        for name, prepared in exported.items():
            shutil.copyfile(CANDIDATE / 'assets' / name, writer.target(name))
            writer.record(name)
            assert all(writer.files[name][key] == prepared[key] for key in ('bytes', 'sha256'))
            writer.files[name] = deepcopy(prepared)
        package = deepcopy(package_before)
        for name, record in writer.files.items():
            package['files'][name] = dict(package['files'].get(name, {}), **record)
        package['bytes'] = sum(row['bytes'] for row in package['files'].values())
        changed = {name for name in set(package['files']) | set(package_before['files'])
                   if package['files'].get(name) != package_before['files'].get(name)}
        assert changed == {'catalog.json', *exported}
        assert {key: value for key, value in package.items() if key not in {'files', 'bytes'}} == {
            key: value for key, value in package_before.items() if key not in {'files', 'bytes'}}
        writer.json('package.json', package)
        for name in [*exported, 'catalog.json', 'package.json']:
            publish(writer.target(name), ASSETS / name)
    assert read(ASSETS / 'catalog.json') == catalog
    assert read(ASSETS / 'package.json') == package
    receipt = dict(status='single_original_voice_bank_resource_installed', bank=BANK,
                   cueCount=len(bank['cues']), previousBankCount=len(before['voices']),
                   currentBankCount=len(catalog['voices']),
                   changedPackageEntries=sorted(changed),
                   publishedFiles=['assets/catalog.json', 'assets/package.json',
                                   *('assets/' + name for name in sorted(exported))],
                   allOtherCatalogValuesUnchanged=True, allOtherPackageEntriesUnchanged=True,
                   fullLibraryRebuilt=False, audioReencoded=False, storyFieldsChanged=False,
                   storyCuePlacementsAccepted=False, audiblePlaybackAccepted=False)
    write(HERE / 'installed-readback.json', receipt)
    AUDIT.mkdir(exist_ok=False)
    for name in ['catalog-additions.json', 'exported-files.json',
                 'preparation-receipt.json', 'prepare_one_bank.py']:
        shutil.copyfile(CANDIDATE / name, AUDIT / ('prepared-' + name))
    for name in ['REPORT.md', 'root-acceptance.json', 'installed-readback.json',
                 'wav-header-readback.json']:
        shutil.copyfile(HERE / name, AUDIT / name)
    shutil.copyfile(Path(__file__), AUDIT / 'integrate_resource.py')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
