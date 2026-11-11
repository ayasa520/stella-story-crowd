"""Prepare two scoped BGM hypotheses from current P25 and served source bytes.

All outputs are new immutable evidence artifacts. The catalog guard compares
only the selected music record: a separate scene's manifest or identity update
must not become a dependency of this experiment. The actual payload, metadata,
P25 scene/review, Studio and relevant current served source files are locked.
This program never registers a scope, restarts an adapter, or opens a browser.
"""

import datetime
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.request import urlopen

OUT = Path(__file__).resolve().parent
ROOT = next(parent for parent in OUT.parents if (parent / 'story_crowd_data/native/scenes/10170002.json').exists())
R = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111'
SITE = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'
OLD = OUT.parent / 'executable-memory-v1'
BASE = 'http://127.0.0.1:5189'
RESOURCE = 'bgm_adv_every06_cd3_10'
SOURCE_COMMIT = '37232806a8180375a4b7a178e27157bb16d12201'
DATA_BASELINE = '7ed87fe831264af2bb9161ce3541e257bd61f489'
EXAMPLES = ['p25-every06-fade0-v37', 'p25-every06-fade1-v37']
URLS = ['/player/player.js', '/player/player_scene.js', '/player/transitions.js', '/player/player.html',
        '/studio/music_player.js', '/studio/music_voice.js', '/studio/transitions.js',
        '/studio/visual_frame_clock.js', '/studio/native_time_config.js']


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def receipt(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': digest(raw)}


def write(name, value):
    path = OUT / name
    with path.open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    return receipt(path)


def get(url):
    with urlopen(BASE + url, timeout=30) as response:
        return response.read()


def replace_once(text, old, new):
    assert text.count(old) == 1, old[:100]
    return text.replace(old, new, 1)


def main():
    source_head = subprocess.check_output(['git', '-C', str(SITE), 'rev-parse', 'HEAD'], text=True).strip()
    data_head = subprocess.check_output(['git', '-C', str(ROOT / 'story_crowd_data'), 'rev-parse', 'HEAD'], text=True).strip()
    assert source_head == SOURCE_COMMIT and data_head == DATA_BASELINE
    assert not subprocess.check_output(['git', '-C', str(SITE), 'status', '--porcelain'], text=True)
    health = json.loads(get('/health'))
    assert Path(health['siteRoot']) == SITE
    scene_path, review_path = ROOT / 'story_crowd_data/native/scenes/10170002.json', ROOT / 'story_crowd_data/review/scenes/10170002.json'
    native, review = json.loads(scene_path.read_text()), json.loads(review_path.read_text())
    catalog_path = ROOT / 'story_crowd_data/assets/catalog.json'
    entry = json.loads(catalog_path.read_text())['music'][RESOURCE]
    audio_path, metadata_path = [ROOT / 'story_crowd_data/assets' / entry[key] for key in ['url', 'metadata_url']]
    metadata = json.loads(metadata_path.read_text())
    assert metadata == entry['metadata'] and metadata['resource'] == RESOURCE
    assert metadata['samples'] == 8007280 and metadata['sample_rate'] == 44100 and metadata['loop'] is True
    assert metadata['startup_events'] == []
    served_metadata, served_audio = get('/api/music/' + RESOURCE), get('/music/' + RESOURCE)
    assert served_metadata == metadata_path.read_bytes() and served_audio == audio_path.read_bytes()
    source_locks = []
    for i, url in enumerate(URLS):
        local = SITE / 'public' / url.lstrip('/'); raw = get(url)
        assert raw == local.read_bytes(), url
        archive = OUT / f'served-preparation-{i:02d}-{local.name}'
        with archive.open('xb') as stream:
            stream.write(raw)
        source_locks.append({'url': url, 'local': str(local.relative_to(ROOT)), 'sha256': digest(raw), 'bytes': len(raw), 'archive': archive.name})
    served = write('served-source-preparation.json', {'status': 'preparation_http_receipt_not_actual_run_before',
        'health': health, 'canonicalCommit': SOURCE_COMMIT, 'sources': source_locks,
        'audio': {'url': '/music/' + RESOURCE, **receipt(audio_path), 'httpSha256': digest(served_audio)},
        'metadata': {'url': '/api/music/' + RESOURCE, **receipt(metadata_path), 'httpSha256': digest(served_metadata)}})
    catalog_lock = write('catalog-entry-lock.json', {'catalog': 'story_crowd_data/assets/catalog.json',
        'jsonPointer': '/music/' + RESOURCE, 'expected': entry,
        'scope': 'Only this record is rechecked before/after. Whole catalog/manifest SHA is informational, never a dependency on unrelated P27 updates.'})
    rows, full_guards = {}, []
    for n in [7, 8, 9]:
        row = next(row for row in native['scenario_list'] if row['scenario_id'] == n); rows[n] = row
        original = review['scenarios'][str(n)]
        assert row['bg_music'] == '' and row['command'] == ['', '', ''] and row['character'] == '' and row['motion'] == '' and row['voice'] == ''
        edges = [edge for branch in row['branch_list'] for edge in branch['transition_list']]
        assert len(edges) == 1 and edges[0]['next_scenario_id'] == n + 1
        full_guards.append({'scenarioId': n, 'stableKey': original['stableKey'], 'sourceText': original['sourceText'],
            'sourceSpeaker': original['sourceSpeaker'], 'expected': {field: row[field] for field in ['bg_music', 'command', 'character', 'motion', 'voice']},
            'branchList': row['branch_list']})
    studio_path = ROOT / 'data/story_studio/project.json'
    assert receipt(studio_path)['sha256'] == 'ebd974d90f89088fa3a504c1f419ae01c352a24e6bd80209c5ec651295d38522'
    current = write('current-target-guards.json', {'version': 2, 'status': 'fresh_current_target_only_guards_not_a_copied_old_before',
        'collectedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'dataHeadAtPreparation': data_head,
        'dataHeadIsInformationalAfterPreparation': True, 'canonicalCommit': SOURCE_COMMIT,
        'scene': receipt(scene_path), 'review': receipt(review_path), 'nodes': full_guards,
        'catalogEntryLock': catalog_lock, 'wholeCatalogAtPreparationInformationalOnly': receipt(catalog_path),
        'actualAudio': receipt(audio_path), 'actualMetadata': receipt(metadata_path), 'protectedStudio': receipt(studio_path),
        'servedPreparation': served, 'manifestNotGuarded': True})
    guards = [receipt(path) for path in [scene_path, review_path, audio_path, metadata_path, studio_path]]
    guards += [receipt(SITE / 'public' / url.lstrip('/')) for url in URLS]
    guards += [catalog_lock, current]
    variants = []
    for fade, example in enumerate(EXAMPLES):
        variants.append({'id': example, 'hypothesisOnly': True, 'installAllowed': False,
            'originalCsvRecovered': False, 'originalCommandPhaseRecovered': False, 'originalRestartRecovered': False,
            'changes': [{'scenarioId': 8, 'expected': {key: rows[8][key] for key in ['bg_music', 'command', 'character', 'motion', 'voice']},
                         'fields': {'bg_music': f'{RESOURCE},{fade},false'}}]})
    packet = write('preview-packet.json', {'version': 2, 'status': 'unactivated_memory_only_0_or_1_second_hypotheses',
        'reviewer': '/root/p15_p16_voice_evidence', 'sceneId': 10170002, 'allowedStarts': [7], 'reviewRoute': [7, 8, 9],
        'persisted': False, 'formalDataWrites': 0, 'fullGuards': full_guards,
        'sourceNative': receipt(scene_path), 'sourceReview': receipt(review_path), 'examples': variants,
        'guardReceipts': guards, 'sourceProposal': receipt(OUT.parent / 'memory-only-controls.json'),
        'sourceCommit': SOURCE_COMMIT, 'dataHeadAtPreparationInformationalOnly': data_head,
        'catalogRecordGuard': {'lock': catalog_lock, 'mustCompareCurrentRecordBeforeAndAfter': True},
        'servedSourceLocks': source_locks, 'originalCsvRecovered': False, 'originalCommandPhaseRecovered': False,
        'originalRestartRecovered': False, 'browserOpened': False})
    registry = write('registry-entry-PROPOSAL.json', {'sceneId': 10170002, 'allowedStarts': [7], 'allowedTargets': [8],
        'allowedFields': ['bg_music'], 'packet': str((OUT / 'preview-packet.json').relative_to(R)),
        'sha256': packet['sha256'], 'exampleIds': EXAMPLES})

    old_probe = (OLD / 'capture-memory-loading.js').read_text(); probe = old_probe
    probe = replace_once(probe, "examples=['p25-every06-fade0','p25-every06-fade1']", 'examples=' + json.dumps(EXAMPLES, separators=(',', ':')))
    probe = replace_once(probe, "const results=[],logs=[],network=[],errors=[],responseTasks=[];", "const packetSha='" + packet['sha256'] + "',out=" + json.dumps(str(OUT) + '/') + ";\n  const results=[],logs=[],network=[],errors=[],responseTasks=[];")
    probe = replace_once(probe, "samples:a.samples,prepared:a.prepared,notes:a.notes", "samples:a.samples,prepared:a.prepared,timing:a.timing,notes:a.notes")
    probe = replace_once(probe, 'const a=globalThis.__p25LoadingAudit={player:m,samples:[],prepared:[],notes:[],promises:new Set(),ids:new WeakMap(),nextId:1};',
        'const a=globalThis.__p25LoadingAudit={player:m,samples:[],prepared:[],timing:[],notes:[],promises:new Set(),ids:new WeakMap(),nextId:1};')
    probe = replace_once(probe, 'a.remove=m.clock.subscribe(()=>{', '''const onTiming=event=>a.timing.push({...snap(),detail:{...event.detail}});
        document.addEventListener('stella-player-timing',onTiming);
        const unsubscribe=m.clock.subscribe(()=>{''')
    probe = replace_once(probe, "return {instances:this.length,clock:m.clock.snapshot(),note:", "a.remove=()=>{unsubscribe();document.removeEventListener('stella-player-timing',onTiming);};\n        return {instances:this.length,timeOrigin:performance.timeOrigin,clock:m.clock.snapshot(),note:")
    probe = replace_once(probe, 'return {context,installed:installed.result.value};', "return {context,contexts:contexts.map(row=>({id:row.id,name:row.name,origin:row.origin,auxData:row.auxData})),playerFrame:playerFrame.frame,installed:installed.result.value};")
    probe = replace_once(probe, "const fade=name.endsWith('fade0')?0:1;", "const fade=name.includes('fade0')?0:1;\n      if(program.review_only_overrides?.packetSha256!==packetSha||program.review_only_overrides?.exampleId!==name||program.review_only_overrides?.persisted!==false)throw Error('Exact v2 private fixture identity mismatch');")
    probe = replace_once(probe, "await page.goto(url);frame=page.frames().find(row=>row.url().includes('/player/player.html'));", "await page.goto(url);\n      await page.waitForFunction(()=>{const body=document.querySelector('iframe')?.contentDocument?.body;return body?.dataset.node==='10170002:7'&&body.dataset.phase==='ready';},null,{timeout:20000});\n      frame=page.frames().find(row=>row.url().includes('/player/player.html'));\n      if(!frame)throw Error('Actual production iframe missing after atomic predecessor readiness');")
    probe = replace_once(probe, 'const program=await check.json();const node=', 'const program=await check.json();const compiledNodes=program.nodes.filter(row=>/^10170002:(7|8|9)$/.test(row.id));const node=')
    probe = replace_once(probe, "resource:m.current.resource,audioTime:m.current.voice.currentTime};", "resource:m.current.resource,voiceId:globalThis.__p25LoadingAudit.ids.get(m.current.voice),beganAudioTime:m.current.voice.began,contextTime:m.context.currentTime,audioTime:m.current.voice.currentTime,clock:m.clock.snapshot()};")
    probe = replace_once(probe, "resource:m.current?.resource,audioTime:m.current?.voice.currentTime};", "resource:m.current?.resource,voiceId:globalThis.__p25LoadingAudit.ids.get(m.current?.voice),beganAudioTime:m.current?.voice.began,contextTime:m.context?.currentTime,audioTime:m.current?.voice.currentTime,clock:m.clock.snapshot()};")
    probe = replace_once(probe, 'const observed=await stopObserver();results.push({example:name,fadeHypothesis:fade,url,observer,at8,at9,...observed});',
        "if(at8.voiceId!==at9.voiceId||at8.beganAudioTime!==at9.beganAudioTime||!(at9.contextTime>at8.contextTime))throw Error('Node9 did not retain the same naturally advancing MusicVoice');\n      const observed=await stopObserver();results.push({example:name,fadeHypothesis:fade,url,compiledNodes,overrides:program.review_only_overrides,observer,at8,at9,...observed});")
    probe = replace_once(probe, "if(cdp)await cdp.detach();await Promise.allSettled(responseTasks);", "if(cdp)await cdp.detach();await Promise.allSettled(responseTasks);\n    await page.goto('about:blank');")
    probe = replace_once(probe, "return {failure,results,logs,network,pageErrors:errors,productionPath:", "const payload={failure,results,logs,network,pageErrors:errors,productionPath:")
    probe = replace_once(probe, "note:'Root must close the sole browser immediately after capture and independently verify source/formal hashes and OS/CLI zero.'};", "note:'Root must close the sole browser immediately after capture and independently verify source/formal hashes and OS/CLI zero.'};\n  const download=page.waitForEvent('download',{timeout:60000});\n  await page.evaluate(async payload=>{const blob=await new Response(new Blob([JSON.stringify(payload)],{type:'application/json'}).stream().pipeThrough(new CompressionStream('gzip'))).blob();const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='actual-bgm-memory-v2.json.gz';a.click();},payload);\n  await (await download).saveAs(out+'actual-bgm-memory-v2.json.gz');\n  return {failure,variants:results.map(row=>({example:row.example,partial:row.partial||false,samples:row.samples?.length,timingEvents:row.timing?.length,at8:row.at8,at9:row.at9})),pageErrors:errors,rawPayload:'actual-bgm-memory-v2.json.gz',pageBlank:true,needsImmediateBrowserClose:true};")
    probe_path = OUT / 'capture-memory-loading.js'
    with probe_path.open('x') as stream:
        stream.write(probe)
    with (OUT / 'probe-changes.diff').open('x') as stream:
        stream.write(''.join(difflib.unified_diff(old_probe.splitlines(True), probe.splitlines(True), fromfile='immutable-executable-memory-v1/capture-memory-loading.js', tofile='executable-memory-v2/capture-memory-loading.js')))
    anchors = []
    for url, a, b, purpose in [('/studio/music_player.js', 23, 43, 'Actual fetch/decode prepare Promise; then callback is only an observation bound.'),
        ('/studio/music_player.js', 68, 89, 'Command then awaited preparation then real MusicVoice zero and PLAY.'),
        ('/studio/music_player.js', 91, 118, 'Gain uses shared game-frame time; fade0 completes synchronously, fade1 subscribes.'),
        ('/studio/music_voice.js', 21, 28, 'Zero-offset source start and independent Web Audio sample clock.'),
        ('/player/player.js', 374, 381, 'Current player awaits music.apply before phase0.'),
        ('/player/player.js', 428, 434, 'Text begin follows actual scene text initialization.'),
        ('/player/player.js', 474, 482, 'AccessibleText is semantic full text; phase2 follows natural textwriter completion.')]:
        path = SITE / 'public' / url.lstrip('/'); lines = path.read_text().splitlines()
        anchors.append({'url': url, **receipt(path), 'firstLine': a, 'lastLine': b, 'purpose': purpose, 'text': '\n'.join(lines[a-1:b])})
    code = write('current-code-entry-order.json', {'status': 'static_current_source_locations_not_original_total_order', 'canonicalCommit': SOURCE_COMMIT, 'anchors': anchors,
        'nativeReference': receipt(R / 'native-bgm-entry-20261112/REPORT.md'),
        'limit': 'Native SetupBGM/loader callbacks do not establish a universal completion order with CardIn/text. These actual experiments measure the current awaited path only.'})
    plan = write('execution-plan.json', {'version': 2, 'status': 'prepared_not_registered_not_run', 'sceneId': 10170002,
        'canonicalCommit': SOURCE_COMMIT, 'dataHeadAtPreparationInformationalOnly': data_head,
        'adapterBaseURL': BASE, 'fixture': packet, 'registryEntryProposal': registry,
        'currentGuards': current, 'catalogEntryLock': catalog_lock, 'servedPreparation': served,
        'probe': receipt(probe_path), 'probeDerivedFrom': receipt(OLD / 'capture-memory-loading.js'), 'codeLocations': code,
        'variants': [{'exampleId': name, 'entry': 7, 'route': [7, 8, 9], 'privateTarget': 8,
            'privateFields': {'bg_music': f'{RESOURCE},{fade},false'}, 'url': BASE + '/?scene=10170002&node=7&nativePreview=' + name,
            'testHypothesisOnly': True, 'nativeCsvApproved': False} for fade, name in enumerate(EXAMPLES)],
        'commonCueZero': 'Each variant starts the same exact payload from its own real MusicVoice.began/audioContext clock zero. Never seek, force equal load latency, or add Wait.',
        'actualProcedure': ['Root reviews exactly this registry proposal and restarts only its owned read-only adapter; this preparation performs neither action.',
            'Run snapshot_preflight.py before. It checks current P25 guards, target catalog record, served sources/audio and both activated programs; any unavailable/mismatched service is a hard stop, never a reason to restart it.',
            'Only after explicit ownership authorization, one fresh Canary session under nice19/CPU22,23, canonical CLI cwd. Run the probe once for fade0 and fade1 fresh documents within that one session.',
            'Actual7 ready, language ja via existing player action, install passive default-world StoryMusicPlayer observer; trusted iframe pointer advances7→8. Allow natural text completion and >=2.3audio seconds plus completed gain ramp.',
            'One real pointer advances8→9; require same voice identity/beganAudioTime and advancing AudioContext. No Stop/Restart or additional route.',
            'The probe removes observers and blanks the page, saves raw gzip, then browser owner immediately closes the sole session and proves CLI/OS0.',
            'Run snapshot_preflight.py after; inspect only saved JSON/clock/gain/request data. Preserve any failures/partial run and do not repeat passed variants.'],
        'observations': ['Actual resource request/response/body-finished host timestamps; passive existing-buffer Promise completion is an observed bound, not exact prior settlement.',
            'Actual console COMMAND/PLAY/FADE events; passive stella-player-timing records monotonic wall time, shared clock and audio context time at enter/text/phase boundaries.',
            'Per-shared-frame current loading, resource, MusicVoice identity/began/currentTime/gain/loop points, independent audio clock and card opacity.',
            'Actual CDP parent/player default-world frame/context metadata and exact private compiled7/8/9 nodes.',
            'No pixel first-glyph time is claimed. Semantic accessibleText already contains the full line before the textwriter finishes; phase2/ready preserve natural completion.'],
        'priorMusicLimitation': 'Original outgoing BGM/mix is not restored. These two fixtures measure only new-cue zero/envelope/loading/text relation; they cannot sign an original outgoing-music crossfade or restart.',
        'sourceSpeedState': 'Pending separate direct review of the existing15 original full frames against original menu OFF/ON sprites. Multiplication label alone proves neither toggle state nor absolute Animator rate.',
        'originalUnknowns': ['original CSV', 'authored command phase/onset', 'literal fade parameter', 'restart/reset flag', 'original Animator rate', 'missing outgoing original mix'],
        'failurePolicy': 'On unavailable service, missing default context, nonunique actual player, suspended/nonadvancing audio or timeout: preserve raw failure/partial observations and close. Do not modify policies/runtime, force playback, seek, inject delay or rerun without root review.',
        'cpuAndBrowser': {'nice': 19, 'cpus': [22, 23], 'maxChromeSessions': 1, 'browser': '/usr/bin/google-chrome-canary',
            'cwd': str(SITE), 'browserAuthorizedByThisPlan': False},
        'formalWrites': 0, 'registryChanged': False, 'adapterChanged': False, 'browserOpened': False,
        'guardScope': 'P25 native/review7-9, selected music catalog entry/audio/metadata, relevant current source and protected Studio. No full-library manifest lock; unrelated P27 scene changes do not invalidate these target guards.'})
    rollback = write('revert BGM memory v2 preparation.json', {'status': 'new_child_directory_only_no_old_or_formal_files_changed',
        'created': [served, catalog_lock, current, packet, registry, code, plan, receipt(probe_path)],
        'actualRegistryUnchangedAtPreparation': receipt(R / 'playback/approved-memory-previews.json'),
        'protectedP25Native': receipt(scene_path), 'protectedP25Review': receipt(review_path), 'protectedStudio': receipt(studio_path),
        'revertInstruction': 'If explicitly asked to revert, exclude only this new executable-memory-v2 evidence directory. No old evidence, production/native/Studio file, registry or adapter was changed.'})
    print(json.dumps({'plan': plan, 'packet': packet, 'registryProposal': registry, 'probe': receipt(probe_path), 'rollback': rollback, 'sourceFiles': len(source_locks), 'currentDataHead': data_head}))


if __name__ == '__main__':
    main()
