"""Audit the single approved two-variant capture using saved JSON only.

Observed gains are compared with the existing player's formula after the
shared-clock synchronous listener list, preserving Float32 AudioParam values.
No source signal is synthesized, no original phase/fade/Wait is selected, and
host-observed request times are kept separate from browser monotonic timings.
"""

import datetime
import gzip
import hashlib
import json
from pathlib import Path
import struct

OUT = Path(__file__).resolve().parent
ROOT = next(parent for parent in OUT.parents if (parent / 'story_crowd_data/native/scenes/10170002.json').exists())
RESOURCE = 'bgm_adv_every06_cd3_10'


def receipt(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def log_events(payload, example, name):
    prefix = name + ' '
    return [{'hostObservedEpochMs': row['hostWall'], 'value': json.loads(row['text'][len(prefix):])}
            for row in payload['logs'] if row['example'] == example and row['text'].startswith(prefix)]


def main():
    raw_path = OUT / 'actual-bgm-memory-v2.json.gz'
    with gzip.open(raw_path, 'rt') as stream:
        payload = json.load(stream)
    before_path, after_path = OUT / 'served-source-before.json', OUT / 'served-source-after.json'
    before, after = json.loads(before_path.read_text()), json.loads(after_path.read_text())
    lifecycle = json.loads((OUT / 'browser-lifecycle.json').read_text())
    assert after['stableBeforeAfter'] and lifecycle['chromeAndCliOsZero'] and lifecycle['cliHasNoBrowsers']
    assert payload['failure'] is None and not payload['pageErrors'] and len(payload['results']) == 2
    assert not any(row['type'] == 'error' for row in payload['logs'])
    runs = []
    for run in payload['results']:
        name, fade = run['example'], run['fadeHypothesis']
        assert not run.get('partial') and not run['notes']
        scoped = next(row['scoped'] for row in before['scopedPrograms'] if row['exampleId'] == name)
        volume = scoped['bgmVolume']
        plays, begins, completes, commands = [log_events(payload, name, event) for event in
            ['STORY_BGM_PLAY', 'STORY_BGM_FADE_BEGIN', 'STORY_BGM_FADE_COMPLETE', 'STORY_BGM_COMMAND']]
        assert len(plays) == len(begins) == len(completes) == len(commands) == 1
        play, begin, complete = plays[0]['value'], begins[0]['value'], completes[0]['value']
        assert begin['fade'] == complete['fade'] == fade and commands[0]['value']['restart'] is False
        stages = {row['detail']['stage']: row for row in run['timing'] if row['detail']['node'] == '10170002:8'}
        assert {'enter', 'command_resources_ready', 'text_begin', 'phase_0_begin', 'phase_2_begin', 'phase_2_end'} <= set(stages)
        phase_errors, gain_rows = [], []
        clock_errors = []
        for n, sample in enumerate(run['samples']):
            if not (sample['sameSharedFrame'] and sample['sameGameSeconds'] and sample['generationUnchanged']
                    and sample['triggerSnapshot'] == sample['observedSnapshot'] == sample['game']):
                phase_errors.append(n)
            if n:
                prior = run['samples'][n - 1]['observedSnapshot']; current = sample['observedSnapshot']
                if current['frame'] == prior['frame'] + 1:
                    expected = min(current['rawDeltaSeconds'], current['maximumDeltaSeconds']) * current['previewRate']
                    if abs(current['deltaSeconds'] - expected) > 1e-8 or abs(current['gameSeconds'] - prior['gameSeconds'] - current['deltaSeconds']) > 1e-8:
                        clock_errors.append(n)
            for voice in sample['voices']:
                assert voice['resource'] == RESOURCE and voice['id'] == 1 and not voice['ended']
                assert voice['beganAudioTime'] == play['audioTime'] and voice['loop'] is True
                assert voice['loopStart'] == play['start'] and voice['loopEnd'] == play['end']
                elapsed = sample['observedSnapshot']['gameSeconds'] - begin['gameSeconds']
                expected = volume * min(1, max(0, elapsed / fade)) if fade else volume
                gain_rows.append({'sampleIndex': n, 'sharedFrame': sample['game']['frame'],
                    'gameElapsedFromFadeBegin': elapsed, 'sampleAudioTime': voice['currentTime'],
                    'observedGain': voice['gain'], 'expectedDouble': expected, 'expectedFloat32': f32(expected),
                    'exactFloat32Match': voice['gain'] == f32(expected), 'absoluteDoubleResidual': abs(voice['gain'] - expected),
                    'pendingFade': sample['pendingFade']})
        assert not phase_errors and not clock_errors and gain_rows and all(row['exactFloat32Match'] for row in gain_rows)
        assert run['at8']['phase'] == run['at9']['phase'] == 'ready'
        assert run['at8']['voiceId'] == run['at9']['voiceId'] == 1
        assert run['at8']['beganAudioTime'] == run['at9']['beganAudioTime'] == play['audioTime']
        assert run['at9']['contextTime'] > run['at8']['contextTime'] and run['at9']['audioTime'] > run['at8']['audioTime'] >= 2.3
        prepared = [row for row in run['prepared'] if row['type'] == 'buffer-promise-fulfilled-observed']
        assert len(prepared) == 1 and prepared[0]['bufferRate'] == 48000 and prepared[0]['bufferSamples'] == 8715407
        assert prepared[0]['bufferDuration'] == 181.57097916666666
        network = [row for row in payload['network'] if row['example'] == name]
        assert len([row for row in network if row['type'] == 'request']) == 2
        assert all(row['status'] == 200 for row in network if row['type'] == 'response')
        assert all(row['error'] is None for row in network if row['type'] == 'body-finished')
        transitions = [row['value'] for row in log_events(payload, name, 'STORY_NORMAL_TRANSITION_CLOCK') if row['value'].get('node') == '10170002:8']
        assert not transitions and all(float(row['cardOpacity']) == 1 for row in run['samples'] if row['node'] == '10170002:8')
        first = next(row for row in run['samples'] if row['voices'])
        runs.append({'exampleId': name, 'fadeHypothesis': fade, 'compiledNodes': run['compiledNodes'], 'overrides': run['overrides'],
            'sampleCount': len(run['samples']), 'phaseCoherentSamples': len(run['samples']), 'phaseErrors': phase_errors,
            'sharedClockDomainErrors': clock_errors, 'gainSampleCount': len(gain_rows), 'exactFloat32Matches': sum(row['exactFloat32Match'] for row in gain_rows),
            'maximumDoubleGainResidual': max(row['absoluteDoubleResidual'] for row in gain_rows), 'gainSamples': gain_rows,
            'gainTarget': volume, 'actualCommand': commands[0], 'actualPlay': plays[0], 'fadeBegin': begins[0], 'fadeComplete': completes[0],
            'firstVoiceObservation': first, 'at8': run['at8'], 'at9': run['at9'],
            'sameVoiceAndAudioZeroAcross8To9': True, 'audioZeroFirstObservedCurrentTime': first['voices'][0]['currentTime'],
            'gainCompletedAtGameElapsed': complete['gameElapsedSeconds'], 'gainCompletedAtAudioElapsed': complete['audioTime'],
            'loadingAndText': {'timingEvents': run['timing'], 'bufferPromiseObservations': run['prepared'], 'networkHostObservations': network,
                'commandResourcesReadyToPhase0Ms': stages['phase_0_begin']['wall'] - stages['command_resources_ready']['wall'],
                'enterToTextBeginMs': stages['text_begin']['wall'] - stages['enter']['wall'],
                'playToTextBeginMs': stages['text_begin']['wall'] - play['milliseconds'],
                'textBeginToNaturalPhase2Ms': stages['phase_2_begin']['wall'] - stages['text_begin']['wall'],
                'playBeforePhase0BeforeTextObserved': play['milliseconds'] <= stages['phase_0_begin']['wall'] <= stages['text_begin']['wall'],
                'node8NewCardTransitionClockEvents': transitions,
                'limits': 'Request timestamps are host receipt observations. Passive buffer then-callback time bounds observed completion, not exact earlier settlement. Only saved synchronous player timing events establish monotonic phase/text boundaries.'},
            'frameContextBinding': run['observer'], 'notes': run['notes']})
    source = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111/native-bgm-entry-20261112/REPORT.md'
    names = ['execution-plan-ready.json', 'preview-packet.json', 'registry-entry-PROPOSAL.json',
        'capture-memory-loading-phase-corrected.js', 'run_memory_capture.py', 'audit_actual_memory.py',
        'served-source-before.json', 'served-source-after.json', 'browser-lifecycle.json',
        'browser-capture.txt', 'browser-close.txt', 'browser-list-after.txt', 'actual-bgm-memory-v2.json.gz',
        'catalog-entry-lock.json', 'current-code-entry-order.json', 'source-speed-button-visual-review.json']
    result = {'version': 1, 'status': 'two_actual_memory_hypotheses_passed_loading_order_measured_no_original_field_signoff',
        'reviewer': '/root/p15_p16_voice_evidence', 'createdUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': {'sceneId': 10170002, 'routePerVariant': [7, 8, 9], 'variants': 2, 'browserSessions': 1, 'screenshots': 0,
            'runtimeChanges': 0, 'nativeFieldWrites': 0, 'subjectiveListeningClaim': False},
        'receipts': [receipt(OUT / name) for name in names], 'nativeStaticReference': receipt(source),
        'canonicalCommit': before['canonicalCommit'], 'beforeAfterStable': after['stableBeforeAfter'],
        'chromeAndCliOsZero': lifecycle['chromeAndCliOsZero'], 'cliHasNoBrowsers': lifecycle['cliHasNoBrowsers'],
        'mainBrowserPids': [row['pid'] for row in lifecycle['liveProcesses'] if row['kind'] == 'chrome' and row['executable'].endswith('/chrome') and '--type=' not in row['argv']],
        'failure': payload['failure'], 'pageErrors': payload['pageErrors'], 'runs': runs,
        'totals': {'observations': sum(run['sampleCount'] for run in runs), 'phaseCoherent': sum(run['phaseCoherentSamples'] for run in runs),
            'gainPoints': sum(run['gainSampleCount'] for run in runs), 'exactFloat32GainMatches': sum(run['exactFloat32Matches'] for run in runs)},
        'verdict': {'actualPayloadZeroAndNaturalProgress': 'supported_for_each_memory_variant',
            'currentAwaitLoadBeforePhase0AndText': 'directly_observed_in_both_current_player_runs',
            'gainHypothesis0And1': 'both_match_current_shared_game_clock_formula_at_every_float32_gain_point',
            'originalCsv': 'unknown', 'originalPhaseAndWait': 'unknown', 'originalLiteralFadeAndRestart': 'unknown',
            'originalOutgoingMusicMix': 'not_restored', 'absoluteOriginalAnimatorRate': 'unknown'},
        'limits': ['Only these two approved natural routes were run, once each; no failed/partial result was replaced or passed case repeated.',
            'The corrected microtask phase is after one shared-clock tick synchronous listeners, not all asynchronous work in that browser frame.',
            'Game-frame fade progress and Web Audio sample elapsed are different recorded clocks. The one-game-second ramp completed at approximately0.9707audio seconds here; this is not an original timing assertion.',
            'Current await-load behavior is measured. The native asynchronous SetupBGM/loader evidence does not prove a universal completion order against CardIn/text.',
            'The original outgoing BGM/mix is absent, so these controls do not reproduce a proven original crossfade or authorize a native BGM CSV, phase, Wait, literal fade, or reset/restart flag.',
            'Visible original SPEED OFF-style was separately reviewed on15 saved full frames; it does not establish runtime boolean, Unity timeScale, or absolute original Animator rate.']}
    target = OUT / 'actual-memory-numeric-review.json'
    with target.open('x') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'receipt': receipt(target), 'totals': result['totals'], 'runs': [
        {key: row[key] for key in ['exampleId', 'sampleCount', 'gainSampleCount', 'exactFloat32Matches', 'maximumDoubleGainResidual']}
        | {'loadToPhase0Ms': row['loadingAndText']['commandResourcesReadyToPhase0Ms'], 'playToTextMs': row['loadingAndText']['playToTextBeginMs']}
        for row in runs], 'mainBrowserPids': result['mainBrowserPids'], 'chromeAndCliOsZero': True}))


if __name__ == '__main__':
    main()
