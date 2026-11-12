"""Own one bounded normal alignment capture and one private FX observation.

The inherited RLIMIT_NICE used to permit Chrome to raise its priority. Lower
both limits in this process before creating any CLI/browser child, so their
nice19 baseline cannot be raised by an ordinary child priority request. This
does not alter system limits, the installed browser or the tablet launchers.
"""
import json
import os
from pathlib import Path
import resource
import subprocess

HERE = Path(__file__).resolve().parent
R = HERE.parent
ROOT = R.parents[3]
CLI = R / 'target-arm-tools-20261112-v1/node_modules/@playwright/cli/playwright-cli.js'
CONFIG = R / 'visual-high/static-seven-case-plan-arm-20261112-v2/browser-arm.json'
SESSION = 'stella-p30-alignment-fx-v1'
ENV = dict(os.environ, PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1',
           PLAYWRIGHT_BROWSERS_PATH=str(R / 'playwright-runtime-cache'))
FAILURES = []
STEPS = []
assert os.getpriority(os.PRIO_PROCESS, 0) == 19
assert sorted(os.sched_getaffinity(0)) == [0, 1]
old_limit = resource.getrlimit(resource.RLIMIT_NICE)
resource.setrlimit(resource.RLIMIT_NICE, (1, 1))
(HERE / 'inherited-priority-bound.json').write_text(json.dumps(dict(
    originalNiceLimit=old_limit, effectiveNiceLimit=resource.getrlimit(resource.RLIMIT_NICE),
    nice=os.getpriority(os.PRIO_PROCESS,0), cpuAffinity=[0,1],
    appliesTo='owned runner and future descendants only', systemConfigurationChanged=False
), indent=2) + '\n')


def call(label, arguments):
    print(json.dumps(dict(step=label, phase='start')), flush=True)
    result = subprocess.run(['/usr/bin/node', str(CLI), '-s=' + SESSION, *arguments],
                            cwd=ROOT, env=ENV, capture_output=True,
                            timeout=1200 if 'run-code' in arguments else 120)
    (HERE / (label + '.stdout.txt')).write_bytes(result.stdout)
    (HERE / (label + '.stderr.txt')).write_bytes(result.stderr)
    STEPS.append(dict(step=label, returncode=result.returncode))
    result.check_returncode()
    print(json.dumps(dict(step=label, phase='finished')), flush=True)
    return result.stdout.decode('utf-8')


def verify_browser_scheduling(label):
    observations = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            if entry.stat().st_uid != os.getuid() or os.readlink(entry / 'exe') not in (
                    '/opt/google/chrome/chrome', '/opt/google/chrome/chrome_crashpad_handler'):
                continue
            pid = int(entry.name)
            threads = []
            for thread in (entry / 'task').iterdir():
                tid = int(thread.name)
                try:
                    threads.append(dict(tid=tid, nice=os.getpriority(os.PRIO_PROCESS, tid),
                                        affinity=sorted(os.sched_getaffinity(tid))))
                except ProcessLookupError:
                    pass
            observations.append(dict(pid=pid, threads=threads))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    (HERE / (label + '-scheduling.json')).write_text(json.dumps(observations, indent=2) + '\n')
    assert observations, 'Owned Chrome process evidence missing'
    assert all(thread['nice'] == 19 and thread['affinity'] == [0,1]
               for process in observations for thread in process['threads']), 'Owned Chrome scheduling differs'


def capture(label, source, expected):
    result = json.loads(call(label, ['--raw', 'run-code', '--filename=' + str(HERE / source)]))
    (HERE / (label + '-result.json')).write_text(json.dumps(result, indent=2) + '\n')
    if result.get('status') != expected:
        FAILURES.append(dict(case=label, status=result.get('status'), failure=result.get('failure')))
    return result


assert '(no browsers)' in call('before', ['list'])
closed = False
try:
    call('open', ['open', 'about:blank', '--config=' + str(CONFIG)])
    verify_browser_scheduling('after-open')
    alignment = capture('alignment', 'capture-alignment.js',
                        'normal_end_marker_alignment_and_default_narration_captured')
    if alignment.get('status') != 'normal_end_marker_alignment_and_default_narration_captured':
        raise RuntimeError('Normal alignment case failed; close rather than replay')
    verify_browser_scheduling('after-alignment')
    capture('private-fx', 'capture-private-fx.js', 'private_fx_observation_completed')
    verify_browser_scheduling('after-private-fx')
finally:
    try:
        call('close', ['close'])
        closed = '(no browsers)' in call('after', ['list'])
        assert closed
    finally:
        (HERE / 'runner-result.json').write_text(json.dumps(dict(
            failures=FAILURES, steps=STEPS, browserClosed=closed,
            videoStarted=False, traceStarted=False, niceBoundInherited=True
        ), indent=2) + '\n')
print(json.dumps(dict(failures=FAILURES, soleBrowserClosed=closed)), flush=True)
if FAILURES:
    raise SystemExit(1)
