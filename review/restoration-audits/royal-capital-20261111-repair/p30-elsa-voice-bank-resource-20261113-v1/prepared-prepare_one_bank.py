"""Copy one existing voice bank through the normal resource exporter.

This is a review-only payload package, never an installed-catalog rewrite.
AssetWriter intentionally rejects data-directory output, so normal export owns
an isolated artifacts temporary directory. Only its completed43 WAVs and bank
index move into this new review folder; no source audio is decoded or changed.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from story_studio.crowd_assets import AssetWriter, PilotAssetPackage
from story_studio.paths import DEFAULT_STUDIO_CONFIG, load_studio_configuration

ROOT = Path('/home/rikka/Projects/stella')
HERE = Path(__file__).resolve().parent
BANK = 'vo_adv_elsa'


def write_new(name, value):
    with (HERE / name).open('x', encoding='utf-8') as output:
        json.dump(value, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write('\n')


def main():
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19
    assert sorted(os.sched_getaffinity(0)) == [0, 1]
    resource.setrlimit(resource.RLIMIT_NICE, (1, 1))
    assert not (HERE / 'assets').exists(), 'Preserve any earlier candidate payload'
    root, config = load_studio_configuration(DEFAULT_STUDIO_CONFIG)
    assert root == ROOT
    # Only voices() is invoked. Its dependency has a single authorized bank,
    # and revision is not consumed by that method. No project/scenes are loaded
    # or rebuilt; model/media/music exporters remain uncalled.
    references = SimpleNamespace(banks={BANK})
    with TemporaryDirectory(prefix='stella-elsa-one-bank-', dir=ROOT / 'artifacts') as temporary:
        writer = AssetWriter(Path(temporary), ROOT)
        package = PilotAssetPackage(ROOT, config, {'revision': 0}, writer, references, '128k')
        selected = package.catalog.voices(BANK)
        assert len(selected) == 43 and len({row['cue'] for row in selected}) == 43
        expected_members = {row['member'] for row in selected}
        assert all(member.startswith('LIMEOS/audio/' + BANK + '/') and member.endswith('.wav')
                   for member in expected_members)
        # The known large Python JSON ingress anomaly is not investigated here.
        # Use the installed ARM Node parser for this one bounded absence read;
        # the child inherits nice/affinity/RLIMIT, and touches no application.
        parser = """const fs=require('node:fs');const c=JSON.parse(fs.readFileSync(process.argv[1],'utf8'));
const members=JSON.parse(process.argv[2]),bank=process.argv[3];
const checks={bankAbsent:!Object.hasOwn(c.voices,bank),previousBankCount:Object.keys(c.voices).length,
membersAbsent:members.every(k=>!Object.hasOwn(c.members,k)),assetMembersAbsent:members.every(k=>!Object.hasOwn(c.asset_members,k))};
console.log(JSON.stringify(checks));"""
        checked = subprocess.run(['/usr/bin/node', '-e', parser,
                                  str(ROOT / 'story_crowd_data/assets/catalog.json'),
                                  json.dumps(sorted(expected_members)), BANK],
                                 capture_output=True, text=True, check=True, timeout=30)
        absence = json.loads(checked.stdout)
        assert absence['bankAbsent'] and absence['membersAbsent'] and absence['assetMembersAbsent']
        assert not (ROOT / 'story_crowd_data/assets/voices' / BANK).exists()
        bank_rows = package.voices()
        assert set(bank_rows) == {BANK}
        bank = bank_rows[BANK]
        assert len(bank['cues']) == 43
        expected_files = {bank['detail_url'], *(row['url'] for row in bank['cues'])}
        assert set(writer.files) == expected_files and len(expected_files) == 44
        assert set(writer.members) == expected_members
        assert writer.members == {row['member']: row['url'] for row in bank['cues']}
        # Normal AssetWriter already records byte identity against each source.
        # Keep its exact records instead of inventing another library inventory.
        assert all(writer.files[row['url']]['sha256'] == writer.files[row['url']]['source_sha256']
                   for row in bank['cues'])
        for name in writer.files:
            assert name.startswith('voices/' + BANK + '/')
            destination = HERE / 'assets' / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            assert not destination.exists()
            shutil.copyfile(writer.target(name), destination)
        files, members = deepcopy(writer.files), deepcopy(writer.members)
    write_new('exported-files.json', files)
    write_new('catalog-additions.json', {
        'kind': 'review-only-exact-key-additions', 'rootConfirmed': False, 'rootReviewed': False,
        'installable': False,
        'absentAtPreparation': [{'table': 'voices', 'key': BANK},
                                *({'table': table, 'key': member} for table in ['members', 'asset_members']
                                  for member in sorted(members))],
        'additions': {'voices': bank_rows, 'members': members, 'asset_members': deepcopy(members)},
        'storyFieldChanges': [], 'allCueStoryPlacementsAccepted': False,
        'audiblePlaybackAccepted': False, 'sourceTimingAccepted': False,
    })
    write_new('preparation-receipt.json', {
        'status': 'one_original_voice_bank_exported_review_only', 'bank': BANK, 'cueCount': 43,
        'exportedFileCount': len(files), 'exportedPayloadBytes': sum(row['bytes'] for row in files.values()),
        'previousInstalledBankCount': absence['previousBankCount'], 'absenceChecks': absence,
        'normalExporter': 'PilotAssetPackage.voices', 'writer': 'AssetWriter',
        'originalWavsByteIdenticalByNormalWriterRecords': True,
        'membersEqualAssetMembers': True, 'allUrlsInsideThisBank': True,
        'nice': os.getpriority(os.PRIO_PROCESS, 0), 'cpuAffinity': sorted(os.sched_getaffinity(0)),
        'rlimitNice': list(resource.getrlimit(resource.RLIMIT_NICE)),
        'audioDecodedOrReencoded': False, 'otherBanksExported': False, 'wholeLibraryRebuilt': False,
        'projectLoadedOrChanged': False, 'formalFilesChanged': [], 'gitCommandsRun': False,
        'browserOrImagesUsed': False, 'storyCuePlacementsAccepted': False, 'audibleListeningAccepted': False,
        'executionAuthorizedForInstall': False, 'rootReviewed': False, 'rootConfirmed': False,
    })
    print(json.dumps({'status': 'candidate_complete', 'bank': BANK, 'cueCount': 43,
                      'exportedFiles': len(files), 'bytes': sum(row['bytes'] for row in files.values())}))


if __name__ == '__main__':
    main()
