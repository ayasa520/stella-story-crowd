"""Own the single explicitly approved two-variant BGM browser session.

Root already created the immutable before snapshot; do not run it again. The
wrapper checks the approved exact bytes, all prior sessions/processes and its
inherited CPU limits before one open. Any failure goes through immediate close
and process accounting, with no second trial, screenshot or runtime change.
"""

import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

OUT = Path(__file__).resolve().parent
ROOT = next(parent for parent in OUT.parents if (parent / 'story_crowd_data/native/scenes/10170002.json').exists())
SITE = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'
SESSION = 'p25-every06-memory-v37'
CONFIG = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111/playback/canary.json'
APPROVED = {
    'execution-plan-ready.json': '56105b525e9ac7fad8df683703f778bfec06b2e22103ef5f1a345d205b8c9131',
    'preview-packet.json': 'e5d577f7e44bde637b99f368ae516942728a70d0c575ef53c21c22b3b6478a5c',
    'capture-memory-loading-phase-corrected.js': 'e120f681f4cf23a3b2860044cf90fe6c1210500aa2adf75efc031a1b8c351a4f',
    'served-source-before.json': 'd84d6d9a012dfceb4db5cd9d9edabcda67c8ba2119984fa7b851b1f36a4a6daf'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def processes():
    rows = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            executable = str((proc / 'exe').readlink())
            argv = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace').strip()
            chrome = '/chrome-canary/' in executable
            server = 'node' in Path(executable).name and 'run-server' in argv and 'playwright' in argv
            if chrome or server:
                pid = int(proc.name)
                rows.append({'pid': pid, 'executable': executable, 'argv': argv,
                             'kind': 'chrome' if chrome else 'cli-server',
                             'nice': os.getpriority(os.PRIO_PROCESS, pid), 'affinity': sorted(os.sched_getaffinity(pid))})
        except (OSError, ProcessLookupError):
            continue
    return rows


def call(arguments, label, timeout, raw=False):
    began = time.monotonic()
    argv = ['playwright-cli', '-s=' + SESSION] + (['--raw'] if raw else []) + arguments
    result = subprocess.run(argv, cwd=SITE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
    path = OUT / (label + '.txt')
    with path.open('x') as stream:
        stream.write(result.stdout)
    record = {'argv': argv, 'exitCode': result.returncode, 'elapsedSeconds': time.monotonic() - began,
              'output': path.name, 'sha256': digest(path)}
    print(json.dumps(record), flush=True)
    return record, result.stdout


def main():
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19 and os.sched_getaffinity(0) == {22, 23}
    assert not (OUT / 'browser-lifecycle.json').exists()
    assert not (OUT / 'actual-bgm-memory-v2.json.gz').exists()
    for name, expected in APPROVED.items():
        assert digest(OUT / name) == expected, name
    assert subprocess.check_output(['git', '-C', str(ROOT / 'story_crowd_data'), 'rev-parse', 'HEAD'], text=True).strip() == 'f7ffccb9a3f7fbf156d3e5da1e5bcadd5025b78d'
    lifecycle = {'session': SESSION, 'startedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'before': processes(), 'commands': [], 'approvedInputs': APPROVED, 'failure': None}
    assert not lifecycle['before'], lifecycle['before']
    listed, text = call(['list'], 'browser-list-before', 30)
    lifecycle['commands'].append(listed)
    assert listed['exitCode'] == 0 and '(no browsers)' in text, text
    try:
        opened, _ = call(['open', 'about:blank', '--config=' + str(CONFIG)], 'browser-open', 60)
        lifecycle['commands'].append(opened)
        assert opened['exitCode'] == 0
        lifecycle['liveProcesses'] = processes()
        assert any(row['kind'] == 'chrome' for row in lifecycle['liveProcesses'])
        assert all(row['nice'] == 19 and set(row['affinity']) <= {22, 23} for row in lifecycle['liveProcesses']), lifecycle['liveProcesses']
        captured, _ = call(['run-code', '--filename=' + str(OUT / 'capture-memory-loading-phase-corrected.js')], 'browser-capture', 180, raw=True)
        lifecycle['commands'].append(captured)
    except Exception as error:
        lifecycle['failure'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        # Close before reading/analysing the raw payload. This single finally
        # owns cleanup even if the probe preserves a partial or failed result.
        try:
            closed, _ = call(['close'], 'browser-close', 60)
            lifecycle['commands'].append(closed)
        except Exception as error:
            lifecycle['closeFailure'] = {'type': type(error).__name__, 'message': str(error)}
        lifecycle['afterClose'] = processes()
        listed, text = call(['list'], 'browser-list-after', 30)
        lifecycle['commands'].append(listed)
        lifecycle['cliHasNoBrowsers'] = listed['exitCode'] == 0 and '(no browsers)' in text
        lifecycle['chromeAndCliOsZero'] = not lifecycle['afterClose']
        lifecycle['finishedUtc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        target = OUT / 'browser-lifecycle.json'
        with target.open('x') as stream:
            stream.write(json.dumps(lifecycle, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'lifecycle': str(target), 'sha256': digest(target), 'failure': lifecycle['failure'],
                          'chromeAndCliOsZero': lifecycle['chromeAndCliOsZero'], 'cliHasNoBrowsers': lifecycle['cliHasNoBrowsers']}), flush=True)


if __name__ == '__main__':
    main()
