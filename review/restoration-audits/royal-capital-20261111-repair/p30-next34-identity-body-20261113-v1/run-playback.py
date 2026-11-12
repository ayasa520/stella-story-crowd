"""Run four bounded comparisons in one Chrome; screenshots follow video-stop."""
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
SESSION = 'stella-p30-saved34-v1'
ENV = dict(os.environ, PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1',
           PLAYWRIGHT_BROWSERS_PATH=str(R / 'playwright-runtime-cache'))
FAILURES = []


def call(label, arguments):
    result = subprocess.run(['/usr/bin/node', str(CLI), '-s=' + SESSION, *arguments],
                            cwd=ROOT, env=ENV, capture_output=True, timeout=420)
    (HERE / (label + '.stdout.txt')).write_bytes(result.stdout)
    (HERE / (label + '.stderr.txt')).write_bytes(result.stderr)
    result.check_returncode()
    return result.stdout.decode('utf-8')


def capture(label, source, expected):
    result = json.loads(call(label, ['--raw', 'run-code', '--filename=' + str(HERE / source)]))
    (HERE / (label + '-result.json')).write_text(json.dumps(result, indent=2) + '\n')
    if result['status'] != expected:
        # A bounded trial's returned failure is evidence, not authorization to
        # repeat it or discard the independent comparisons in this same live
        # browser. Protocol/driver exceptions still escape to owned cleanup.
        FAILURES.append(dict(case=label, failure=result.get('failure', result['status'])))


assert '(no browsers)' in call('before', ['list'])
recording = False
try:
    call('open', ['open', 'about:blank', '--config=' + str(CONFIG)])
    call('video-start', ['video-start', str(HERE / 'saved-felt33-body-32-33-34.webm'), '--size=1280x1000', '--fps=30'])
    recording = True
    (HERE / 'recording-start.json').write_text(json.dumps(dict(afterVideoStartWall=int(time.time()*1000))) + '\n')
    capture('body', 'capture-body.js', 'saved32_33punpun_34_completed')
    call('video-stop', ['video-stop'])
    recording = False
    capture('characters', 'capture-characters.js', 'saved33_character_fields_completed')
finally:
    try:
        if recording:
            call('video-stop-finally', ['video-stop'])
    finally:
        call('close', ['close'])
        assert '(no browsers)' in call('after', ['list'])
(HERE / 'runner-result.json').write_text(json.dumps(dict(
    failures=FAILURES, browserClosed=True, traceStarted=False), indent=2) + '\n')
print(json.dumps(dict(failures=FAILURES, soleBrowserClosed=True)))
if FAILURES:
    raise SystemExit(1)
