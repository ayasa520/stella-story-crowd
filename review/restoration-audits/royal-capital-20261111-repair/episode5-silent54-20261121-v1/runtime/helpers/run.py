"""One released normal saved Worker/Firefox session, with bounded cleanup.

The supervisor owns new process groups and kills only those groups. Independent
pre-existing local services are never stopped. Every failure keeps its logs and
before/after guards; it cannot silently retry with another browser or program.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BINDING = json.loads((HERE/'input-binding.json').read_text())
DATA = Path(BINDING['dataRoot'])
SOURCE = Path(BINDING['sourceRoot'])

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args]).decode().strip()

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def inputs():
    return {'dataHead': git(DATA, 'rev-parse', 'HEAD'), 'dataStatus': git(DATA, 'status', '--short'),
            'dataInputs': {p: sha(DATA/p) for p in BINDING['dataInputs']},
            'protectedFirstThree': {p: sha(DATA/p) for p in BINDING['protectedFirstThree']},
            'sourceHead': git(SOURCE, 'rev-parse', 'HEAD'),
            'sourceStatus': git(SOURCE, 'status', '--short'),
            'sourceFiles': {p: sha(SOURCE/p) for p in BINDING['source']['sourceFiles']},
            'distFiles': {p: sha(SOURCE/'dist'/p) for p in BINDING['source']['distFiles']},
            'resourceAndSourceGuards': {p: sha(ROOT/p) for p in BINDING['resourceAndSourceGuards']}}

def check_inputs(actual):
    for key in ['dataHead', 'dataStatus', 'dataInputs', 'protectedFirstThree', 'resourceAndSourceGuards']:
        assert actual[key] == BINDING[key], key
    for key in ['sourceFiles', 'distFiles']:
        assert actual[key] == BINDING['source'][key], key
    assert actual['sourceHead'] == BINDING['source']['head']
    assert actual['sourceStatus'] == BINDING['source']['status']

def processes():
    return subprocess.check_output(['ps', '-eo', 'pid,ppid,pgid,comm,args'], text=True)

def members(group):
    rows=[]
    for line in processes().splitlines()[1:]:
        fields=line.strip().split(None, 4)
        if len(fields)>=4 and int(fields[2])==group:
            rows.append({'pid': int(fields[0]), 'ppid': int(fields[1]), 'pgid': int(fields[2]),
                         'comm': fields[3], 'args': fields[4] if len(fields)>4 else ''})
    return rows

def stop(process):
    if members(process.pid):
        try: os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError: pass
    try: process.wait(timeout=12)
    except subprocess.TimeoutExpired:
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        process.wait(timeout=5)
    if members(process.pid):
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        end=time.monotonic()+5
        while members(process.pid) and time.monotonic()<end: time.sleep(.1)

parser=argparse.ArgumentParser()
parser.add_argument('--release', required=True)
parser.add_argument('--release-sha256', required=True)
parser.add_argument('--attempt', default='attempt-1')
args=parser.parse_args()
assert re.fullmatch(r'attempt-[1-9][0-9]*', args.attempt)
release_path=Path(args.release).resolve()
assert sha(release_path)==args.release_sha256
release=json.loads(release_path.read_text())
assert release.get('rootConfirmed') is True
assert release['dataHead']==BINDING['dataHead']
bindings=release['runtimeBindings']
required=[HERE/'run.py', HERE/'play.mjs', HERE/'worktree-upstream.mjs',
          HERE/'input-binding.json', HERE/'capture-plan.json', HERE/'normal-prepare-receipt.json',
          HERE/'ending-observer.mjs', HERE/'capture-readiness.mjs', HERE/'win01-metadata.json',
          ROOT/'artifacts/stella-local-deployment-3394828/serve-local.mjs',
          ROOT/'artifacts/stella-local-deployment-3394828/workers-local.mjs',
          ROOT/'artifacts/stella-local-deployment-3394828/d1-local.mjs',
          ROOT/'artifacts/stella-p30-firefox-20261120/bidi.mjs',
          ROOT/'artifacts/stella-p30-firefox-20261120/render-probe.mjs']
for path in required:
    assert bindings.get(str(path.relative_to(ROOT)))==sha(path), str(path)
for relative, expected in bindings.items():
    assert sha(ROOT/relative)==expected, relative
assert os.getpriority(os.PRIO_PROCESS,0)==19
assert sorted(os.sched_getaffinity(0))==[0,1]
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
out=HERE/args.attempt
out.mkdir() # Existing attempts must remain immutable evidence, never overwritten.
write(out/'release-binding.json', {'path': str(release_path), 'sha256': sha(release_path),
                                  'runtimeBindings': bindings, 'revision': BINDING['revision']})
owned=[]
handles={'supervisorPid': os.getpid(), 'nice':19,'affinity':[0,1], 'server':None,'browser':None,'driver':None,
         'recorder':None,'xvfb':None,'state':'fresh-guards'}
status=1
try:
    before=inputs();write(out/'inputs-before.json', before);check_inputs(before)
    inventory=processes();(out/'processes-before.txt').write_text(inventory)
    # Test-browser processes are absent before this sole authorized session.
    browser_rows=[line for line in inventory.splitlines()[1:] if re.search(r'\b(?:firefox|chrome|chromium|Xvfb)(?:\s|$)', line.split(None,3)[-1])]
    assert not browser_rows, browser_rows
    with socket.socket() as test_socket:
        test_socket.bind(('127.0.0.1',5198))
    elf=subprocess.check_output(['file','/usr/lib/firefox/firefox'],text=True)
    assert 'ARM aarch64' in elf, elf
    write(out/'browser-platform.json',{'path':str(Path('/usr/bin/firefox').resolve()),'fileOutput':elf,
       'binarySha256':sha('/usr/lib/firefox/firefox'),'GALLIUM_DRIVER':'llvmpipe',
       'LIBGL_ALWAYS_SOFTWARE':'1','LP_NUM_THREADS':'1','MESA_GLTHREAD':'false'})
    env=os.environ.copy();env.pop('STELLA_HOSTING',None)
    env.update(STELLA_REVIEW_DIST=str(SOURCE/'dist'),STELLA_REVIEW_REVISION=BINDING['revision'],
               STELLA_REVIEW_OUTPUT=str(out),GALLIUM_DRIVER='llvmpipe',LIBGL_ALWAYS_SOFTWARE='1',
               LP_NUM_THREADS='1',MESA_GLTHREAD='false',OMP_NUM_THREADS='1',
               OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    server_log=(out/'server.log').open('wb')
    server=subprocess.Popen(['node','--import',str(HERE/'worktree-upstream.mjs'),
                             str(ROOT/'artifacts/stella-local-deployment-3394828/serve-local.mjs'),'5198'],
                            env=env,stdout=server_log,stderr=subprocess.STDOUT,start_new_session=True)
    owned.append(('server',server,server_log));handles['server']={'pid':server.pid,'pgid':server.pid,'origin':'http://127.0.0.1:5198'}
    write(out/'handles.json',handles);print('HANDLES '+json.dumps(handles),flush=True)
    end=time.monotonic()+20
    while True:
        if server.poll() is not None: raise RuntimeError('Normal Worker exited; inspect server.log')
        try:
            with urllib.request.urlopen('http://127.0.0.1:5198/player/player.html',timeout=2) as response:
                assert response.status==200
            break
        except OSError:
            if time.monotonic()>=end: raise
            time.sleep(.1)
    with tempfile.TemporaryDirectory(prefix='stella-silent54-') as folder:
        profile=Path(folder)
        (profile/'user.js').write_text('''user_pref("browser.shell.checkDefaultBrowser",false);
user_pref("network.proxy.type",1);
user_pref("network.proxy.http","127.0.0.1");
user_pref("network.proxy.http_port",9);
user_pref("network.proxy.ssl","127.0.0.1");
user_pref("network.proxy.ssl_port",9);
user_pref("network.proxy.no_proxies_on","127.0.0.1,localhost");
''')
        browser_log=(out/'firefox.log').open('wb')
        browser=subprocess.Popen(['/usr/bin/firefox','--headless','--no-remote','--profile',str(profile),
                                   '--remote-debugging-port','0','about:blank'],env=env,
                                  stdout=browser_log,stderr=subprocess.STDOUT,start_new_session=True)
        owned.append(('browser',browser,browser_log));handles['browser']={'pid':browser.pid,'pgid':browser.pid,'profile':str(profile)}
        write(out/'handles.json',handles);print('HANDLES '+json.dumps(handles),flush=True)
        end=time.monotonic()+25
        address=None
        while time.monotonic()<end and browser.poll() is None:
            found=re.search(r'WebDriver BiDi listening on (ws://127.0.0.1:\d+)',(out/'firefox.log').read_text())
            if found: address=found[1];break
            time.sleep(.1)
        if not address: raise RuntimeError('Firefox did not announce BiDi; inspect firefox.log')
        driver_log=(out/'driver.log').open('wb')
        driver=subprocess.Popen(['node',str(HERE/'play.mjs'),address],env=env,
                                 stdout=driver_log,stderr=subprocess.STDOUT,start_new_session=True)
        owned.append(('driver',driver,driver_log));handles['driver']={'pid':driver.pid,'pgid':driver.pid,'bidi':address}
        handles['state']='capturing';write(out/'handles.json',handles);print('HANDLES '+json.dumps(handles),flush=True)
        try: status=driver.wait(timeout=900)
        finally:
            # Close before the temporary profile is removed, including failures.
            stop(driver);stop(browser)
finally:
    failure=sys.exc_info()[1]
    if failure:
        write(out/'supervisor-failure.json',{'error':str(failure),'traceback':traceback.format_exc()})
    for name,process,log in reversed(owned):
        stop(process);log.close()
    after=inputs();write(out/'inputs-after.json',after)
    same=False
    try: check_inputs(after);same=True
    except Exception as error:
        write(out/'input-guard-failure.json',{'error':str(error)});status=1
    closure={'owned':[{'kind':name,'pid':process.pid,'pgid':process.pid,'exitCode':process.returncode,
                       'remainingGroupMembers':members(process.pid)} for name,process,_ in owned],
             'allOwnedGroupsEmpty':all(not members(p.pid) for _,p,_ in owned),
             'inputsUnchanged':same,'driverExitCode':status,'recorderStarted':False,'xvfbStarted':False,
             'sourceDataFreezeMayBeReleasedAfterSupervisorExit':True,
             'imageReviewStarted':False,'supervisorPid':os.getpid()}
    (out/'processes-after.txt').write_text(processes());write(out/'process-exit.json',closure)
    handles['state']='closed';write(out/'handles.json',handles)
    print('CLOSURE '+json.dumps(closure),flush=True)
sys.exit(status)
