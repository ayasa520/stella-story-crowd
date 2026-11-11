"""Check the activated two-variant experiment without global manifest guards.

Only the exact P25 scene/review, selected catalog record, payload and served
source bytes bind this experiment. Full compiled programs are archived, while
before/after equality uses scoped7/8/9 nodes and BGM volume: unrelated directory
or manifest updates must not masquerade as a target change. Missing activation
or service is a hard error; this script has no server or registry write path.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.request import urlopen

OUT = Path(__file__).resolve().parent
ROOT = next(parent for parent in OUT.parents if (parent / 'story_crowd_data/native/scenes/10170002.json').exists())
R = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111'
SITE = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def get(base, url):
    with urlopen(base + url, timeout=30) as response:
        return response.read()


def main():
    phase = sys.argv[1]
    assert phase in ['before', 'after']
    plan = json.loads((OUT / 'execution-plan-phase-corrected.json').read_text()); base = plan['adapterBaseURL']
    packet_path = ROOT / plan['fixture']['path']; assert digest(packet_path.read_bytes()) == plan['fixture']['sha256']
    packet = json.loads(packet_path.read_text())
    for guard in packet['guardReceipts'] + [packet['sourceProposal'], plan['probe']]:
        assert digest((ROOT / guard['path']).read_bytes()) == guard['sha256'], guard['path']
    health = json.loads(get(base, '/health')); assert Path(health['siteRoot']) == SITE
    commit = subprocess.check_output(['git', '-C', str(SITE), 'rev-parse', 'HEAD'], text=True).strip()
    assert commit == plan['canonicalCommit']
    proposal = json.loads((OUT / 'registry-entry-PROPOSAL.json').read_text())
    registry_path = R / 'playback/approved-memory-previews.json'; registry = json.loads(registry_path.read_text())
    scopes = [row for row in registry if any(name in row['exampleIds'] for name in proposal['exampleIds'])]
    assert scopes == [proposal], 'Exact v2 proposal must first be activated by root.'
    lock = json.loads((OUT / 'catalog-entry-lock.json').read_text())
    catalog = json.loads((ROOT / lock['catalog']).read_text())
    assert catalog['music']['bgm_adv_every06_cd3_10'] == lock['expected'], 'Selected music catalog entry changed.'
    directory = OUT / ('runtime-' + phase); directory.mkdir(exist_ok=False)
    sources = []
    for i, source in enumerate(packet['servedSourceLocks']):
        raw = get(base, source['url']); assert digest(raw) == source['sha256'] and raw == (ROOT / source['local']).read_bytes()
        archive = directory / (f'source-{i:02d}-' + Path(source['local']).name)
        with archive.open('xb') as stream:
            stream.write(raw)
        sources.append({**source, 'archive': str(archive.relative_to(OUT))})
    media = []
    for endpoint, field in [('/music/', 'url'), ('/api/music/', 'metadata_url')]:
        local = ROOT / 'story_crowd_data/assets' / lock['expected'][field]
        raw = get(base, endpoint + 'bgm_adv_every06_cd3_10'); assert raw == local.read_bytes()
        archive = directory / local.name
        with archive.open('xb') as stream:
            stream.write(raw)
        media.append({'url': endpoint + 'bgm_adv_every06_cd3_10', 'sha256': digest(raw), 'bytes': len(raw), 'archive': str(archive.relative_to(OUT))})
    programs = []
    for variant in plan['variants']:
        example = variant['exampleId']; raw = get(base, '/program?scene=10170002&node=7&nativePreview=' + example)
        program = json.loads(raw); overrides = program['review_only_overrides']
        assert program['start'] == '10170002:7' and overrides['exampleId'] == example
        assert overrides['packetSha256'] == plan['fixture']['sha256'] and overrides['persisted'] is False
        nodes = [row for row in program['nodes'] if row['id'] in ['10170002:7', '10170002:8', '10170002:9']]
        assert len(nodes) == 3
        for guard in packet['fullGuards']:
            node = next(row for row in nodes if row['scenario_id'] == guard['scenarioId'])
            assert node['text'] == guard['sourceText'] and node['speaker'] == guard['sourceSpeaker']
            assert node['model'] == '' and node['body'] == '' and node['face'] == ''
            assert node['command'] == ['', '', ''] and node['bank'] == '' and node['cue'] == ''
            if node['scenario_id'] != 8:
                assert node['bg_music'] == '' and node['music']['action'] == 'inherit'
        target = next(row for row in nodes if row['scenario_id'] == 8)
        fade = 0 if 'fade0' in example else 1
        assert target['bg_music'] == variant['privateFields']['bg_music']
        assert target['music'] == {'action': 'play', 'resource': 'bgm_adv_every06_cd3_10', 'fade': fade, 'restart': False}
        scoped = {'start': program['start'], 'before': program['before'], 'nodes': nodes,
                  'bgmVolume': program['semantics']['bgm_volume'], 'overrides': overrides}
        archive = directory / (example + '-program.json')
        with archive.open('xb') as stream:
            stream.write(raw)
        programs.append({'exampleId': example, 'programArchive': str(archive.relative_to(OUT)), 'programSha256': digest(raw),
                         'scopedSha256': digest(json.dumps(scoped, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()), 'scoped': scoped})
    result = {'phase': phase, 'health': health, 'canonicalCommit': commit, 'sources': sources, 'media': media,
        'packetSha256': plan['fixture']['sha256'], 'registrySha256': digest(registry_path.read_bytes()),
        'selectedCatalogEntry': lock['expected'], 'scopedPrograms': programs,
        'nativeSceneSha256': digest((ROOT / 'story_crowd_data/native/scenes/10170002.json').read_bytes()),
        'reviewSceneSha256': digest((ROOT / 'story_crowd_data/review/scenes/10170002.json').read_bytes()),
        'protectedStudioSha256': digest((ROOT / 'data/story_studio/project.json').read_bytes()),
        'dataHeadInformationalOnly': subprocess.check_output(['git', '-C', str(ROOT / 'story_crowd_data'), 'rev-parse', 'HEAD'], text=True).strip()}
    if phase == 'after':
        before = json.loads((OUT / 'served-source-before.json').read_text())
        for key in ['packetSha256', 'registrySha256', 'nativeSceneSha256', 'reviewSceneSha256', 'protectedStudioSha256', 'selectedCatalogEntry']:
            assert result[key] == before[key], key
        assert [(row['url'], row['sha256']) for row in result['sources']] == [(row['url'], row['sha256']) for row in before['sources']]
        assert [(row['url'], row['sha256']) for row in media] == [(row['url'], row['sha256']) for row in before['media']]
        assert [(row['exampleId'], row['scopedSha256']) for row in programs] == [(row['exampleId'], row['scopedSha256']) for row in before['scopedPrograms']]
        result['stableBeforeAfter'] = True
    target = OUT / ('served-source-' + phase + '.json')
    with target.open('x') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'path': str(target.relative_to(ROOT)), 'sha256': digest(target.read_bytes()), 'sourceFiles': len(sources), 'variants': len(programs)}))


if __name__ == '__main__':
    main()
