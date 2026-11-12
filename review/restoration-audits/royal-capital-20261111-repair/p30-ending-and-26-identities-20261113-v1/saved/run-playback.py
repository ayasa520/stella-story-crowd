"""Own one browser, preserving same-document ending and independent cleanup.

The normal saved-data case is recorded only after its identity images. Private
probes run later with their own response projections and receipts. A failed
required playback closes the browser rather than retrying the authored route.
All CLI stdout/stderr and returned evidence survive assertions and cleanup.
"""
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
R = HERE.parent
ROOT = R.parents[3]
CLI = R / 'target-arm-tools-20261112-v1/node_modules/@playwright/cli/playwright-cli.js'
CONFIG = R / 'visual-high/static-seven-case-plan-arm-20261112-v2/browser-arm.json'
SESSION = 'stella-p30-ending-normal-v1'
ENV = dict(os.environ, PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1',
           PLAYWRIGHT_BROWSERS_PATH=str(R / 'playwright-runtime-cache'))
FAILURES = []
STEPS = []


def call(label, arguments):
    print(json.dumps(dict(step=label, phase='start')), flush=True)
    completed = subprocess.run(['/usr/bin/node', str(CLI), '-s=' + SESSION, *arguments],
                               cwd=ROOT, env=ENV, capture_output=True,
                               timeout=1200 if 'run-code' in arguments else 120)
    (HERE / (label + '.stdout.txt')).write_bytes(completed.stdout)
    (HERE / (label + '.stderr.txt')).write_bytes(completed.stderr)
    STEPS.append(dict(step=label, returncode=completed.returncode))
    completed.check_returncode()
    print(json.dumps(dict(step=label, phase='finished')), flush=True)
    return completed.stdout.decode('utf-8')


def capture(label, source, expected, required=True):
    result = json.loads(call(label, ['--raw', 'run-code', '--filename=' + str(HERE / source)]))
    (HERE / (label + '-result.json')).write_text(json.dumps(result, indent=2) + '\n')
    if result['status'] != expected or result.get('cleanupPassed') is False:
        FAILURES.append(dict(case=label, status=result['status'], failure=result.get('failure')))
        if required:
            raise RuntimeError(label + ': ' + result.get('failure', result['status']))
    return result


assert '(no browsers)' in call('before', ['list'])
recording = False
closed = False
try:
    call('open', ['open', 'about:blank', '--config=' + str(CONFIG)])
    capture('characters', 'capture-characters.js', 'saved26_characters_completed_at34_ja')
    call('video-start', ['video-start', str(HERE / 'saved-ending-34-to-finish.webm'),
                         '--size=1280x1000', '--fps=30'])
    recording = True
    (HERE / 'recording-start.json').write_text(json.dumps(dict(
        afterVideoStartWall=int(time.time() * 1000), unifiedFrameClockOriginProven=False)) + '\n')
    capture('ending', 'capture-ending.js', 'saved_ending_completed_audio_voice_continues')
    call('video-stop', ['video-stop'])
    recording = False
    capture('normal-stop', 'stop-normal.js', 'normal_transport_stopped_after_recording')
    # Independent source review found that the proposed FX driver rereads a
    # global slot after verification instead of retaining that exact object
    # atomically. Its unused generated source stays as evidence; this session
    # never invokes it. A future reviewed revision requires its own release.
    (HERE / 'private-fx-not-run.json').write_text(json.dumps(dict(
        executed=False, reason='Independent review requires atomic verified observer ownership',
        proposal='p30-fx-observer-driver-proposal-20261113-v1'), indent=2) + '\n')
    capture('private-bgm', 'capture-private-bgm.js',
            'private_original_story_bgm_transport_progress_observed', required=False)
finally:
    try:
        if recording:
            call('video-stop-finally', ['video-stop'])
    finally:
        try:
            call('close', ['close'])
            closed = '(no browsers)' in call('after', ['list'])
            assert closed
        finally:
            (HERE / 'runner-result.json').write_text(json.dumps(dict(
                failures=FAILURES, steps=STEPS, browserClosed=closed,
                traceStarted=False, screenshotsDuringRecording=False), indent=2) + '\n')
print(json.dumps(dict(failures=FAILURES, soleBrowserClosed=closed)), flush=True)
if FAILURES:
    raise SystemExit(1)
