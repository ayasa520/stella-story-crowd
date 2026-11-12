"""Own one unrecorded Chrome; close before delegated costume-image review."""
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
R = HERE.parent
ROOT = R.parents[3]
CLI = R / 'target-arm-tools-20261112-v1/node_modules/@playwright/cli/playwright-cli.js'
CONFIG = R / 'visual-high/static-seven-case-plan-arm-20261112-v2/browser-arm.json'
SESSION = 'stella-p30-prefix-v2'
ENV = dict(os.environ, PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1',
           PLAYWRIGHT_BROWSERS_PATH=str(R / 'playwright-runtime-cache'))


def call(label, arguments):
    result = subprocess.run(['/usr/bin/node', str(CLI), '-s=' + SESSION, *arguments],
                            cwd=ROOT, env=ENV, capture_output=True, timeout=140)
    (HERE / (label + '.stdout.txt')).write_bytes(result.stdout)
    (HERE / (label + '.stderr.txt')).write_bytes(result.stderr)
    result.check_returncode()
    return result.stdout.decode('utf-8')


assert '(no browsers)' in call('before', ['list'])
try:
    call('open', ['open', 'about:blank', '--config=' + str(CONFIG)])
    result = json.loads(call('capture', ['--raw', 'run-code', '--filename=' + str(HERE / 'capture.js')]))
    (HERE / 'playback-result.json').write_text(json.dumps(result, indent=2) + '\n')
    assert result['status'] == 'ordinary26_27_28_corrected_prefix_completed', result.get('failure')
finally:
    call('close', ['close'])
    assert '(no browsers)' in call('after', ['list'])
print('Corrected prefix Chinese/Japanese capture complete; browser closed.')

