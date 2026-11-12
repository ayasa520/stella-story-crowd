"""Own formal character-route playback and browser cleanup in one process."""
import base64
import json
import os
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
R=HERE.parent
ROOT=R.parents[3]
CLI=R/'target-arm-tools-20261112-v1/node_modules/@playwright/cli/playwright-cli.js'
CONFIG=R/'visual-high/static-seven-case-plan-arm-20261112-v2/browser-arm.json'
SESSION='stella-p30-four-model-formal-v1'
environment=dict(os.environ,PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1',PLAYWRIGHT_BROWSERS_PATH=str(R/'playwright-runtime-cache'))


def call(label,args,timeout=30):
    result=subprocess.run(['/usr/bin/node',str(CLI),'-s='+SESSION,*args],cwd=ROOT,
                          env=environment,capture_output=True,timeout=timeout)
    (HERE/(label+'.stdout.txt')).write_bytes(result.stdout)
    (HERE/(label+'.stderr.txt')).write_bytes(result.stderr)
    print(json.dumps({'step':label,'exitCode':result.returncode}),flush=True)
    result.check_returncode()
    return result.stdout.decode('utf-8')


failure=None
assert '(no browsers)' in call('before',['list'])
try:
    call('open',['open','about:blank','--config='+str(CONFIG)])
    result=json.loads(call('formal',['--raw','run-code','--filename='+str(HERE/'capture-formal.js')],150))
    assert result['status']=='formal_four_model_character_routes_passed'
    if result.get('trace'):
        payload=result['trace'].pop('traceGzipBase64',None)
        if payload:(HERE/'entry-trace.json.gz').write_bytes(base64.b64decode(payload,validate=True))
        (HERE/'trace-meta.json').write_text(json.dumps(result['trace'],indent=2)+'\n')
    (HERE/'formal-playback.json').write_text(json.dumps(result,indent=2)+'\n')
except Exception as error:
    failure=str(error)
finally:
    # Diagnostic outcome never substitutes for formal playback. This finally
    # owns browser shutdown before any coordinator analysis or image review.
    try:call('close',['close'])
    except Exception as error:failure=failure or str(error)
    try:closed='(no browsers)' in call('after',['list'])
    except Exception as error:closed=False;failure=failure or str(error)
    value={'failure':failure,'cliZero':closed,'previewOverrides':False,'formalDataAlreadySaved':True}
    (HERE/'runner-result.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value),flush=True)
if failure or not closed:raise SystemExit(1)
